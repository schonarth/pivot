from datetime import date
from decimal import Decimal
from unittest.mock import ANY, patch

import pytest

from markets.models import OHLCV
from markets.ohlcv_provider import OhlcvFetchResult
from markets.tasks import repair_ohlcv_history


@pytest.mark.django_db
class TestOhlcvRepair:
    def test_repair_task_deletes_invalid_rows_and_refetches_requested_window(self, asset):
        bad_day = date(2026, 4, 16)
        OHLCV.objects.create(
            asset=asset,
            date=bad_day,
            open=Decimal("0.0000"),
            high=Decimal("0.0000"),
            low=Decimal("0.0000"),
            close=Decimal("48.5800"),
            volume=0,
            source="yahoo_finance",
        )

        with patch(
            "markets.ohlcv_provider.fetch_ohlcv_with_fallback",
            return_value=OhlcvFetchResult(
                source="yahoo_finance",
                records=[
                    {
                        "date": bad_day,
                        "open": Decimal("47.2900"),
                        "high": Decimal("48.6800"),
                        "low": Decimal("46.7600"),
                        "close": Decimal("48.5800"),
                        "volume": 54484300,
                    }
                ],
            ),
        ) as fetch_ohlcv, patch("realtime.services.publish_event"):
            repair_ohlcv_history(
                source="manual",
                symbol=asset.display_symbol,
                date_from="2026-04-16",
                date_to="2026-04-16",
            )

        fetch_ohlcv.assert_called_once_with(
            asset.provider_symbol,
            alpha_vantage_key=None,
            start_date=bad_day,
            end_date=bad_day,
        )
        stored = OHLCV.objects.filter(asset=asset, date=bad_day).first()
        assert stored is not None
        assert stored.open == Decimal("47.2900")
        assert stored.high == Decimal("48.6800")
        assert stored.low == Decimal("46.7600")
        assert stored.close == Decimal("48.5800")

    @patch("markets.views.queue_ohlcv_repair")
    def test_ohlcv_repair_start_queues_task(self, mock_queue, authenticated_client):
        mock_queue.return_value = (
            True,
            {
                "state": "queued",
                "source": "manual",
                "initiated_by": "user-id",
                "symbol": "PETR4",
                "date_from": "2026-04-16",
                "date_to": "2026-04-16",
                "total_assets": 1,
                "processed_assets_count": 0,
                "invalid_rows_found": 0,
                "invalid_rows_deleted": 0,
                "repaired_rows": 0,
                "current_asset": None,
                "processed_assets": [],
                "started_at": "2026-04-16T00:00:00Z",
                "updated_at": "2026-04-16T00:00:01Z",
                "completed_at": None,
            },
        )

        response = authenticated_client.post(
            "/api/markets/ohlcv-repair/",
            {
                "symbol": "PETR4",
                "date_from": "2026-04-16",
                "date_to": "2026-04-16",
            },
            format="json",
        )

        assert response.status_code == 202
        assert response.data["queued"] is True
        mock_queue.assert_called_once_with(
            source="manual",
            initiated_by=ANY,
            symbol="PETR4",
            date_from="2026-04-16",
            date_to="2026-04-16",
        )
