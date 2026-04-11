import uuid
from decimal import Decimal, InvalidOperation

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Simulate a market price update for an asset, triggering the full alert evaluation pipeline."

    def add_arguments(self, parser):
        parser.add_argument("symbol", type=str, help="Asset display symbol (e.g. AAPL)")
        parser.add_argument("price", type=str, help="Simulated price (e.g. 150.00)")

    def handle(self, *args, **options):
        from markets.models import Asset, AssetQuote
        from alerts.tasks import evaluate_alerts_for_assets

        symbol = options["symbol"].upper()

        try:
            price = Decimal(options["price"])
        except InvalidOperation:
            raise CommandError(f"Invalid price: {options['price']!r}")

        if price <= 0:
            raise CommandError("Price must be positive")

        try:
            asset = Asset.objects.get(display_symbol=symbol)
        except Asset.DoesNotExist:
            raise CommandError(f"Asset '{symbol}' not found")
        except Asset.MultipleObjectsReturned:
            raise CommandError(f"Multiple assets match '{symbol}'; be more specific")

        now = timezone.now()

        cache_key = f"price:{asset.id}"
        cache.set(
            cache_key,
            {"price": str(price), "as_of": now.isoformat(), "source": "simulated"},
            timeout=3600,
        )

        AssetQuote.objects.create(
            id=uuid.uuid4(),
            asset=asset,
            price=price,
            currency=asset.currency,
            source="simulated",
            as_of=now,
            is_delayed=False,
        )

        evaluate_alerts_for_assets([str(asset.id)])

        self.stdout.write(
            self.style.SUCCESS(f"Simulated {symbol} @ {price} — alert evaluation complete")
        )
