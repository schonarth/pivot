import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Alert(models.Model):
    CONDITION_CHOICES = [("price_above", "Price Above"), ("price_below", "Price Below")]
    STATUS_CHOICES = [("active", "Active"), ("triggered", "Triggered"), ("paused", "Paused")]
    SIDE_CHOICES = [("BUY", "Buy"), ("SELL", "Sell")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE, related_name="alerts")
    asset = models.ForeignKey("markets.Asset", on_delete=models.CASCADE, related_name="alerts")
    condition_type = models.CharField(max_length=12, choices=CONDITION_CHOICES)
    threshold = models.DecimalField(max_digits=20, decimal_places=4)
    notify_enabled = models.BooleanField(default=True)
    auto_trade_enabled = models.BooleanField(default=False)
    auto_trade_side = models.CharField(max_length=4, choices=SIDE_CHOICES, null=True, blank=True)
    auto_trade_quantity = models.PositiveIntegerField(null=True, blank=True)
    auto_trade_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["portfolio", "status"]),
            models.Index(fields=["asset", "status"]),
        ]


class AlertTrigger(models.Model):
    OUTCOME_CHOICES = [
        ("notification_only", "Notification Only"),
        ("notification_and_trade_executed", "Notification And Trade Executed"),
        ("notification_and_trade_skipped", "Notification And Trade Skipped"),
        ("notification_and_trade_failed", "Notification And Trade Failed"),
        ("trade_executed", "Trade Executed"),
        ("trade_skipped", "Trade Skipped"),
        ("trade_failed", "Trade Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="triggers")
    triggered_price = models.DecimalField(max_digits=20, decimal_places=4)
    triggered_at = models.DateTimeField(auto_now_add=True)
    outcome = models.CharField(max_length=35, choices=OUTCOME_CHOICES)
    details = models.JSONField(default=dict)
    notification_sent = models.BooleanField(default=False)
    price_was_override = models.BooleanField(default=False)
    trade = models.ForeignKey("trading.Trade", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "alert_triggers"
        ordering = ["-triggered_at"]