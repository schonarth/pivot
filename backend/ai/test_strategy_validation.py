from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from ai.models import StrategyRecommendation
from markets.models import AssetQuote, NewsItem, OHLCV, TechnicalIndicators


def make_quote(asset, price=Decimal("100.00")):
    return AssetQuote.objects.create(
        asset=asset,
        price=price,
        currency=asset.currency,
        as_of=timezone.now(),
    )


def make_ohlcv(asset, closes):
    start = timezone.now().date() - timedelta(days=len(closes) - 1)
    for index, close in enumerate(closes):
        OHLCV.objects.create(
            asset=asset,
            date=start + timedelta(days=index),
            open=Decimal(str(close)),
            high=Decimal(str(close)) + Decimal("1.00"),
            low=Decimal(str(close)) - Decimal("1.00"),
            close=Decimal(str(close)),
            volume=1000 + index,
        )


def make_indicators(asset, *, positive=True):
    TechnicalIndicators.objects.create(
        asset=asset,
        date=timezone.now().date(),
        rsi_14=Decimal("62.00") if positive else Decimal("38.00"),
        macd=Decimal("1.50") if positive else Decimal("-1.50"),
        macd_signal=Decimal("1.00") if positive else Decimal("-1.00"),
        macd_histogram=Decimal("0.50") if positive else Decimal("-0.50"),
        ma_20=Decimal("95.00") if positive else Decimal("105.00"),
        ma_50=Decimal("90.00") if positive else Decimal("110.00"),
        ma_200=Decimal("80.00") if positive else Decimal("120.00"),
        bb_upper=Decimal("115.00"),
        bb_middle=Decimal("100.00"),
        bb_lower=Decimal("85.00"),
        volume_20d_avg=1000,
    )


def make_news(asset, headline, score):
    return NewsItem.objects.create(
        asset=asset,
        headline=headline,
        url=f"https://example.com/{asset.display_symbol}/{score}",
        source="fixture",
        sentiment_score=Decimal(str(score)),
        published_at=timezone.now(),
    )


@pytest.mark.django_db
class TestStrategyValidation:
    def test_strategy_validation_approves_aligned_candidate(self, authenticated_client, portfolio, asset):
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, f"{asset.display_symbol} raises guidance after earnings beat", "0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 2,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["verdict"] == "approve"
        assert response.data["technical_inputs"]["vote"] == "positive"
        assert response.data["context_inputs"]["vote"] == "positive"
        assert StrategyRecommendation.objects.filter(candidate_id=response.data["candidate_id"]).exists()

    @patch("ai.strategy_validation.StrategyValidationService._generate_rationale")
    def test_strategy_validation_saves_generated_rationale(
        self,
        mock_generate_rationale,
        authenticated_client,
        portfolio,
        asset,
    ):
        rationale = (
            "This buy has a reasonable setup. The chart is improving, recent context is supportive, "
            "and the short-window move is not fighting the trade idea."
        )
        mock_generate_rationale.return_value = rationale
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, f"{asset.display_symbol} raises guidance after earnings beat", "0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 2,
            },
            format="json",
        )

        recommendation = StrategyRecommendation.objects.get(candidate_id=response.data["candidate_id"])
        assert response.data["rationale"] == rationale
        assert recommendation.rationale == rationale

    def test_strategy_validation_rejects_hard_conflict(self, authenticated_client, portfolio, asset):
        make_quote(asset)
        make_ohlcv(asset, [104, 102, 100, 98, 96])
        make_indicators(asset, positive=False)
        make_news(asset, f"{asset.display_symbol} cuts outlook after earnings miss", "-0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 2,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["verdict"] == "reject"
        assert response.data["technical_inputs"]["vote"] == "negative"

    def test_strategy_validation_defers_missing_context_support(self, authenticated_client, portfolio, asset):
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 2,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["verdict"] == "defer"
        assert response.data["context_inputs"]["item_count"] == 0

    @patch("realtime.services.publish_event")
    def test_rejected_validation_does_not_block_manual_trade(
        self,
        mock_publish,
        authenticated_client,
        portfolio_with_cash,
        asset,
    ):
        make_quote(asset)
        make_ohlcv(asset, [104, 102, 100, 98, 96])
        make_indicators(asset, positive=False)
        make_news(asset, f"{asset.display_symbol} cuts outlook after earnings miss", "-0.80")

        validation = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio_with_cash.id),
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 1,
            },
            format="json",
        )

        trade = authenticated_client.post(
            f"/api/portfolios/{portfolio_with_cash.id}/trades/",
            {
                "asset_id": str(asset.id),
                "action": "BUY",
                "quantity": 1,
                "rationale": "Manual review",
            },
            format="json",
        )

        assert validation.data["verdict"] == "reject"
        assert trade.status_code == 201
        assert trade.data["trade"]["action"] == "BUY"
