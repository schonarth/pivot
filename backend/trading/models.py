import uuid
from decimal import Decimal, ROUND_HALF_EVEN

from django.conf import settings
from django.db import models
from django.utils import timezone

from portfolios.services import derive_currency, get_fee_rate


class Position(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE, related_name="positions")
    asset = models.ForeignKey("markets.Asset", on_delete=models.CASCADE, related_name="positions")
    quantity = models.PositiveIntegerField()
    average_cost = models.DecimalField(max_digits=20, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "positions"
        unique_together = [("portfolio", "asset")]
        indexes = [
            models.Index(fields=["portfolio"]),
        ]


class Trade(models.Model):
    ACTION_CHOICES = [("BUY", "Buy"), ("SELL", "Sell")]
    EXECUTED_BY_CHOICES = [("manual", "Manual"), ("alert", "Alert"), ("autonomous", "Autonomous"), ("agent", "Agent")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE, related_name="trades")
    asset = models.ForeignKey("markets.Asset", on_delete=models.CASCADE, related_name="trades")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=4)
    gross_value = models.DecimalField(max_digits=20, decimal_places=2)
    fees = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    net_cash_impact = models.DecimalField(max_digits=20, decimal_places=2)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    rationale = models.CharField(max_length=255, default="Manual operation")
    executed_by = models.CharField(max_length=12, choices=EXECUTED_BY_CHOICES, default="manual")
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trades"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["portfolio", "-executed_at"]),
        ]