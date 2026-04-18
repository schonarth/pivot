from decimal import Decimal
import pytest

from ai.models import AIAuth, AICost
from ai.services import AIService


@pytest.mark.django_db
class TestAISettingsEndpoints:
    def test_get_settings_returns_default_configuration(self, authenticated_client, user):
        response = authenticated_client.get("/api/ai/get_settings/")

        assert response.status_code == 200
        assert response.data["provider_name"] == "openai"
        assert response.data["monthly_budget_usd"] == "10.00"
        assert response.data["has_api_key"] is False
        assert "available_tasks" in response.data
        assert response.data["instance_default_enabled"] is False
        assert response.data["instance_default_allow_other_users"] is False
        assert response.data["instance_default_owned_by_current_user"] is False
        assert response.data["can_use_instance_default"] is False

        ai_auth = AIAuth.objects.get(user=user)
        assert ai_auth.provider_name == "openai"

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

    def test_set_api_key_rejects_instance_default_updates_for_inheritors(self, user, user2):
        owner_service = AIService(user)
        owner_service.set_api_key("owner-key")
        owner_service.set_instance_default_api_key("instance-key", allow_other_users=True)

        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient

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
