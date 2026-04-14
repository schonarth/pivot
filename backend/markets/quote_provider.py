import logging
import uuid
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone

from .models import AssetQuote

logger = logging.getLogger("paper_trader.markets")


def fetch_yahoo_quote(provider_symbol: str) -> dict | None:
    try:
        import yfinance as yf

        ticker = yf.Ticker(provider_symbol)
        info = ticker.fast_info
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            return None
        last_row = hist.iloc[-1]
        price = Decimal(str(last_row["Close"])).quantize(Decimal("0.0001"))
        as_of = timezone.now()
        return {
            "price": price,
            "source": "yahoo_finance",
            "as_of": as_of,
            "is_delayed": True,
            "provider_payload": {
                "symbol": provider_symbol,
                "open": str(last_row.get("Open", "")),
                "high": str(last_row.get("High", "")),
                "low": str(last_row.get("Low", "")),
                "volume": str(last_row.get("Volume", "")),
            },
        }
    except Exception:
        logger.exception("Failed to fetch quote for %s", provider_symbol)
        return None


def refresh_asset_quote(asset_id: str) -> AssetQuote | None:
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .services import ingest_ohlcv

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return None

    quote_data = fetch_yahoo_quote(asset.provider_symbol)
    if quote_data is None:
        return None

    cache_key = f"price:{asset.id}"
    cache.set(
        cache_key,
        {
            "price": str(quote_data["price"]),
            "as_of": quote_data["as_of"].isoformat(),
            "source": quote_data["source"],
        },
        timeout=3600,
    )

    quote = AssetQuote.objects.create(
        id=uuid.uuid4(),
        asset=asset,
        price=quote_data["price"],
        currency=asset.currency,
        source=quote_data["source"],
        as_of=quote_data["as_of"],
        is_delayed=quote_data["is_delayed"],
        provider_payload=quote_data.get("provider_payload"),
    )

    try:
        ohlcv_list = fetch_ohlcv_with_fallback(asset.provider_symbol, period="1d")
        if ohlcv_list:
            ingest_ohlcv(asset_id, ohlcv_list)
    except Exception:
        logger.exception(f"Failed to fetch daily OHLCV for {asset.provider_symbol} during quote refresh")

    return quote


def get_latest_quote(asset_id: str) -> AssetQuote | None:
    return AssetQuote.objects.filter(asset_id=asset_id).order_by("-fetched_at").first()