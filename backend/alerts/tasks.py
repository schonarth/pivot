import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger("paper_trader.alerts")


@shared_task
def evaluate_alerts_for_assets(asset_ids: list[str]):
    from decimal import Decimal

    from markets.models import Asset, AssetQuote
    from .models import Alert
    from .services import evaluate_alert

    for asset_id in asset_ids:
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            continue

        quote = AssetQuote.objects.filter(asset=asset).order_by("-fetched_at").first()
        if quote is None:
            continue

        current_price = quote.price

        with transaction.atomic():
            alerts = Alert.objects.filter(asset_id=asset_id, status="active").select_for_update()
            for alert in alerts:
                try:
                    evaluate_alert(alert, current_price)
                except Exception:
                    logger.exception("Failed to evaluate alert %s", alert.id)