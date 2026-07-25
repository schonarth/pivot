from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from ai.models import RecommendationInvalidation, StrategyRecommendation, StrategyScenarioFrame
from ai.services import EvidenceReviewService
from ai.strategy_validation import (
    _normalize_ai_scenario_payloads,
    _parse_scenario_response,
    validate_scenario_frame_payloads,
)
from markets.models import OHLCV, AssetQuote, NewsItem, NewsSource, TechnicalIndicators
from portfolios.models import Portfolio, PortfolioGuardrails
from trading.models import Position


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
    news_source, _ = NewsSource.objects.get_or_create(
        feed_url="https://finance.yahoo.com/quote/{symbol}/news",
        defaults={"institution_name": "Yahoo Finance"},
    )
    return NewsItem.objects.create(
        asset=asset,
        headline=headline,
        url=f"https://example.com/{asset.display_symbol}/{score}",
        source="fixture",
        news_source=news_source,
        sentiment_score=Decimal(str(score)),
        published_at=timezone.now(),
    )


def make_recommendation(*, user, portfolio, asset, news_item):
    return StrategyRecommendation.objects.create(
        user=user,
        portfolio=portfolio,
        asset=asset,
        action="BUY",
        quantity=1,
        candidate={"asset_symbol": asset.display_symbol},
        technical_inputs={"vote": "positive"},
        context_inputs={
            "vote": "positive",
            "items": [{"news_item_id": str(news_item.id), "headline": news_item.headline}],
        },
        sentiment_trajectory_inputs={"vote": "positive", "entries": []},
        verdict="approve",
        rationale="Stored recommendation rationale.",
    )
@pytest.mark.django_db
class TestStrategyValidation:
    def test_material_correction_invalidates_matching_recommendation_idempotently_and_keeps_snapshot(
        self, user, portfolio, asset
    ):
        news_item = make_news(asset, f"{asset.display_symbol} raises guidance", "0.80")
        recommendation = make_recommendation(user=user, portfolio=portfolio, asset=asset, news_item=news_item)
        original_context = recommendation.context_inputs
        service = EvidenceReviewService(user)

        correction = service.create_fact_correction(
            news_item=news_item,
            fact_key="guidance",
            corrected_value="Guidance was withdrawn.",
            correction_state="corrected",
            reason="Issuer correction.",
        )
        service.invalidate_recommendations_for_trigger(correction)

        assert RecommendationInvalidation.objects.filter(
            recommendation=recommendation, fact_correction=correction
        ).count() == 1
        recommendation.refresh_from_db()
        assert recommendation.context_inputs == original_context

    def test_artifact_disputed_invalidates_only_matching_operator_recommendation(self, user, user2, portfolio, asset):
        news_item = make_news(asset, f"{asset.display_symbol} raises guidance", "0.80")
        matching = make_recommendation(user=user, portfolio=portfolio, asset=asset, news_item=news_item)
        other_portfolio = Portfolio.objects.create(
            user=user2,
            name="Other portfolio",
            market=asset.market,
            initial_capital=Decimal("1000.00"),
            current_cash=Decimal("1000.00"),
        )
        other = make_recommendation(user=user2, portfolio=other_portfolio, asset=asset, news_item=news_item)

        review = EvidenceReviewService(user).set_artifact_review(news_item, "disputed", "Conflicting report.")

        assert RecommendationInvalidation.objects.filter(recommendation=matching, artifact_review=review).exists()
        assert not RecommendationInvalidation.objects.filter(recommendation=other).exists()

    def test_accepted_artifact_and_source_stance_do_not_invalidate_recommendations(self, user, portfolio, asset):
        news_item = make_news(asset, f"{asset.display_symbol} raises guidance", "0.80")
        recommendation = make_recommendation(user=user, portfolio=portfolio, asset=asset, news_item=news_item)
        service = EvidenceReviewService(user)

        service.set_artifact_review(news_item, "accepted", "Confirmed.")
        service.set_source_stance(news_item.news_source, "untrusted")

        assert not RecommendationInvalidation.objects.filter(recommendation=recommendation).exists()

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
        assert [frame["scenario_case"] for frame in response.data["scenario_frames"]] == ["base", "bull", "bear"]
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

    def test_strategy_validation_defers_when_evidence_votes_conflict(self, authenticated_client, portfolio, asset):
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, f"{asset.display_symbol} cuts outlook after earnings miss", "-0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {"portfolio_id": str(portfolio.id), "asset_id": str(asset.id), "action": "BUY", "quantity": 2},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["verdict"] == "defer"

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

    def test_strategy_validation_persists_scenario_risk_from_guardrails_and_position(
        self,
        authenticated_client,
        portfolio,
        asset,
    ):
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, f"{asset.display_symbol} raises guidance after earnings beat", "0.80")
        PortfolioGuardrails.objects.create(portfolio=portfolio, enabled=True, max_position_size_pct=Decimal("15.00"))
        Position.objects.create(portfolio=portfolio, asset=asset, quantity=3, average_cost=Decimal("90.00"))

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
        frames = list(StrategyScenarioFrame.objects.filter(recommendation=recommendation))
        risk_notes = {frame.risk_notes for frame in frames}
        guidance = {frame.position_size_guidance for frame in frames}

        assert len(frames) == 3
        assert len(risk_notes) == 3
        assert len(guidance) == 3
        assert any("3 shares already held" in frame.risk_notes for frame in frames)
        assert any("Do not scale up" in frame.position_size_guidance for frame in frames)
        assert any("15.00%" in frame.position_size_guidance for frame in frames)

    def test_buy_with_positive_news_produces_causal_supportive_scenario(
        self,
        authenticated_client,
        portfolio,
        asset,
    ):
        headline = f"{asset.display_symbol} raises guidance after earnings beat"
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, headline, "0.80")

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

        bull_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bull")
        bear_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bear")

        assert response.data["verdict"] == "approve"
        assert bull_frame["direction"] == "supportive"
        assert headline in bull_frame["risk_notes"]
        assert "supports the BUY" in bull_frame["risk_notes"]
        assert bear_frame["direction"] == "adverse"

    def test_sell_with_negative_news_produces_causal_supportive_scenario(
        self,
        authenticated_client,
        portfolio,
        asset,
    ):
        headline = f"{asset.display_symbol} cuts outlook after earnings miss"
        make_quote(asset)
        make_ohlcv(asset, [104, 102, 100, 98, 96])
        make_indicators(asset, positive=False)
        make_news(asset, headline, "-0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "SELL",
                "quantity": 2,
            },
            format="json",
        )

        bear_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bear")
        bull_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bull")

        assert response.data["verdict"] == "approve"
        assert bear_frame["direction"] == "supportive"
        assert headline in bear_frame["risk_notes"]
        assert "supports the SELL" in bear_frame["risk_notes"]
        assert bull_frame["direction"] == "adverse"

    def test_sell_with_asset_bullish_news_renders_as_adverse_to_sell(
        self,
        authenticated_client,
        portfolio,
        asset,
    ):
        headline = f"{asset.display_symbol} raises guidance after earnings beat"
        make_quote(asset)
        make_ohlcv(asset, [96, 98, 100, 102, 104])
        make_indicators(asset, positive=True)
        make_news(asset, headline, "0.80")

        response = authenticated_client.post(
            "/api/ai/strategy-validation/",
            {
                "portfolio_id": str(portfolio.id),
                "asset_id": str(asset.id),
                "action": "SELL",
                "quantity": 2,
            },
            format="json",
        )

        bull_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bull")
        bear_frame = next(frame for frame in response.data["scenario_frames"] if frame["scenario_case"] == "bear")

        assert response.data["verdict"] == "reject"
        assert bull_frame["direction"] == "adverse"
        assert headline in bull_frame["risk_notes"]
        assert "works against the SELL" in bull_frame["risk_notes"]
        assert bear_frame["direction"] == "supportive"

    def test_no_news_fallback_is_honest_but_not_repetitive(
        self,
        authenticated_client,
        portfolio,
        asset,
    ):
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

        risk_notes = [frame["risk_notes"] for frame in response.data["scenario_frames"]]

        assert response.data["verdict"] == "defer"
        assert any("No stored headline" in note for note in risk_notes)
        assert any("no stored bullish headline" in note.lower() for note in risk_notes)
        assert any("no stored bearish headline" in note.lower() for note in risk_notes)
        assert len(set(risk_notes)) == 3


class TestScenarioFrameValidation:
    def valid_frames(self):
        return [
            {
                "scenario_case": "base",
                "direction": "conditional",
                "catalysts": [{"source": "technical_inputs", "text": "Technical vote: positive"}],
                "invalidating_conditions": [{"source": "context_inputs", "text": "Context turns negative"}],
                "confidence_band": "medium",
                "risk_notes": "Risk uses stored candidate facts.",
                "position_size_guidance": "Advisory only.",
            }
        ]

    def test_accepts_supported_frame(self):
        assert validate_scenario_frame_payloads(self.valid_frames())[0]["scenario_case"] == "base"

    def test_rejects_invalid_case(self):
        frames = self.valid_frames()
        frames[0]["scenario_case"] = "upside"

        with pytest.raises(ValueError, match="invalid case"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_invalid_confidence_band(self):
        frames = self.valid_frames()
        frames[0]["confidence_band"] = "certain"

        with pytest.raises(ValueError, match="invalid confidence"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_unsupported_catalyst(self):
        frames = self.valid_frames()
        frames[0]["catalysts"] = [{"source": "outside_news", "text": "Unstored market fact"}]

        with pytest.raises(ValueError, match="unsupported catalysts"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_missing_risk_fields(self):
        frames = self.valid_frames()
        frames[0]["risk_notes"] = ""

        with pytest.raises(ValueError, match="risk notes"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_scenario_cap_violation(self):
        frames = self.valid_frames() * 4

        with pytest.raises(ValueError, match="cap"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_new_trade_idea(self):
        frames = self.valid_frames()
        frames[0]["proposed_action"] = "BUY"

        with pytest.raises(ValueError, match="new trade idea"):
            validate_scenario_frame_payloads(frames)

    def test_rejects_generic_ai_output_when_context_exists(self):
        frames = self.valid_frames()
        frames[0]["risk_notes"] = "Recent context supports the trade idea, but risk is still meaningful."

        with pytest.raises(ValueError, match="generic risk notes"):
            validate_scenario_frame_payloads(
                frames,
                context_texts=["ACME raises guidance after earnings beat"],
            )

    def test_rejects_malformed_ai_output_without_stored_news_text(self):
        frames = self.valid_frames()
        frames[0]["risk_notes"] = "The setup looks better, but the exact catalyst is not clear."

        with pytest.raises(ValueError, match="stored context"):
            validate_scenario_frame_payloads(
                frames,
                context_texts=["ACME raises guidance after earnings beat"],
            )

    def test_parses_fenced_json_response(self):
        frames = _parse_scenario_response('```json\n[{"scenario_case":"base","direction":"conditional"}]\n```')

        assert frames[0]["scenario_case"] == "base"

    def test_normalizes_recoverable_ai_frame_metadata(self):
        recommendation = type("Recommendation", (), {"action": "SELL", "candidate": {}, "context_inputs": {}})()
        frames = [
            {
                "scenario_case": "bull",
                "direction": "SELL",
                "catalysts": {"source": "google_news_rss", "text": "ACME recovery continues"},
                "invalidating_conditions": {"source": "google_news_rss", "text": "ACME recovery fails"},
                "confidence_band": "low",
                "risk_notes": "ACME raises guidance after earnings beat, which would make selling less attractive.",
            }
        ]

        normalized = _normalize_ai_scenario_payloads(frames, recommendation, "Keep the submitted quantity capped.")

        assert normalized[0]["direction"] == "adverse"
        assert normalized[0]["catalysts"][0]["source"] == "context_inputs"
        assert normalized[0]["invalidating_conditions"][0]["source"] == "context_inputs"
        assert normalized[0]["position_size_guidance"] == "Keep the submitted quantity capped."

    def test_repairs_recoverable_ai_risk_notes_with_stored_headline(self):
        recommendation = type(
            "Recommendation",
            (),
            {
                "action": "SELL",
                "candidate": {"asset_symbol": "PETR4"},
                "context_inputs": {
                    "items": [
                        {
                            "headline": "PETR4 falls as oil prices retreat",
                            "bucket": "symbol",
                            "asset_symbol": "PETR4",
                            "sentiment_score": "-0.70",
                        }
                    ]
                },
            },
        )()
        frames = [
            {
                "scenario_case": "bear",
                "direction": "SELL",
                "catalysts": [{"source": "context_inputs", "text": "Petrobras pressure continues"}],
                "invalidating_conditions": [{"source": "context_inputs", "text": "Oil rebounds"}],
                "confidence_band": "medium",
                "risk_notes": "Negative sentiment trajectory supports the trade.",
                "position_size_guidance": "Keep the submitted quantity capped.",
            }
        ]

        normalized = _normalize_ai_scenario_payloads(frames, recommendation, "Keep the submitted quantity capped.")

        assert normalized[0]["risk_notes"] == (
            "PETR4 falls as oil prices retreat. That asset-negative path supports the submitted SELL trade. "
            "Keep the trade conditional unless price action confirms this scenario."
        )

    def test_repairs_bull_and_bear_with_case_specific_direct_news(self):
        recommendation = type(
            "Recommendation",
            (),
            {
                "action": "BUY",
                "candidate": {"asset_symbol": "AAPL"},
                "context_inputs": {
                    "items": [
                        {
                            "headline": "Apple announces record buyback",
                            "bucket": "symbol",
                            "asset_symbol": "AAPL",
                            "sentiment_score": "0.80",
                        },
                        {
                            "headline": "Apple faces antitrust lawsuit",
                            "bucket": "company",
                            "asset_symbol": "AAPL",
                            "sentiment_score": "-0.70",
                        },
                    ]
                },
            },
        )()
        frames = [
            {
                "scenario_case": "bull",
                "direction": "BUY",
                "catalysts": [{"source": "context_inputs", "text": "Buyback supports upside"}],
                "invalidating_conditions": [{"source": "context_inputs", "text": "Lawsuit worsens"}],
                "confidence_band": "medium",
                "risk_notes": "Positive context supports the trade.",
                "position_size_guidance": "Keep the submitted quantity capped.",
            },
            {
                "scenario_case": "bear",
                "direction": "BUY",
                "catalysts": [{"source": "context_inputs", "text": "Lawsuit creates risk"}],
                "invalidating_conditions": [{"source": "context_inputs", "text": "Buyback dominates"}],
                "confidence_band": "medium",
                "risk_notes": "Negative context weakens the trade.",
                "position_size_guidance": "Keep the submitted quantity capped.",
            },
        ]

        normalized = _normalize_ai_scenario_payloads(frames, recommendation, "Keep the submitted quantity capped.")

        assert normalized[0]["risk_notes"].startswith("Apple announces record buyback.")
        assert normalized[1]["risk_notes"].startswith("Apple faces antitrust lawsuit.")

    def test_repaired_risk_notes_do_not_use_indirect_other_symbol_news_as_direct_evidence(self):
        recommendation = type(
            "Recommendation",
            (),
            {
                "action": "BUY",
                "candidate": {"asset_symbol": "AMZN"},
                "context_inputs": {
                    "items": [
                        {
                            "headline": "Apple increases AI spending",
                            "bucket": "theme",
                            "asset_symbol": "AAPL",
                        }
                    ]
                },
            },
        )()
        frames = [
            {
                "scenario_case": "bull",
                "direction": "BUY",
                "catalysts": [{"source": "context_inputs", "text": "Apple increases AI spending"}],
                "invalidating_conditions": [{"source": "technical_inputs", "text": "AMZN loses momentum"}],
                "confidence_band": "medium",
                "risk_notes": "Recent context supports the trade.",
                "position_size_guidance": "Keep the submitted quantity capped.",
            }
        ]

        normalized = _normalize_ai_scenario_payloads(frames, recommendation, "Keep the submitted quantity capped.")

        assert "Apple" not in normalized[0]["risk_notes"]
        assert "No direct AMZN headline is available" in normalized[0]["risk_notes"]
