import logging
from celery import shared_task
from django.conf import settings
from django.db.models import Count

logger = logging.getLogger("paper_trader.markets")


@shared_task
def fetch_market_prices():
    from .models import Asset
    from .services import MARKET_CONFIGS, is_market_open
    from .quote_provider import refresh_asset_quote

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
def backfill_ohlcv_historical(source: str = "startup", initiated_by: str | None = None):
    """Backfill historical OHLCV data for all tracked assets (5+ years).

    This task fetches historical OHLCV from Yahoo Finance (primary) with automatic
    fallback to Alpha Vantage if Yahoo fails. Runs asynchronously and logs progress.
    """
    from .backfill_progress import (
        clear_backfill_lock,
        finish_backfill_status,
        mark_backfill_asset_completed,
        mark_backfill_asset_failed,
        mark_backfill_asset_started,
        update_backfill_status,
    )
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .services import ingest_ohlcv
    from realtime.services import publish_event

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None

    tracked_assets = (
        Asset.objects.filter(is_seeded=True)
        .annotate(ohlcv_count=Count("ohlcv_data"))
        .filter(ohlcv_count__lt=200)
        .distinct()
    )
    total = tracked_assets.count()
    success_count = 0
    fail_count = 0

    update_backfill_status(
        state="running",
        source=source,
        initiated_by=initiated_by,
        total_assets=total,
    )
    publish_event("ohlcv_backfill", "ohlcv.backfill.updated", update_backfill_status())

    if total == 0:
        finish_backfill_status(state="completed")
        publish_event("ohlcv_backfill", "ohlcv.backfill.completed", update_backfill_status())
        return

    try:
        for idx, asset in enumerate(tracked_assets, 1):
            mark_backfill_asset_started(
                symbol=asset.display_symbol,
                index=idx,
                total_assets=total,
            )
            publish_event("ohlcv_backfill", "ohlcv.backfill.updated", update_backfill_status())

            logger.info(f"Backfilling OHLCV [{idx}/{total}] for {asset.display_symbol}")
            try:
                ohlcv_list = fetch_ohlcv_with_fallback(
                    asset.provider_symbol,
                    alpha_vantage_key=alpha_vantage_key,
                    period="5y"
                )
                if ohlcv_list:
                    ingest_count = ingest_ohlcv(str(asset.id), ohlcv_list)
                    mark_backfill_asset_completed(
                        symbol=asset.display_symbol,
                        rows_ingested=ingest_count,
                        index=idx,
                        total_assets=total,
                    )
                    publish_event("ohlcv_backfill", "ohlcv.backfill.updated", update_backfill_status())
                    logger.info(f"Ingested {ingest_count} OHLCV records for {asset.display_symbol}")
                    success_count += 1
                else:
                    mark_backfill_asset_failed(
                        symbol=asset.display_symbol,
                        error="No OHLCV data fetched",
                        index=idx,
                        total_assets=total,
                    )
                    publish_event("ohlcv_backfill", "ohlcv.backfill.updated", update_backfill_status())
                    logger.warning(f"No OHLCV data fetched for {asset.display_symbol}")
                    fail_count += 1
            except Exception as error:
                mark_backfill_asset_failed(
                    symbol=asset.display_symbol,
                    error=str(error),
                    index=idx,
                    total_assets=total,
                )
                publish_event("ohlcv_backfill", "ohlcv.backfill.updated", update_backfill_status())
                logger.exception(f"Backfill failed for {asset.display_symbol}")
                fail_count += 1

        finish_backfill_status(state="completed")
        publish_event("ohlcv_backfill", "ohlcv.backfill.completed", update_backfill_status())
        logger.info(f"Backfill complete: {success_count} success, {fail_count} failed")
    except Exception:
        finish_backfill_status(state="failed")
        publish_event("ohlcv_backfill", "ohlcv.backfill.failed", update_backfill_status())
        logger.exception("Backfill task failed")
        raise
    finally:
        clear_backfill_lock()


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


@shared_task
def fetch_asset_news():
    """Fetch and store news for all tracked assets."""
    from .models import Asset
    from .services import NewsService

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

    for asset in tracked_assets:
        try:
            NewsService.fetch_and_store_news(asset)
        except Exception:
            logger.exception(f"Failed to fetch news for {asset.display_symbol}")
