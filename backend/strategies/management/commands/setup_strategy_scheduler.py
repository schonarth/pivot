from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Command(BaseCommand):
    help = "Set up periodic task for evaluating active strategies"

    def handle(self, *args, **options):
        # Create interval schedule: every 5 minutes
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )

        # Create or update the periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name="Evaluate Active Strategies",
            defaults={
                "task": "strategies.tasks.evaluate_active_strategies",
                "interval": schedule,
                "enabled": True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("Created periodic task: Evaluate Active Strategies (every 5 minutes)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Periodic task already exists: Evaluate Active Strategies")
            )
