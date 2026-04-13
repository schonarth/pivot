from decimal import Decimal

from rest_framework import serializers
from .models import CashTransaction, Portfolio, PortfolioSnapshot


class PortfolioSerializer(serializers.ModelSerializer):
    base_currency = serializers.CharField(read_only=True)

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "name",
            "market",
            "base_currency",
            "initial_capital",
            "current_cash",
            "is_primary",
            "is_simulating",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "base_currency", "current_cash", "created_at", "updated_at")


class CreatePortfolioSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    market = serializers.ChoiceField(choices=["BR", "US", "UK", "EU"])
    initial_capital = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=Decimal("0"))


class DepositWithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=Decimal("0.01"))


class CashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashTransaction
        fields = ("id", "transaction_type", "amount", "resulting_cash", "created_at")
        read_only_fields = ("id", "resulting_cash", "created_at")


class PortfolioSummarySerializer(serializers.Serializer):
    portfolio_id = serializers.UUIDField()
    name = serializers.CharField()
    market = serializers.CharField()
    base_currency = serializers.CharField()
    initial_capital = serializers.CharField()
    current_cash = serializers.CharField()
    positions_value = serializers.CharField()
    total_equity = serializers.CharField()
    net_external_cash_flows = serializers.CharField()
    trading_pnl = serializers.CharField()
    positions = serializers.ListField()


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioSnapshot
        fields = ("id", "cash", "positions_value", "total_equity", "net_external_cash_flows", "captured_at")