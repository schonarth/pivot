import logging
from datetime import date, timedelta
from decimal import Decimal
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .ohlcv_provider import is_valid_ohlcv_record
from .models import Asset, MarketConfig, NewsItem, OHLCV

try:
    from exchange_calendars import get_calendar
except ImportError:
    get_calendar = None


logger = logging.getLogger("paper_trader.markets")


MARKET_CONFIGS = {
    "BR": {
        "name": "Brazil",
        "currency": "BRL",
        "exchange": "BVMF",
        "fee_rate": "0.0003",
        "iana_timezone": "America/Sao_Paulo",
    },
    "US": {
        "name": "United States",
        "currency": "USD",
        "exchange": "XNYS",
        "fee_rate": "0.0000",
        "iana_timezone": "America/New_York",
    },
    "UK": {
        "name": "United Kingdom",
        "currency": "GBP",
        "exchange": "XLON",
        "fee_rate": "0.0010",
        "iana_timezone": "Europe/London",
    },
    "EU": {
        "name": "European Union",
        "currency": "EUR",
        "exchange": "XPAR",
        "fee_rate": "0.0010",
        "iana_timezone": "Europe/Paris",
    },
}


def get_market_config(market_code: str) -> MarketConfig | dict | None:
    cfg = MARKET_CONFIGS.get(market_code)
    if cfg is None:
        return None
    try:
        return MarketConfig.objects.get(code=market_code)
    except MarketConfig.DoesNotExist:
        return cfg


def is_market_open(market_code: str) -> bool:
    cfg = MARKET_CONFIGS.get(market_code)
    if cfg is None:
        return False
    if get_calendar is None:
        return None
    try:
        cal = get_calendar(cfg["exchange"])
        now = timezone.now()
        if not cal.is_session(now.date()):
            return False

        open_at = cal.session_open(now.date())
        close_at = cal.session_close(now.date())
        return open_at <= now <= close_at
    except Exception:
        return None


def get_market_timezone(market_code: str) -> str:
    cfg = MARKET_CONFIGS.get(market_code)
    if cfg is None:
        return "UTC"
    return cfg["iana_timezone"]


def seed_market_configs():
    for code, cfg in MARKET_CONFIGS.items():
        MarketConfig.objects.update_or_create(
            code=code,
            defaults={
                "name": cfg["name"],
                "currency": cfg["currency"],
                "exchange": cfg["exchange"],
                "fee_rate": cfg["fee_rate"],
                "iana_timezone": cfg["iana_timezone"],
            },
        )


def get_or_create_asset(*, display_symbol: str, market: str, **kwargs) -> Asset:
    defaults = {
        "name": kwargs.get("name", display_symbol),
        "exchange": kwargs.get("exchange", ""),
        "currency": kwargs.get("currency", ""),
        "is_seeded": kwargs.get("is_seeded", True),
    }
    defaults.update({k: v for k, v in kwargs.items() if k not in defaults})
    asset, _ = Asset.objects.update_or_create(
        market=market,
        display_symbol=display_symbol,
        defaults=defaults,
    )
    return asset


def ingest_ohlcv(asset_id: str, ohlcv_list: list[dict], source: str = "yahoo_finance") -> int:
    """Ingest OHLCV records, handling duplicates gracefully.

    Args:
        asset_id: Asset UUID
        ohlcv_list: List of OHLCV dicts with keys: date, open, high, low, close, volume
        source: Provider name (default: "yahoo_finance")

    Returns:
        Number of records ingested (created + updated).
    """
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return 0

    if not ohlcv_list:
        return 0

    count = 0
    invalid_dates: list = []
    with transaction.atomic():
        for ohlcv in ohlcv_list:
            if not is_valid_ohlcv_record(ohlcv):
                invalid_dates.append(ohlcv.get("date"))
                continue
            obj, created = OHLCV.objects.update_or_create(
                asset=asset,
                date=ohlcv["date"],
                defaults={
                    "open": ohlcv["open"],
                    "high": ohlcv["high"],
                    "low": ohlcv["low"],
                    "close": ohlcv["close"],
                    "volume": ohlcv["volume"],
                    "source": source,
                },
            )
            if created:
                count += 1

    if invalid_dates:
        logger.warning(
            "Discarded invalid OHLCV rows for %s from %s: %s",
            asset.display_symbol,
            source,
            ", ".join(str(date) for date in invalid_dates[:5]),
        )

    return count


def recent_ohlcv_needs_repair(asset_id: str, lookback_days: int = 5) -> bool:
    cutoff = timezone.now().date() - timedelta(days=lookback_days)
    recent_rows = (
        OHLCV.objects.filter(asset_id=asset_id, date__gte=cutoff)
        .order_by("-date")
        .values("date", "open", "high", "low", "close", "volume")
    )
    return any(not is_valid_ohlcv_record(row) for row in recent_rows)


def invalid_ohlcv_dates(asset_id: str, start_date: date | None = None, end_date: date | None = None) -> list[date]:
    queryset = OHLCV.objects.filter(asset_id=asset_id)
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    return [
        row["date"]
        for row in queryset.order_by("date").values("date", "open", "high", "low", "close", "volume")
        if not is_valid_ohlcv_record(row)
    ]


def delete_invalid_ohlcv_rows(
    asset_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[date]:
    invalid_dates = invalid_ohlcv_dates(asset_id, start_date=start_date, end_date=end_date)
    if invalid_dates:
        OHLCV.objects.filter(asset_id=asset_id, date__in=invalid_dates).delete()
    return invalid_dates


class NewsService:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    CACHE_TTL = 4 * 3600
    EMPTY_CACHE_TTL = 15 * 60

    @classmethod
    def fetch_and_store_news(cls, asset: Asset) -> int:
        """Fetch news for asset from all sources and store results. Returns count of new items."""
        cached = cache.get(f"news:{asset.id}")
        if cached:
            return 0

        news_items = []
        news_items.extend(cls._fetch_google_news_rss(asset))
        news_items.extend(cls._fetch_yahoo_finance(asset))
        news_items.extend(cls._fetch_marketwatch(asset))
        if asset.market == "BR":
            news_items.extend(cls._fetch_valor_economico(asset))

        if not news_items:
            news_items.extend(cls._fetch_rss_fallback(asset))

        count = cls._store_news_items(asset, news_items)
        cache.set(f"news:{asset.id}", True, cls.CACHE_TTL if news_items else cls.EMPTY_CACHE_TTL)
        return count

    @classmethod
    def _google_news_locale(cls, asset: Asset) -> tuple[str, str, str]:
        locales = {
            "BR": ("pt-BR", "BR", "BR:pt-419"),
            "US": ("en-US", "US", "US:en"),
            "UK": ("en-GB", "GB", "GB:en"),
            "EU": ("en", "FR", "FR:en"),
        }
        return locales.get(asset.market, ("en-US", "US", "US:en"))

    @classmethod
    def _google_news_queries(cls, asset: Asset) -> list[str]:
        queries = [asset.provider_symbol, asset.display_symbol]
        if asset.name and asset.name.lower() not in {
            asset.display_symbol.lower(),
            asset.provider_symbol.lower(),
        }:
            queries.append(f'"{asset.name}"')
            queries.append(f'{asset.display_symbol} OR "{asset.name}"')

        seen = set()
        result = []
        for query in queries:
            normalized = query.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(query)
        return result[:3]

    @classmethod
    def _fetch_google_news_rss(cls, asset: Asset) -> list[dict]:
        hl, gl, ceid = cls._google_news_locale(asset)
        items = []
        seen_urls = set()

        for query in cls._google_news_queries(asset):
            url = (
                "https://news.google.com/rss/search?"
                f"q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={ceid}"
            )
            try:
                feed = feedparser.parse(url)
            except Exception:
                continue

            for entry in feed.entries[:8]:
                link = entry.get("link", "")
                headline = entry.get("title", "").strip()
                if not link or not headline or link in seen_urls:
                    continue
                seen_urls.add(link)
                published_at = None
                published_value = entry.get("published") or entry.get("updated")
                if published_value:
                    try:
                        published_at = parsedate_to_datetime(published_value)
                    except (TypeError, ValueError, IndexError, OverflowError):
                        published_at = None
                items.append({
                    "headline": headline[:500],
                    "url": link,
                    "source": "google_news_rss",
                    "summary": entry.get("summary", "")[:1000] or None,
                    "published_at": published_at,
                })

        return items

    @classmethod
    def _fetch_yahoo_finance(cls, asset: Asset) -> list[dict]:
        """Scrape Yahoo Finance news for symbol."""
        try:
            url = f"https://finance.yahoo.com/quote/{asset.provider_symbol}/news"
            resp = requests.get(url, headers=cls.HEADERS, timeout=5)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            items = []
            for link in soup.find_all("a", {"data-test": "quoteNewsLink"})[:5]:
                headline = link.get_text(strip=True)
                href = link.get("href", "")
                if headline and href:
                    items.append({
                        "headline": headline[:500],
                        "url": href if href.startswith("http") else f"https://finance.yahoo.com{href}",
                        "source": "yahoo_finance",
                        "summary": None,
                        "published_at": None,
                    })
            return items
        except Exception:
            return []

    @classmethod
    def _fetch_marketwatch(cls, asset: Asset) -> list[dict]:
        """Scrape MarketWatch news for symbol."""
        try:
            url = f"https://www.marketwatch.com/investing/stock/{asset.provider_symbol.lower()}"
            resp = requests.get(url, headers=cls.HEADERS, timeout=5)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            items = []
            for article in soup.find_all("div", {"class": "article"})[:5]:
                headline_el = article.find("h3")
                link_el = article.find("a")
                if headline_el and link_el:
                    headline = headline_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    items.append({
                        "headline": headline[:500],
                        "url": href if href.startswith("http") else f"https://www.marketwatch.com{href}",
                        "source": "marketwatch",
                        "summary": None,
                        "published_at": None,
                    })
            return items
        except Exception:
            return []

    @classmethod
    def _fetch_valor_economico(cls, asset: Asset) -> list[dict]:
        """Scrape Valor Econômico news for BR assets."""
        try:
            url = f"https://www.valor.com.br/search?q={asset.display_symbol}"
            resp = requests.get(url, headers=cls.HEADERS, timeout=5)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            items = []
            for article in soup.find_all("a", {"class": "article"})[:5]:
                headline = article.get_text(strip=True)
                href = article.get("href", "")
                if headline and href:
                    items.append({
                        "headline": headline[:500],
                        "url": href if href.startswith("http") else f"https://www.valor.com.br{href}",
                        "source": "valor_economico",
                        "summary": None,
                        "published_at": None,
                    })
            return items
        except Exception:
            return []

    @classmethod
    def _fetch_rss_fallback(cls, asset: Asset) -> list[dict]:
        """Fallback to RSS feeds when scraping fails."""
        feeds = {
            "BR": "http://feeds.bloomberg.com/markets/news.rss?country=BR",
            "US": "https://feeds.finance.yahoo.com/news",
            "UK": "http://feeds.bloomberg.com/markets/news.rss?country=UK",
            "EU": "http://feeds.bloomberg.com/markets/news.rss?country=EU",
        }
        url = feeds.get(asset.market)
        if not url:
            return []

        try:
            feed = feedparser.parse(url)
            items = []
            for entry in feed.entries[:5]:
                if asset.display_symbol.lower() in entry.get("title", "").lower():
                    items.append({
                        "headline": entry.get("title", "")[:500],
                        "url": entry.get("link", ""),
                        "source": "rss_feed",
                        "summary": entry.get("summary", "")[:1000],
                        "published_at": None,
                    })
            return items
        except Exception:
            return []

    @classmethod
    def _store_news_items(cls, asset: Asset, news_items: list[dict]) -> int:
        """Store news items in database, skip duplicates."""
        created_items = []
        count = 0
        for item in news_items:
            if not item.get("url"):
                continue
            news_item, created = NewsItem.objects.update_or_create(
                asset=asset,
                url=item["url"][:500],
                defaults={
                    "headline": item["headline"],
                    "summary": item.get("summary"),
                    "source": item["source"],
                    "published_at": item.get("published_at"),
                },
            )
            if created:
                count += 1
                created_items.append(news_item)
        cls._attach_sentiment_scores(created_items)
        return count

    @classmethod
    def _attach_sentiment_scores(cls, news_items: list[NewsItem]) -> None:
        if not news_items:
            return

        from ai.services import AIService

        headlines = [item.headline for item in news_items if item.headline]
        sentiments = AIService.analyze_news_sentiment(headlines)
        if not sentiments:
            return

        for news_item in news_items:
            score = sentiments.get(news_item.headline)
            if score is None:
                continue
            score_decimal = Decimal(str(score)) if not isinstance(score, Decimal) else score
            score_decimal = max(Decimal("-1.0"), min(Decimal("1.0"), score_decimal))
            news_item.sentiment_score = score_decimal
            news_item.save(update_fields=["sentiment_score"])
