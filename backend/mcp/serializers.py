from rest_framework import serializers
from .models import OTP, AgentToken
from ai.serializers import AIAuthSettingsSerializer
from ai.models import AICost
from strategies.serializers import StrategyRuleSerializer, StrategyInstanceSerializer, BacktestScenarioSerializer, StrategyTradeSerializer
from trading.serializers import TradeSerializer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


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
