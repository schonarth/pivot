import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from accounts.models import User


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at and not self.used_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save()

    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mcp_otps'
        indexes = [
            models.Index(fields=['user', 'code']),
        ]


class AgentToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_tokens')
    token = models.CharField(max_length=255, unique=True, editable=False)
    name = models.CharField(max_length=255)
    origin = models.CharField(max_length=255, help_text='Agent origin/identifier')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mcp_agent_tokens'
        unique_together = ['user', 'origin']
