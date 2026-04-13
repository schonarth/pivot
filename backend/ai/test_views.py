import pytest
from decimal import Decimal

from ai.models import AIAuth, AICost


@pytest.mark.django_db
class TestAISettingsEndpoints:
    def test_get_settings_returns_default_configuration(self, authenticated_client, user):
        response = authenticated_client.get("/api/ai/get_settings/")

        assert response.status_code == 200
        assert response.data["provider_name"] == "openai"
        assert response.data["monthly_budget_usd"] == "10.00"
        assert response.data["has_api_key"] is False
        assert "available_tasks" in response.data

        ai_auth = AIAuth.objects.get(user=user)
        assert ai_auth.provider_name == "openai"

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
