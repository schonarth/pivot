from celery import shared_task
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
    for market_code, cfg in MARKET_CONFIGS.items():
        if not is_market_open(market_code):
            continue
        market_assets = tracked_assets.filter(market=market_code)
        for asset in market_assets:
            try:
                quote = refresh_asset_quote(str(asset.id))
                if quote:
                    refreshed_asset_ids.append(str(asset.id))
            except Exception:
                logger.exception("Failed to refresh quote for asset %s", asset.display_symbol)

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