from rest_framework import serializers
from .models import AIAuth, PROVIDER_CHOICES, TASK_MODELS


class AIAuthSettingsSerializer(serializers.ModelSerializer):
    """Serializer for AI auth settings (no API key exposed)."""
    has_api_key = serializers.SerializerMethodField()
    available_providers = serializers.SerializerMethodField()
    available_models = serializers.SerializerMethodField()
    available_tasks = serializers.SerializerMethodField()

    class Meta:
        model = AIAuth
        fields = (
            "provider_name",
            "monthly_budget_usd",
            "alert_threshold_pct",
            "task_models",
            "has_api_key",
            "available_providers",
            "available_models",
            "available_tasks",
        )
        read_only_fields = ("available_providers", "available_models", "available_tasks")

    def get_has_api_key(self, obj) -> bool:
        return obj.api_key_encrypted is not None

    def get_available_providers(self, obj) -> list:
        return [{"value": choice[0], "label": choice[1]} for choice in PROVIDER_CHOICES]

    def get_available_models(self, obj) -> dict:
        return {
            provider: models
            for provider, models in {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "anthropic": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
                "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
            }.items()
        }

    def get_available_tasks(self, obj) -> dict:
        return TASK_MODELS


class AIBudgetSerializer(serializers.Serializer):
    """Serializer for AI budget info (for header/display)."""
    enabled = serializers.BooleanField()
    monthly_budget_usd = serializers.CharField()
    usage_usd = serializers.CharField()
    remaining_usd = serializers.CharField()
    percentage_used = serializers.CharField()
    at_limit = serializers.BooleanField()
    should_warn = serializers.BooleanField()
