from rest_framework import serializers
from .models import Alert, AlertTrigger


class TriggerTradeSerializer(serializers.Serializer):
    action = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=20, decimal_places=4)
    gross_value = serializers.DecimalField(max_digits=20, decimal_places=2)
    fees = serializers.DecimalField(max_digits=20, decimal_places=2)
    net_cash_impact = serializers.DecimalField(max_digits=20, decimal_places=2)


class AlertTriggerSummarySerializer(serializers.ModelSerializer):
    trade = TriggerTradeSerializer(read_only=True)

    class Meta:
        model = AlertTrigger
        fields = ("id", "triggered_price", "triggered_at", "outcome", "notification_sent", "price_was_override", "trade")


class AlertSerializer(serializers.ModelSerializer):
    asset_display_symbol = serializers.CharField(source="asset.display_symbol", read_only=True)
    latest_trigger = serializers.SerializerMethodField()

    def get_latest_trigger(self, obj):
        trigger = obj.triggers.select_related("trade").first()
        if trigger is None:
            return None
        return AlertTriggerSummarySerializer(trigger).data

    class Meta:
        model = Alert
        fields = (
            "id",
            "portfolio",
            "asset",
            "asset_display_symbol",
            "condition_type",
            "threshold",
            "notify_enabled",
            "auto_trade_enabled",
            "auto_trade_side",
            "auto_trade_quantity",
            "auto_trade_pct",
            "status",
            "last_evaluated_at",
            "triggered_at",
            "latest_trigger",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "last_evaluated_at", "triggered_at", "created_at", "updated_at")


class AlertCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    condition_type = serializers.ChoiceField(choices=["price_above", "price_below"])
    threshold = serializers.DecimalField(max_digits=20, decimal_places=4)
    notify_enabled = serializers.BooleanField(default=True)
    auto_trade_enabled = serializers.BooleanField(default=False)
    auto_trade_side = serializers.ChoiceField(choices=["BUY", "SELL"], required=False, allow_null=True)
    auto_trade_quantity = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    auto_trade_pct = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    def validate(self, data):
        if not data.get("notify_enabled") and not data.get("auto_trade_enabled"):
            raise serializers.ValidationError("At least one of notify_enabled or auto_trade_enabled must be true.")

        if data.get("auto_trade_enabled"):
            if not data.get("auto_trade_side"):
                raise serializers.ValidationError("auto_trade_side is required when auto_trade_enabled is true.")
            has_quantity = data.get("auto_trade_quantity") is not None
            has_pct = data.get("auto_trade_pct") is not None
            if not has_quantity and not has_pct:
                raise serializers.ValidationError("Either auto_trade_quantity or auto_trade_pct must be set when auto_trade_enabled is true.")
            if has_quantity and has_pct:
                raise serializers.ValidationError("Only one of auto_trade_quantity or auto_trade_pct can be set, not both.")
        else:
            data["auto_trade_side"] = None
            data["auto_trade_quantity"] = None
            data["auto_trade_pct"] = None

        return data


class AlertTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertTrigger
        fields = ("id", "alert", "triggered_price", "triggered_at", "outcome", "details", "notification_sent", "price_was_override", "trade")
