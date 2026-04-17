from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache

from markets.backfill_progress import get_backfill_status
from markets.models import Asset, OHLCV
from markets.ohlcv_provider import OhlcvFetchResult
from markets.tasks import backfill_ohlcv_historical


def make_ohlcv_list(day: date):
    return [
        {
            "date": day,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        }
    ]


def seed_ohlcv_history(asset: Asset, start_day: date, days: int = 200):
    OHLCV.objects.bulk_create(
        [
            OHLCV(
                asset=asset,
                date=start_day + timedelta(days=offset),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000 + offset,
                source="yahoo_finance",
            )
            for offset in range(days)
        ]
    )


@pytest.mark.django_db
class TestOhlcvBackfillProgress:
    def test_backfill_task_records_progress(self):
        cache.clear()
        Asset.objects.create(
            display_symbol="AAA",
            provider_symbol="AAA",
            name="AAA Holdings",
            market="US",
            exchange="XNYS",
            currency="USD",
            is_seeded=True,
        )
        Asset.objects.create(
            display_symbol="BBB",
            provider_symbol="BBB",
            name="BBB Holdings",
            market="US",
            exchange="XNYS",
            currency="USD",
            is_seeded=True,
        )

        with patch(
            "markets.ohlcv_provider.fetch_ohlcv_with_fallback",
            side_effect=[
                OhlcvFetchResult(source="yahoo_finance", records=make_ohlcv_list(date(2026, 4, 15))),
                OhlcvFetchResult(source="yahoo_finance", records=make_ohlcv_list(date(2026, 4, 15))),
            ],
        ), patch("realtime.services.publish_event"):
            backfill_ohlcv_historical(source="startup")

        status = get_backfill_status()

        assert status["state"] == "completed"
        assert status["processed_assets_count"] == 2
        assert status["successful_assets"] == 2
        assert status["failed_assets"] == 0
        assert status["current_asset"] is None
        assert set(item["symbol"] for item in status["processed_assets"]) == {"AAA", "BBB"}

    def test_backfill_task_noops_when_history_is_already_complete(self):
        cache.clear()
        asset = Asset.objects.create(
            display_symbol="AAA",
            provider_symbol="AAA",
            name="AAA Holdings",
            market="US",
            exchange="XNYS",
            currency="USD",
            is_seeded=True,
        )
        seed_ohlcv_history(asset, date(2024, 1, 1))

        with patch("markets.ohlcv_provider.fetch_ohlcv_with_fallback") as fetch, patch(
            "realtime.services.publish_event"
        ):
            backfill_ohlcv_historical(source="startup")

        status = get_backfill_status()

        assert status["state"] == "completed"
        assert status["processed_assets_count"] == 0
        assert status["successful_assets"] == 0
        assert status["failed_assets"] == 0
        assert status["current_asset"] is None
        fetch.assert_not_called()
