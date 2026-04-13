from celery import shared_task
from django.conf import settings
import logging

logger = logging.getLogger("paper_trader.markets")


@shared_task
def fetch_market_prices():
    from .models import Asset, AssetQuote
    from .services import MARKET_CONFIGS, is_market_open
    from .quote_provider import fetch_yahoo_quote, refresh_asset_quote

    tracked_assets = Asset.objects.filter(
        id__in=set(
            list(
                Asset.objects.filter(
                    positions__isnull=False
                ).values_list("id", flat=True)
            )
            + list(
                Asset.objects.filter(
                    alerts__status="active"
                ).values_list("id", flat=True)
            )
        )
    )

    refreshed_asset_ids = []
    portfolios_to_notify = set()
    for market_code, cfg in MARKET_CONFIGS.items():
        if not is_market_open(market_code):
            continue
        market_assets = tracked_assets.filter(market=market_code)
        for asset in market_assets:
            try:
                quote = refresh_asset_quote(str(asset.id))
                if quote:
                    refreshed_asset_ids.append(str(asset.id))
                    for position in asset.positions.all():
                        portfolios_to_notify.add(str(position.portfolio_id))
            except Exception:
                logger.exception("Failed to refresh quote for asset %s", asset.display_symbol)

    if portfolios_to_notify:
        from realtime.services import publish_event
        for portfolio_id in portfolios_to_notify:
            publish_event(f"portfolio_{portfolio_id}", "price.updated", {"portfolio_id": portfolio_id})

    if refreshed_asset_ids:
        from alerts.tasks import evaluate_alerts_for_assets

        evaluate_alerts_for_assets.delay(refreshed_asset_ids)


@shared_task
def refresh_single_asset_quote(asset_id: str):
    from .quote_provider import refresh_asset_quote

    try:
        refresh_asset_quote(asset_id)
    except Exception:
        logger.exception("Failed to refresh quote for asset %s", asset_id)


@shared_task
def backfill_ohlcv_historical():
    """Backfill historical OHLCV data for all tracked assets (5+ years).

    This task fetches historical OHLCV from Yahoo Finance (primary) with automatic
    fallback to Alpha Vantage if Yahoo fails. Runs asynchronously and logs progress.
    """
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .services import ingest_ohlcv

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None

    tracked_assets = Asset.objects.filter(is_seeded=True).distinct()
    total = tracked_assets.count()
    success_count = 0
    fail_count = 0

    for idx, asset in enumerate(tracked_assets, 1):
        logger.info(f"Backfilling OHLCV [{idx}/{total}] for {asset.display_symbol}")
        try:
            ohlcv_list = fetch_ohlcv_with_fallback(
                asset.provider_symbol,
                alpha_vantage_key=alpha_vantage_key,
                period="5y"
            )
            if ohlcv_list:
                ingest_count = ingest_ohlcv(str(asset.id), ohlcv_list)
                logger.info(f"Ingested {ingest_count} OHLCV records for {asset.display_symbol}")
                success_count += 1
            else:
                logger.warning(f"No OHLCV data fetched for {asset.display_symbol}")
                fail_count += 1
        except Exception:
            logger.exception(f"Backfill failed for {asset.display_symbol}")
            fail_count += 1

    logger.info(f"Backfill complete: {success_count} success, {fail_count} failed")


@shared_task
def fetch_daily_ohlcv():
    """Fetch and store daily OHLCV for all tracked assets.

    Runs after market close daily. Updates existing OHLCV records or creates new ones.
    """
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .services import ingest_ohlcv

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None

    tracked_assets = Asset.objects.filter(is_seeded=True).distinct()

    for asset in tracked_assets:
        try:
            ohlcv_list = fetch_ohlcv_with_fallback(
                asset.provider_symbol,
                alpha_vantage_key=alpha_vantage_key,
                period="1d"
            )
            if ohlcv_list:
                ingest_ohlcv(str(asset.id), ohlcv_list)
        except Exception:
            logger.exception(f"Failed to fetch daily OHLCV for {asset.display_symbol}")