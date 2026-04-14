import uuid
from django.db import models
from django.contrib.auth.models import User
from portfolios.models import Portfolio


RULE_TYPES = [
    ("rsi_oversold", "RSI Oversold/Overbought"),
    ("ma_crossover", "Moving Average Crossover"),
    ("macd_crossover", "MACD Crossover"),
    ("bb_bands", "Bollinger Bands"),
    ("combination", "Combination (AND)"),
]


class StrategyRule(models.Model):
    """Predefined strategy rules that users can enable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    description = models.TextField()
    conditions = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "strategy_rules"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class StrategyInstance(models.Model):
    """User's enabled strategy for a portfolio."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="strategies")
    rule = models.ForeignKey(StrategyRule, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    backtest_approved_at = models.DateTimeField(null=True, blank=True)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "strategy_instances"
        unique_together = [("portfolio", "rule")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.portfolio.name} - {self.rule.name}"


class BacktestScenario(models.Model):
    """A backtest run for a strategy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_instance = models.ForeignKey(StrategyInstance, on_delete=models.CASCADE, related_name="backtest_scenarios")
    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ], default="pending")
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "backtest_scenarios"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Backtest {self.strategy_instance.rule.name} ({self.date_from} to {self.date_to})"


class StrategyTrade(models.Model):
    """Trades executed by strategy (auto or live)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_instance = models.ForeignKey(StrategyInstance, on_delete=models.CASCADE, related_name="trades")
    asset_id = models.UUIDField()
    action = models.CharField(max_length=10, choices=[("BUY", "Buy"), ("SELL", "Sell")])
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    price = models.DecimalField(max_digits=20, decimal_places=4)
    executed_at = models.DateTimeField()
    auto_executed = models.BooleanField(default=False)
    matched_conditions = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "strategy_trades"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.action} {self.quantity} @ {self.price}"
