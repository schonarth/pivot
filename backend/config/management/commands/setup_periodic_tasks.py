from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule


class Command(BaseCommand):
    help = "Set up periodic Celery Beat tasks"

    def handle(self, *args, **options):
        price_interval, _ = IntervalSchedule.objects.get_or_create(
            every=300,
            period=IntervalSchedule.SECONDS,
        )

        PeriodicTask.objects.update_or_create(
            name="fetch_market_prices",
            defaults={
                "task": "markets.tasks.fetch_market_prices",
                "interval": price_interval,
            },
        )

        snapshot_interval, _ = IntervalSchedule.objects.get_or_create(
            every=300,
            period=IntervalSchedule.SECONDS,
        )

        PeriodicTask.objects.update_or_create(
            name="capture_portfolio_snapshots",
            defaults={
                "task": "config.tasks.capture_portfolio_snapshots",
                "interval": snapshot_interval,
            },
        )

        self.stdout.write(self.style.SUCCESS("Periodic tasks configured."))