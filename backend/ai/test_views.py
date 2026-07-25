from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ai.models import AIAuth, AICost, StrategyRecommendation
from ai.services import AIService, EvidenceReviewService
from markets.models import NewsItem, NewsSource


@pytest.mark.django_db
class TestAISettingsEndpoints:
    def test_get_settings_returns_default_configuration(self, authenticated_client, user):
        response = authenticated_client.get("/api/ai/get_settings/")

        assert response.status_code == 200
        assert response.data["provider_name"] == "openai"
        assert response.data["enabled"] is True
        assert response.data["monthly_budget_usd"] == "10.00"
        assert response.data["has_api_key"] is False
        assert "available_tasks" in response.data
        assert response.data["instance_default_enabled"] is False
        assert response.data["instance_default_allow_other_users"] is False
        assert response.data["instance_default_owned_by_current_user"] is False
        assert response.data["can_use_instance_default"] is False

        ai_auth = AIAuth.objects.get(user=user)
        assert ai_auth.provider_name == "openai"
        assert ai_auth.enabled is True

    def test_update_settings_toggles_enabled_flag(self, authenticated_client, user):
        response = authenticated_client.post(
            "/api/ai/update_settings/",
            {"enabled": False},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["enabled"] is False

        ai_auth = AIAuth.objects.get(user=user)
        assert ai_auth.enabled is False

    def test_get_settings_reports_instance_default_state(self, authenticated_client, user):
        service = AIService(user)
        service.set_api_key("user-key")
        service.set_instance_default_api_key("instance-key", allow_other_users=True)

        response = authenticated_client.get("/api/ai/get_settings/")

        assert response.status_code == 200
        assert response.data["instance_default_enabled"] is True
        assert response.data["instance_default_allow_other_users"] is True
        assert response.data["instance_default_owned_by_current_user"] is True
        assert response.data["instance_default_owner_username"] == user.username
        assert response.data["can_use_instance_default"] is True

    def test_get_settings_fetches_instance_default_once(self, authenticated_client, user):
        service = AIService(user)
        service.set_api_key("user-key")
        service.set_instance_default_api_key("instance-key", allow_other_users=True)

        with CaptureQueriesContext(connection) as queries:
            response = authenticated_client.get("/api/ai/get_settings/")

        instance_key_queries = [query for query in queries if 'FROM "ai_instance_keys"' in query["sql"]]
        assert response.status_code == 200
        assert len(instance_key_queries) == 1

    def test_disabled_ai_blocks_credentials(self, user):
        service = AIService(user)
        service.set_api_key("user-key")

        ai_auth = AIAuth.objects.get(user=user)
        ai_auth.enabled = False
        ai_auth.save(update_fields=["enabled"])

        service = AIService(user)
        assert service.has_ai_enabled() is False
        assert service.get_api_credentials() == (None, None)

    def test_set_api_key_rejects_instance_default_updates_for_inheritors(self, user, user2):
        owner_service = AIService(user)
        owner_service.set_api_key("owner-key")
        owner_service.set_instance_default_api_key("instance-key", allow_other_users=True)

        refresh = RefreshToken.for_user(user2)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = client.post(
            "/api/ai/set_api_key/",
            {
                "api_key": "other-key",
                "provider_name": "openai",
                "use_as_instance_default": True,
                "allow_other_users": False,
            },
            format="json",
        )

        assert response.status_code == 403
        assert response.data["error"] == "instance default key is managed by another user"

    def test_budget_returns_usage_summary(self, authenticated_client, user):
        ai_auth = AIAuth.objects.create(
            user=user,
            monthly_budget_usd=Decimal("20.00"),
            alert_threshold_pct=10,
        )
        AICost.objects.create(
            ai_auth=ai_auth,
            model_name="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=Decimal("18.50"),
            task_type="indicator_insight",
        )

        response = authenticated_client.get("/api/ai/budget/")

        assert response.status_code == 200
        assert response.data["enabled"] is False
        assert response.data["monthly_budget_usd"] == "20.00"
        assert response.data["usage_usd"] == "18.500000"
        assert response.data["remaining_usd"] == "1.500000"
        assert response.data["percentage_used"] == "92"
        assert response.data["at_limit"] is False
        assert response.data["should_warn"] is True

    def test_provider_cost_estimation_is_non_zero_for_supported_non_openai_models(self):
        cost = AIService._estimate_provider_cost("anthropic", "claude-opus-4-6", 1000, 500)

        assert cost > 0


@pytest.mark.django_db
class TestStrategyRecommendationReviewEndpoint:
    def test_reports_evidence_treatment_history_uncertainty_and_latest_invalidation(
        self, authenticated_client, user, portfolio, asset
    ):
        source = NewsSource.objects.create(
            institution_name="Test Source",
            feed_url="https://example.com/feed",
        )
        news_item = NewsItem.objects.create(
            asset=asset,
            headline=f"{asset.display_symbol} raises guidance",
            url="https://example.com/article",
            source="fixture",
            news_source=source,
            published_at=timezone.now(),
        )
        recommendation = StrategyRecommendation.objects.create(
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
        EvidenceReviewService(user).create_fact_correction(
            news_item=news_item,
            fact_key="guidance",
            corrected_value="Guidance was withdrawn.",
            correction_state="disputed",
            reason="Issuer correction.",
        )

        response = authenticated_client.get("/api/ai/strategy-recommendations/")

        assert response.status_code == 200
        payload = next(item for item in response.data if item["id"] == str(recommendation.id))
        assert payload["is_invalidated"] is True
        assert payload["latest_invalidation"]["trigger_type"] == "fact_correction"
        assert payload["latest_invalidation"]["reason"] == "Issuer correction."
        assert payload["evidence"] == [
            {
                "news_item_id": str(news_item.id),
                "excerpt": news_item.headline,
                "current_treatment": {"kind": "fact_correction", "state": "disputed", "adjustment": -1},
                "correction_history": payload["evidence"][0]["correction_history"],
                "artifact_review_history": [],
                "categorical_uncertainty": "disputed",
            }
        ]
        assert payload["evidence"][0]["correction_history"][0]["original_value"] == news_item.headline


@pytest.mark.django_db
class TestEvidenceReviewEndpoints:
    def test_allows_reviewing_an_insight_headline_without_a_saved_recommendation(
        self, authenticated_client, asset
    ):
        source = NewsSource.objects.create(
            institution_name="Insight Source",
            feed_url="https://example.com/insight-feed",
            market="US",
        )
        news_item = NewsItem.objects.create(
            asset=asset,
            headline="AAA publishes an outlook update",
            url="https://example.com/insight-article",
            source="fixture",
            news_source=source,
            published_at=timezone.now(),
        )

        evidence_response = authenticated_client.get(f"/api/ai/evidence/news-items/{news_item.id}/")
        correction_response = authenticated_client.post(
            "/api/ai/evidence/corrections/",
            {
                "news_item_id": str(news_item.id),
                "fact_key": "outlook",
                "corrected_value": "Outlook was withdrawn.",
                "correction_state": "corrected",
                "reason": "Issuer update.",
            },
            format="json",
        )

        assert evidence_response.status_code == 200
        assert evidence_response.data["evidence"][0]["news_item_id"] == str(news_item.id)
        assert correction_response.status_code == 201

    def test_returns_scoped_evidence_suggestions_and_applies_review_mutations(
        self, authenticated_client, user, portfolio, asset
    ):
        source = NewsSource.objects.create(
            institution_name="Test Source",
            feed_url="https://example.com/evidence-feed",
            market="US",
        )
        news_item = NewsItem.objects.create(
            asset=asset,
            headline="AAA reports earnings result",
            url="https://example.com/evidence-article",
            source="fixture",
            news_source=source,
            published_at=timezone.now(),
        )
        recommendation = StrategyRecommendation.objects.create(
            user=user,
            portfolio=portfolio,
            asset=asset,
            action="BUY",
            quantity=1,
            candidate={},
            technical_inputs={},
            context_inputs={"items": [{"news_item_id": str(news_item.id), "headline": news_item.headline}]},
            sentiment_trajectory_inputs={},
            verdict="approve",
            rationale="Stored recommendation rationale.",
        )

        evidence_response = authenticated_client.get(
            f"/api/ai/strategy-recommendations/{recommendation.id}/evidence/"
        )

        assert evidence_response.status_code == 200
        assert evidence_response.data["fact_key_suggestions"] == []
        assert evidence_response.data["evidence"][0]["original_value"] == news_item.headline
        assert evidence_response.data["evidence"][0]["source_id"] == str(source.id)
        assert evidence_response.data["evidence"][0]["eligible_source_count"] >= 2
        assert evidence_response.data["evidence"][0]["source_stance_controls_enabled"] is True

        correction_response = authenticated_client.post(
            "/api/ai/evidence/corrections/",
            {
                "news_item_id": str(news_item.id),
                "fact_key": "Earnings Result",
                "corrected_value": "Earnings were restated.",
                "correction_state": "corrected",
                "reason": "Issuer filing.",
            },
            format="json",
        )

        assert correction_response.status_code == 201
        assert correction_response.data["fact_key"] == "earnings_result"
        assert correction_response.data["original_value"] == news_item.headline
        assert authenticated_client.get("/api/ai/fact-key-suggestions/").data == ["earnings_result"]

        review_response = authenticated_client.post(
            "/api/ai/evidence/artifact-reviews/",
            {
                "news_item_id": str(news_item.id),
                "artifact_review_state": "disputed",
                "reason": "Conflicting report.",
            },
            format="json",
        )
        stance_response = authenticated_client.post(
            "/api/ai/evidence/source-stances/",
            {"source_id": str(source.id), "stance": "untrusted"},
            format="json",
        )
        clear_response = authenticated_client.delete(f"/api/ai/evidence/source-stances/{source.id}/")

        assert review_response.status_code == 201
        assert stance_response.status_code == 201
        assert clear_response.status_code == 204
