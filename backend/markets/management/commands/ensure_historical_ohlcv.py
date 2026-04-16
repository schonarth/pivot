from markets.backfill_progress import queue_ohlcv_backfill
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Queue OHLCV backfill when tracked assets are missing history."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="startup")

    def handle(self, *args, **options):
        queued, status = queue_ohlcv_backfill(source=options["source"])
        if queued:
            self.stdout.write(self.style.SUCCESS("Queued OHLCV historical backfill."))
            return

        if status.get("state") in {"queued", "running"}:
            self.stdout.write(self.style.SUCCESS("OHLCV backfill already queued."))
            return

        self.stdout.write(self.style.SUCCESS("OHLCV backfill not started."))
