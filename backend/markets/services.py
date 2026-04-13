import uuid
from decimal import Decimal
import requests
import feedparser
from bs4 import BeautifulSoup
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from exchange_calendars import get_calendar

from .models import Asset, AssetQuote, MarketConfig, OHLCV, NewsItem


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
    cal = get_calendar(cfg["exchange"])
    return cal.is_session(timezone.now().date())


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
    with transaction.atomic():
        for ohlcv in ohlcv_list:
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

    return count


class NewsService:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    CACHE_TTL = 4 * 3600

    @classmethod
    def fetch_and_store_news(cls, asset: Asset) -> int:
        """Fetch news for asset from all sources and store results. Returns count of new items."""
        cached = cache.get(f"news:{asset.id}")
        if cached:
            return 0

        news_items = []
        news_items.extend(cls._fetch_yahoo_finance(asset))
        news_items.extend(cls._fetch_marketwatch(asset))
        if asset.market == "BR":
            news_items.extend(cls._fetch_valor_economico(asset))

        if not news_items:
            news_items.extend(cls._fetch_rss_fallback(asset))

        count = cls._store_news_items(asset, news_items)
        cache.set(f"news:{asset.id}", True, cls.CACHE_TTL)
        return count

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
                    })
            return items
        except Exception:
            return []

    @classmethod
    def _store_news_items(cls, asset: Asset, news_items: list[dict]) -> int:
        """Store news items in database, skip duplicates."""
        count = 0
        for item in news_items:
            if not item.get("url"):
                continue
            _, created = NewsItem.objects.update_or_create(
                asset=asset,
                url=item["url"],
                defaults={
                    "headline": item["headline"],
                    "summary": item.get("summary"),
                    "source": item["source"],
                },
            )
            if created:
                count += 1
        return count