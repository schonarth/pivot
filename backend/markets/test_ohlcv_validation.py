from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from markets.models import OHLCV
from markets.ohlcv_provider import OhlcvFetchResult, fetch_ohlcv_with_fallback
from markets.quote_provider import refresh_asset_quote
from markets.services import ingest_ohlcv


@pytest.mark.django_db
class TestOhlcvValidation:
    def test_fetch_ohlcv_with_fallback_uses_alpha_vantage_when_yahoo_returns_invalid_rows(self):
        valid_rows = [
            {
                "date": date(2026, 4, 15),
                "open": Decimal("100.0000"),
                "high": Decimal("101.0000"),
                "low": Decimal("99.0000"),
                "close": Decimal("100.5000"),
                "volume": 1000,
            }
        ]

        with patch("markets.ohlcv_provider.fetch_yahoo_historical", return_value=[
            {
                "date": date(2026, 4, 16),
                "open": Decimal("0.0000"),
                "high": Decimal("0.0000"),
                "low": Decimal("0.0000"),
                "close": Decimal("48.5800"),
                "volume": 0,
            }
        ]), patch("markets.ohlcv_provider.fetch_alpha_vantage_historical", return_value=valid_rows):
            result = fetch_ohlcv_with_fallback("PETR4.SA", alpha_vantage_key="key", period="1d")

        assert result is not None
        assert result.source == "alpha_vantage"
        assert result.records == valid_rows

    def test_ingest_ohlcv_discards_invalid_rows(self, asset):
        valid_day = {
            "date": date(2026, 4, 16),
            "open": Decimal("47.2900"),
            "high": Decimal("48.6800"),
            "low": Decimal("46.7600"),
            "close": Decimal("48.5800"),
            "volume": 54484300,
        }
        invalid_day = {
            "date": date(2026, 4, 15),
            "open": Decimal("0.0000"),
            "high": Decimal("0.0000"),
            "low": Decimal("0.0000"),
            "close": Decimal("48.5800"),
            "volume": 0,
        }

        count = ingest_ohlcv(str(asset.id), [invalid_day, valid_day], source="alpha_vantage")

        stored = OHLCV.objects.filter(asset=asset).order_by("date")

        assert count == 1
        assert stored.count() == 1
        assert stored.first().date == valid_day["date"]
        assert stored.first().source == "alpha_vantage"

    def test_refresh_asset_quote_repairs_recent_invalid_ohlcv_window(self, asset):
        asset.provider_symbol = "PETR4.SA"
        asset.currency = "BRL"
        asset.save()

        with patch("markets.quote_provider.fetch_yahoo_quote", return_value={
            "price": Decimal("48.5800"),
            "source": "yahoo_finance",
            "as_of": timezone.now(),
            "is_delayed": True,
            "provider_payload": {"symbol": asset.provider_symbol},
        }), patch("markets.services.recent_ohlcv_needs_repair", return_value=True), patch(
            "markets.ohlcv_provider.fetch_ohlcv_with_fallback",
            return_value=OhlcvFetchResult(
                source="alpha_vantage",
                records=[
                    {
                        "date": date(2026, 4, 15),
                        "open": Decimal("47.9500"),
                        "high": Decimal("48.1000"),
                        "low": Decimal("46.7300"),
                        "close": Decimal("46.8900"),
                        "volume": 61852100,
                    }
                ],
            ),
        ) as fetch_ohlcv, patch("markets.services.ingest_ohlcv") as ingest:
            refresh_asset_quote(str(asset.id))

        fetch_ohlcv.assert_called_once_with(asset.provider_symbol, period="5d")
        ingest.assert_called_once()
        assert ingest.call_args.kwargs["source"] == "alpha_vantage"
