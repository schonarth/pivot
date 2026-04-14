import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from markets.models import OHLCV, TechnicalIndicators
from trading.technical import IndicatorCalculator


@pytest.mark.django_db
class TestIndicatorCalculator:
    def test_ingest_indicators_stores_latest_snapshot(self, asset):
        stored = IndicatorCalculator.ingest_indicators(
            str(asset.id),
            {
                "date": timezone.now().date(),
                "rsi_14": 54.32,
                "macd": 1.23456,
                "macd_signal": 1.11111,
                "macd_histogram": 0.12345,
                "ma_20": 101.23456,
                "ma_50": 99.87654,
                "ma_200": 88.76543,
                "bb_upper": 110.99999,
                "bb_middle": 100.11111,
                "bb_lower": 90.22222,
                "volume_20d_avg": 1234567,
            },
        )

        assert stored is True

        indicators = TechnicalIndicators.objects.get(asset=asset)
        assert indicators.rsi_14 == Decimal("54.32")
        assert indicators.macd == Decimal("1.2346")
        assert indicators.bb_lower == Decimal("90.2222")
        assert indicators.volume_20d_avg == 1234567

    def test_calculate_indicators_returns_none_when_history_is_too_short(self, asset):
        base_date = timezone.now().date() - timedelta(days=10)
        for offset in range(10):
            close = Decimal("100.00") + Decimal(str(offset))
            OHLCV.objects.create(
                asset=asset,
                date=base_date + timedelta(days=offset),
                open=close - Decimal("1.00"),
                high=close + Decimal("1.00"),
                low=close - Decimal("2.00"),
                close=close,
                volume=1000 + offset,
            )

        indicators = IndicatorCalculator.calculate_indicators(str(asset.id), asset.display_symbol)

        assert indicators is None
