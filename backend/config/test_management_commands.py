from unittest.mock import patch

import pytest
from django.core.management import call_command
from django_celery_beat.models import PeriodicTask

from django.conf import settings


@pytest.mark.django_db
def test_setup_periodic_tasks_registers_refresh_jobs_and_kicks_off_prices():
    with patch("config.management.commands.setup_periodic_tasks.fetch_market_prices.delay") as kickoff:
        call_command("setup_periodic_tasks")

    kickoff.assert_called_once()
    assert PeriodicTask.objects.filter(name="fetch_market_prices", task="markets.tasks.fetch_market_prices").exists()
    assert PeriodicTask.objects.filter(
        name="refresh_untracked_asset_prices",
        task="markets.tasks.refresh_untracked_asset_prices",
    ).exists()

    fetch_task = PeriodicTask.objects.get(name="fetch_market_prices")
    assert fetch_task.interval.every == settings.PRICE_REFRESH_INTERVAL
    assert fetch_task.interval.period == "seconds"

    untracked_task = PeriodicTask.objects.get(name="refresh_untracked_asset_prices")
    assert untracked_task.interval.every == 3600
    assert untracked_task.interval.period == "seconds"
