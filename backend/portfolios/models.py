import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from .services import derive_currency


class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios")
    name = models.CharField(max_length=100)
    market = models.CharField(max_length=5)
    base_currency = models.CharField(max_length=3, editable=False)
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    current_cash = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    is_primary = models.BooleanField(default=False)
    is_simulating = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolios"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.base_currency:
            self.base_currency = derive_currency(self.market)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.market})"


class CashTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("initial_funding", "Initial Funding"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
    ]
    INITIATED_BY_CHOICES = [("user", "User"), ("agent", "Agent")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="cash_transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    resulting_cash = models.DecimalField(max_digits=20, decimal_places=2)
    initiated_by = models.CharField(max_length=10, choices=INITIATED_BY_CHOICES, default="user")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cash_transactions"
        ordering = ["-created_at"]


class PortfolioSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="snapshots")
    cash = models.DecimalField(max_digits=20, decimal_places=2)
    positions_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    total_equity = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    net_external_cash_flows = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0"))
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_snapshots"
        ordering = ["-captured_at"]


class PortfolioGuardrails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.OneToOneField(Portfolio, on_delete=models.CASCADE, related_name="guardrails")
    max_trades_per_day = models.IntegerField(default=10, help_text="Maximum trades allowed per day")
    max_position_size_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("20"),
        help_text="Max position size as % of portfolio"
    )
    stop_loss_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("-5"),
        help_text="Stop loss threshold as % change from entry"
    )
    take_profit_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("10"),
        help_text="Take profit threshold as % change from entry"
    )
    min_order_value = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal("10"),
        help_text="Minimum order value in portfolio currency"
    )
    enabled = models.BooleanField(default=False, help_text="Enable guardrails enforcement")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio_guardrails"

    def __str__(self):
        return f"Guardrails for {self.portfolio.name}"


class PortfolioWatchMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="watch_memberships")
    asset = models.ForeignKey("markets.Asset", on_delete=models.CASCADE, related_name="portfolio_watch_memberships")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_watch_memberships"
        ordering = ["-created_at"]
        unique_together = [("portfolio", "asset")]
        indexes = [
            models.Index(fields=["portfolio"]),
        ]

    def __str__(self):
        return f"{self.portfolio.name} watch -> {self.asset.display_symbol}"
