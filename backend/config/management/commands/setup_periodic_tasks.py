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

        indicator_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=17,
            minute=0,
            day_of_week="*",
        )

        PeriodicTask.objects.update_or_create(
            name="calculate_indicators_daily",
            defaults={
                "task": "trading.tasks.calculate_indicators_daily",
                "crontab": indicator_schedule,
            },
        )

        news_interval, _ = IntervalSchedule.objects.get_or_create(
            every=21600,
            period=IntervalSchedule.SECONDS,
        )

        PeriodicTask.objects.update_or_create(
            name="fetch_asset_news",
            defaults={
                "task": "markets.tasks.fetch_asset_news",
                "interval": news_interval,
            },
        )

        sentiment_interval, _ = IntervalSchedule.objects.get_or_create(
            every=3600,
            period=IntervalSchedule.SECONDS,
        )

        PeriodicTask.objects.update_or_create(
            name="analyze_news_sentiment",
            defaults={
                "task": "ai.tasks.analyze_news_sentiment",
                "interval": sentiment_interval,
            },
        )

        self.stdout.write(self.style.SUCCESS("Periodic tasks configured."))