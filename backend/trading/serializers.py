from decimal import Decimal

from rest_framework import serializers
from .models import Position, Trade


class PositionSerializer(serializers.ModelSerializer):
    asset_display_symbol = serializers.CharField(source="asset.display_symbol", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    asset_market = serializers.CharField(source="asset.market", read_only=True)
    asset_currency = serializers.CharField(source="asset.currency", read_only=True)

    class Meta:
        model = Position
        fields = (
            "id",
            "portfolio",
            "asset",
            "asset_display_symbol",
            "asset_name",
            "asset_market",
            "asset_currency",
            "quantity",
            "average_cost",
            "created_at",
            "updated_at",
        )


class PositionDetailSerializer(PositionSerializer):
    current_price = serializers.SerializerMethodField()
    current_price_as_of = serializers.SerializerMethodField()
    unrealized_pnl_amount = serializers.SerializerMethodField()
    unrealized_pnl_pct = serializers.SerializerMethodField()

    def get_current_price(self, obj):
        from markets.quote_provider import get_latest_quote

        quote = get_latest_quote(str(obj.asset_id))
        return str(quote.price) if quote else str(obj.average_cost)

    def get_current_price_as_of(self, obj):
        from markets.quote_provider import get_latest_quote

        quote = get_latest_quote(str(obj.asset_id))
        return quote.fetched_at.isoformat() if quote else None

    def get_unrealized_pnl_amount(self, obj):
        from decimal import Decimal

        from markets.quote_provider import get_latest_quote

        quote = get_latest_quote(str(obj.asset_id))
        current_price = quote.price if quote else obj.average_cost
        return str(Decimal(str(obj.quantity)) * current_price - Decimal(str(obj.quantity)) * obj.average_cost)

    def get_unrealized_pnl_pct(self, obj):
        from decimal import Decimal

        from markets.quote_provider import get_latest_quote

        quote = get_latest_quote(str(obj.asset_id))
        current_price = quote.price if quote else obj.average_cost
        if obj.average_cost == 0:
            return "0"
        return str((current_price - obj.average_cost) / obj.average_cost)

    class Meta(PositionSerializer.Meta):
        fields = PositionSerializer.Meta.fields + (
            "current_price",
            "current_price_as_of",
            "unrealized_pnl_amount",
            "unrealized_pnl_pct",
        )


class TradeSerializer(serializers.ModelSerializer):
    asset_display_symbol = serializers.CharField(source="asset.display_symbol", read_only=True)

    class Meta:
        model = Trade
        fields = (
            "id",
            "portfolio",
            "asset",
            "asset_display_symbol",
            "action",
            "quantity",
            "price",
            "gross_value",
            "fees",
            "net_cash_impact",
            "realized_pnl",
            "rationale",
            "executed_by",
            "executed_at",
        )


class TradeCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    rationale = serializers.CharField(max_length=255, required=False, default="Manual operation")

    def validate_action(self, value):
        return value.upper()