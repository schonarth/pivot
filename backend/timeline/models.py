import uuid

from django.conf import settings
from django.db import models


class TimelineEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("trade", "Trade"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("alert_triggered", "Alert Triggered"),
        ("alert_notification", "Alert Notification"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey("portfolios.Portfolio", on_delete=models.CASCADE, related_name="timeline_events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "timeline_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["portfolio", "-created_at"]),
        ]