from celery import shared_task
import logging

logger = logging.getLogger("paper_trader.trading")


@shared_task
def calculate_indicators_daily():
    """Calculate technical indicators daily for all tracked assets.

    Runs after market close for assets with positions or active alerts.
    """
    from markets.models import Asset
    from trading.technical import IndicatorCalculator

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
            indicators = IndicatorCalculator.calculate_indicators(str(asset.id), asset.display_symbol)
            if indicators:
                IndicatorCalculator.ingest_indicators(str(asset.id), indicators)
                logger.info(f"Calculated indicators for {asset.display_symbol}")
        except Exception:
            logger.exception(f"Failed to calculate indicators for {asset.display_symbol}")


@shared_task
def calculate_indicators_for_asset(asset_id: str):
    """Calculate technical indicators on-demand for a specific asset.

    Args:
        asset_id: Asset UUID
    """
    from trading.technical import IndicatorCalculator
    from markets.models import Asset

    try:
        asset = Asset.objects.get(id=asset_id)
        indicators = IndicatorCalculator.calculate_indicators(asset_id, asset.display_symbol)
        if indicators:
            IndicatorCalculator.ingest_indicators(asset_id, indicators)
    except Asset.DoesNotExist:
        logger.warning(f"Asset {asset_id} not found")
    except Exception:
        logger.exception(f"Failed to calculate indicators for asset {asset_id}")
