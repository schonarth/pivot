from rest_framework import serializers
from .models import AIAuth


class AIAuthSettingsSerializer(serializers.Serializer):
    """Serializer for AI auth settings (no API key exposed)."""
    provider_name = serializers.CharField(read_only=True)
    monthly_budget_usd = serializers.DecimalField(max_digits=8, decimal_places=2)
    alert_threshold_pct = serializers.IntegerField()
    has_api_key = serializers.SerializerMethodField()

    def get_has_api_key(self, obj) -> bool:
        return obj.api_key_encrypted is not None


class AIBudgetSerializer(serializers.Serializer):
    """Serializer for AI budget info (for header/display)."""
    enabled = serializers.BooleanField()
    monthly_budget_usd = serializers.CharField()
    usage_usd = serializers.CharField()
    remaining_usd = serializers.CharField()
    percentage_used = serializers.CharField()
    at_limit = serializers.BooleanField()
    should_warn = serializers.BooleanField()
