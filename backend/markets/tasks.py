import logging
from collections import deque
from datetime import date, timedelta
from celery import shared_task
from django.conf import settings
from django.db.models import Count, Max, Q

logger = logging.getLogger("paper_trader.markets")

UNTRACKED_PRICE_REFRESH_BATCH_SIZE = 50
UNTRACKED_PRICE_REFRESH_STATE = {
    "seeded_for": None,
    "pending": deque(),
    "failed": set(),
}


def _refresh_asset(asset, refreshed_asset_ids, portfolios_to_notify):
    from .quote_provider import refresh_asset_quote

    quote = refresh_asset_quote(str(asset.id))
    if quote is None:
        return False

    refreshed_asset_ids.append(str(asset.id))
    for position in asset.positions.all():
        portfolios_to_notify.add(str(position.portfolio_id))
    for membership in asset.portfolio_watch_memberships.all():
        portfolios_to_notify.add(str(membership.portfolio_id))
    return True


def _seed_untracked_price_refresh_state():
    from django.utils import timezone
    from .models import Asset
    from portfolios.models import PortfolioWatchMembership
    from trading.models import Position

    cutoff = timezone.now() - timedelta(hours=24)
    held_asset_ids = Position.objects.values_list("asset_id", flat=True).distinct()
    watched_asset_ids = PortfolioWatchMembership.objects.values_list("asset_id", flat=True).distinct()
    asset_ids = list(
        Asset.objects.exclude(id__in=held_asset_ids)
        .exclude(id__in=watched_asset_ids)
        .exclude(alerts__status="active")
        .annotate(latest_quote_at=Max("quotes__fetched_at"))
        .filter(Q(latest_quote_at__lt=cutoff) | Q(latest_quote_at__isnull=True))
        .order_by("latest_quote_at", "created_at", "id")
        .values_list("id", flat=True)
    )

    today = timezone.localdate()
    UNTRACKED_PRICE_REFRESH_STATE["seeded_for"] = today
    UNTRACKED_PRICE_REFRESH_STATE["pending"] = deque(str(asset_id) for asset_id in asset_ids)
    UNTRACKED_PRICE_REFRESH_STATE["failed"] = set()


def _refresh_asset_group(asset_queryset, refreshed_asset_ids, portfolios_to_notify):
    from .services import is_market_open

    for asset in asset_queryset:
        if not is_market_open(asset.market):
            continue
        try:
            _refresh_asset(asset, refreshed_asset_ids, portfolios_to_notify)
        except Exception:
            logger.exception("Failed to refresh quote for asset %s", asset.display_symbol)


@shared_task
def fetch_market_prices():
    from .models import Asset

    refreshed_asset_ids = []
    portfolios_to_notify = set()
    held_asset_ids = list(Asset.objects.filter(positions__isnull=False).distinct().values_list("id", flat=True))
    watched_asset_ids = list(
        Asset.objects.filter(portfolio_watch_memberships__isnull=False)
        .exclude(id__in=held_asset_ids)
        .distinct()
        .values_list("id", flat=True)
    )

    held_assets = Asset.objects.filter(id__in=held_asset_ids).order_by("display_symbol")
    watched_assets = Asset.objects.filter(id__in=watched_asset_ids).order_by("display_symbol")
    alert_assets = (
        Asset.objects.filter(alerts__status="active")
        .exclude(id__in=held_asset_ids)
        .exclude(id__in=watched_asset_ids)
        .distinct()
        .order_by("display_symbol")
    )

    _refresh_asset_group(held_assets, refreshed_asset_ids, portfolios_to_notify)
    _refresh_asset_group(watched_assets, refreshed_asset_ids, portfolios_to_notify)
    _refresh_asset_group(alert_assets, refreshed_asset_ids, portfolios_to_notify)

    if portfolios_to_notify:
        from realtime.services import publish_event
        for portfolio_id in portfolios_to_notify:
            publish_event(f"portfolio_{portfolio_id}", "price.updated", {"portfolio_id": portfolio_id})

    if refreshed_asset_ids:
        from alerts.tasks import evaluate_alerts_for_assets

        evaluate_alerts_for_assets.delay(refreshed_asset_ids)


@shared_task
def refresh_untracked_asset_prices():
    from django.utils import timezone
    from .quote_provider import refresh_asset_quote

    today = timezone.localdate()
    if UNTRACKED_PRICE_REFRESH_STATE["seeded_for"] != today:
        _seed_untracked_price_refresh_state()

    pending = UNTRACKED_PRICE_REFRESH_STATE["pending"]
    if not pending:
        return 0

    refreshed_asset_ids = []
    attempts = 0
    while pending and attempts < UNTRACKED_PRICE_REFRESH_BATCH_SIZE:
        asset_id = pending.popleft()
        attempts += 1
        try:
            if refresh_asset_quote(asset_id):
                refreshed_asset_ids.append(asset_id)
            else:
                UNTRACKED_PRICE_REFRESH_STATE["failed"].add(asset_id)
        except Exception:
            UNTRACKED_PRICE_REFRESH_STATE["failed"].add(asset_id)
            logger.exception("Failed to refresh quote for asset %s", asset_id)

    return len(refreshed_asset_ids)


@shared_task
def refresh_single_asset_quote(asset_id: str):
    from .quote_provider import refresh_asset_quote

    try:
        refresh_asset_quote(asset_id)
    except Exception:
        logger.exception("Failed to refresh quote for asset %s", asset_id)


@shared_task
def backfill_single_asset_ohlcv(asset_id: str, initiated_by: str | None = None):
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .services import ingest_ohlcv
    from realtime.services import publish_event

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None

    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        return

    publish_event(
        f"asset_{asset_id}",
        "ohlcv.backfill.started",
        {"asset_id": asset_id, "symbol": asset.display_symbol},
    )

    try:
        ohlcv_result = fetch_ohlcv_with_fallback(
            asset.provider_symbol,
            alpha_vantage_key=alpha_vantage_key,
            period="5y",
        )
        rows_ingested = 0
        if ohlcv_result:
            rows_ingested = ingest_ohlcv(str(asset.id), ohlcv_result.records, source=ohlcv_result.source)
        publish_event(
            f"asset_{asset_id}",
            "ohlcv.backfill.completed",
            {
                "asset_id": asset_id,
                "symbol": asset.display_symbol,
                "rows_ingested": rows_ingested,
                "initiated_by": initiated_by,
            },
        )
    except Exception:
        publish_event(
            f"asset_{asset_id}",
            "ohlcv.backfill.failed",
            {"asset_id": asset_id, "symbol": asset.display_symbol},
        )
        logger.exception("Single-asset backfill failed for %s", asset.display_symbol)


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
                ohlcv_result = fetch_ohlcv_with_fallback(
                    asset.provider_symbol,
                    alpha_vantage_key=alpha_vantage_key,
                    period="5y"
                )
                if ohlcv_result:
                    ingest_count = ingest_ohlcv(str(asset.id), ohlcv_result.records, source=ohlcv_result.source)
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
    from .services import ingest_ohlcv, recent_ohlcv_needs_repair

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None

    tracked_assets = Asset.objects.filter(is_seeded=True).distinct()

    for asset in tracked_assets:
        try:
            period = "5d" if recent_ohlcv_needs_repair(str(asset.id)) else "1d"
            ohlcv_result = fetch_ohlcv_with_fallback(
                asset.provider_symbol,
                alpha_vantage_key=alpha_vantage_key,
                period=period,
            )
            if ohlcv_result:
                ingest_ohlcv(str(asset.id), ohlcv_result.records, source=ohlcv_result.source)
        except Exception:
            logger.exception(f"Failed to fetch daily OHLCV for {asset.display_symbol}")


@shared_task
def repair_ohlcv_history(
    source: str = "manual",
    initiated_by: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    from .models import Asset
    from .ohlcv_provider import fetch_ohlcv_with_fallback
    from .repair_progress import (
        clear_repair_lock,
        finish_repair_status,
        mark_repair_asset_completed,
        mark_repair_asset_failed,
        mark_repair_asset_started,
        update_repair_status,
    )
    from .services import delete_invalid_ohlcv_rows, ingest_ohlcv, invalid_ohlcv_dates
    from realtime.services import publish_event

    alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, "ALPHA_VANTAGE_API_KEY") else None
    start_date = date.fromisoformat(date_from) if date_from else None
    end_date = date.fromisoformat(date_to) if date_to else None

    queryset = Asset.objects.filter(ohlcv_data__isnull=False)
    if symbol:
        queryset = queryset.filter(Q(display_symbol__iexact=symbol) | Q(provider_symbol__iexact=symbol))
    tracked_assets = queryset.distinct().order_by("market", "display_symbol")
    total = tracked_assets.count()

    update_repair_status(
        state="running",
        source=source,
        initiated_by=initiated_by,
        symbol=symbol,
        date_from=date_from,
        date_to=date_to,
        total_assets=total,
    )
    publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())

    if total == 0:
        finish_repair_status(state="completed")
        publish_event("ohlcv_repair", "ohlcv.repair.completed", update_repair_status())
        return

    try:
        for idx, asset in enumerate(tracked_assets, 1):
            mark_repair_asset_started(
                symbol=asset.display_symbol,
                index=idx,
                total_assets=total,
            )
            publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())

            try:
                invalid_dates = invalid_ohlcv_dates(
                    str(asset.id),
                    start_date=start_date,
                    end_date=end_date,
                )
                if not invalid_dates:
                    mark_repair_asset_completed(
                        symbol=asset.display_symbol,
                        invalid_rows_deleted=0,
                        rows_ingested=0,
                        index=idx,
                        total_assets=total,
                    )
                    publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())
                    continue

                fetch_start = start_date or min(invalid_dates)
                fetch_end = end_date or max(invalid_dates)
                ohlcv_result = fetch_ohlcv_with_fallback(
                    asset.provider_symbol,
                    alpha_vantage_key=alpha_vantage_key,
                    start_date=fetch_start,
                    end_date=fetch_end,
                )
                if ohlcv_result:
                    delete_invalid_ohlcv_rows(
                        str(asset.id),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    ingest_count = ingest_ohlcv(str(asset.id), ohlcv_result.records, source=ohlcv_result.source)
                    mark_repair_asset_completed(
                        symbol=asset.display_symbol,
                        invalid_rows_deleted=len(invalid_dates),
                        rows_ingested=ingest_count,
                        index=idx,
                        total_assets=total,
                    )
                    publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())
                else:
                    mark_repair_asset_failed(
                        symbol=asset.display_symbol,
                        error="No OHLCV data fetched",
                        index=idx,
                        total_assets=total,
                    )
                    publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())
            except Exception as error:
                mark_repair_asset_failed(
                    symbol=asset.display_symbol,
                    error=str(error),
                    index=idx,
                    total_assets=total,
                )
                publish_event("ohlcv_repair", "ohlcv.repair.updated", update_repair_status())
                logger.exception("OHLCV repair failed for %s", asset.display_symbol)

        finish_repair_status(state="completed")
        publish_event("ohlcv_repair", "ohlcv.repair.completed", update_repair_status())
    except Exception:
        finish_repair_status(state="failed")
        publish_event("ohlcv_repair", "ohlcv.repair.failed", update_repair_status())
        logger.exception("OHLCV repair task failed")
        raise
    finally:
        clear_repair_lock()


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
