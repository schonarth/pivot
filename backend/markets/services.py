import uuid

from django.db import transaction
from django.utils import timezone

from exchange_calendars import get_calendar

from .models import Asset, AssetQuote, MarketConfig, OHLCV


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