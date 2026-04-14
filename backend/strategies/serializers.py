from rest_framework import serializers
from .models import StrategyRule, StrategyInstance, BacktestScenario, StrategyTrade


class StrategyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyRule
        fields = ["id", "name", "rule_type", "description", "conditions"]


class StrategyInstanceSerializer(serializers.ModelSerializer):
    rule = StrategyRuleSerializer(read_only=True)
    rule_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = StrategyInstance
        fields = ["id", "portfolio_id", "rule", "rule_id", "enabled", "backtest_approved_at", "settings", "created_at"]
        read_only_fields = ["backtest_approved_at", "created_at"]


class BacktestScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestScenario
        fields = ["id", "strategy_instance_id", "date_from", "date_to", "status", "result", "error_message", "created_at", "completed_at"]
        read_only_fields = ["status", "result", "error_message", "created_at", "completed_at"]


class StrategyTradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyTrade
        fields = ["id", "strategy_instance_id", "asset_id", "action", "quantity", "price", "executed_at", "auto_executed", "matched_conditions"]
