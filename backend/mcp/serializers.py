from rest_framework import serializers
from .models import OTP, AgentToken
from ai.serializers import AIAuthSettingsSerializer
from ai.models import AICost
from strategies.serializers import StrategyRuleSerializer, StrategyInstanceSerializer, BacktestScenarioSerializer, StrategyTradeSerializer
from trading.serializers import TradeSerializer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid')
        return super().to_internal_value(data)


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['code', 'expires_at']
        read_only_fields = ['code', 'expires_at']


class AgentTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentToken
        fields = ['id', 'name', 'origin', 'llm_provider', 'llm_model', 'created_at', 'last_used_at']
        read_only_fields = ['id', 'created_at', 'last_used_at']


class TokenExchangeSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    otp = StrictCharField(min_length=6, max_length=6)
    name = StrictCharField(max_length=255)
    origin = StrictCharField(max_length=255, required=False, allow_blank=True, default='unknown')
    llm_provider = StrictCharField(max_length=64)
    llm_model = StrictCharField(max_length=128)


class AISettingsReadOnlySerializer(serializers.Serializer):
    """Read-only AI settings and budget info for agents."""
    provider_name = serializers.CharField()
    monthly_budget_usd = serializers.CharField()
    alert_threshold_pct = serializers.IntegerField()
    task_models = serializers.JSONField()
    has_api_key = serializers.BooleanField()
    total_cost_month_usd = serializers.CharField()
    usage_percent = serializers.IntegerField()
    remaining_budget_usd = serializers.CharField()


class BacktestCreateSerializer(serializers.Serializer):
    """Serializer for creating a backtest."""
    strategy_instance_id = serializers.UUIDField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class EvidenceMutationSerializer(serializers.Serializer):
    news_item_id = serializers.UUIDField()
    reason = serializers.CharField()

    def validate(self, attrs):
        if "original_value" in self.initial_data:
            raise serializers.ValidationError({"original_value": "This value is captured from the source artifact."})
        return attrs


class FactCorrectionCreateSerializer(EvidenceMutationSerializer):
    fact_key = serializers.CharField(max_length=100)
    corrected_value = serializers.CharField()
    correction_state = serializers.ChoiceField(choices=["corrected", "disputed", "stale"])


class ArtifactReviewCreateSerializer(EvidenceMutationSerializer):
    artifact_review_state = serializers.ChoiceField(choices=["accepted", "disputed", "stale"])


class SourceStanceCreateSerializer(serializers.Serializer):
    source_id = serializers.IntegerField()
    stance = serializers.ChoiceField(choices=["trusted", "untrusted"], required=False)
    clear = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs["clear"] == ("stance" in attrs):
            raise serializers.ValidationError("Provide either stance or clear.")
        return attrs


class EvidenceRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    source_artifact_type = serializers.CharField(read_only=True)
    source_artifact_id = serializers.UUIDField(read_only=True)
    source = serializers.IntegerField(source="source_id", read_only=True)
    fact_key = serializers.CharField(read_only=True, required=False)
    original_value = serializers.CharField(read_only=True, required=False)
    corrected_value = serializers.CharField(read_only=True, required=False)
    correction_state = serializers.CharField(read_only=True, required=False)
    artifact_review_state = serializers.CharField(read_only=True, required=False)
    stance = serializers.CharField(read_only=True, required=False)
    reason = serializers.CharField(read_only=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    superseded_at = serializers.DateTimeField(read_only=True)
    created_by_agent = serializers.SerializerMethodField()

    def get_created_by_agent(self, obj):
        if not obj.created_by_agent_id:
            return None
        return {
            "id": obj.created_by_agent_id,
            "name": obj.created_by_agent.name,
            "origin": obj.created_by_agent.origin,
        }
