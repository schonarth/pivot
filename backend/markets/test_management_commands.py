from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestEnsureHistoricalOhlcvCommand:
    def test_queues_backfill_on_startup(self):
        with patch(
            "markets.management.commands.ensure_historical_ohlcv.queue_ohlcv_backfill",
            return_value=(True, {"state": "queued"}),
        ) as queue:
            call_command("ensure_historical_ohlcv")

        queue.assert_called_once_with(source="startup")

    def test_reports_when_backfill_is_already_running(self):
        with patch(
            "markets.management.commands.ensure_historical_ohlcv.queue_ohlcv_backfill",
            return_value=(False, {"state": "running"}),
        ) as queue:
            call_command("ensure_historical_ohlcv")

        queue.assert_called_once_with(source="startup")
