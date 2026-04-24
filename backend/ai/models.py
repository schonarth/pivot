import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


PROVIDER_CHOICES = [
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("google", "Google"),
]

TASK_MODELS = {
    "sentiment_analysis": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-opus-4-6",
        "google": "gemini-2.0-flash",
    },
    "asset_filtering": {
        "openai": "gpt-4o",
        "anthropic": "claude-opus-4-6",
        "google": "gemini-2.0-flash",
    },
    "indicator_insight": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-haiku-4-5-20251001",
        "google": "gemini-2.0-flash",
    },
    "trade_validation": {
        "openai": "gpt-4o",
        "anthropic": "claude-opus-4-6",
        "google": "gemini-2.0-flash",
    },
    "opportunity_discovery": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-haiku-4-5-20251001",
        "google": "gemini-2.0-flash",
    },
}


class AIAuth(models.Model):
    """Store encrypted API keys and usage budgets for AI providers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_auth")
    provider_name = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="openai")
    enabled = models.BooleanField(default=True)

    api_key_encrypted = models.BinaryField(null=True, blank=True)

    monthly_budget_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text="Monthly budget in USD for AI calls"
    )
    alert_threshold_pct = models.IntegerField(
        default=10,
        help_text="Warn when this % of budget remains (e.g., 10 = warn at 90% consumed)"
    )

    task_models = models.JSONField(
        default=dict,
        blank=True,
        help_text="Task-specific model overrides: {task_type: model_name}"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_auth"

    def __str__(self):
        return f"{self.user.username} - {self.provider_name}"

    def get_model_for_task(self, task_type: str) -> str:
        """Get the model to use for a specific task type."""
        if task_type in self.task_models:
            return self.task_models[task_type]
        if task_type in TASK_MODELS and self.provider_name in TASK_MODELS[task_type]:
            return TASK_MODELS[task_type][self.provider_name]
        return TASK_MODELS.get(task_type, {}).get(self.provider_name, "gpt-4o-mini")


class AIInstanceKey(models.Model):
    id = models.SmallIntegerField(primary_key=True, default=1, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    provider_name = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="openai")
    api_key_encrypted = models.BinaryField(null=True, blank=True)
    allow_other_users = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_instance_keys"

    def __str__(self):
        return f"Instance default AI key ({self.provider_name})"


class AICost(models.Model):
    """Track each AI API call and its cost."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ai_auth = models.ForeignKey(AIAuth, on_delete=models.CASCADE, related_name="costs")

    model_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6)

    task_type = models.CharField(
        max_length=50,
        help_text="Type of task (e.g., 'asset_filtering', 'indicator_insight', 'trade_validation')"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_costs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ai_auth", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.ai_auth.user.username} - {self.model_name} ({self.cost_usd})"


class StrategyRecommendation(models.Model):
    VERDICT_CHOICES = [
        ("approve", "Approve"),
        ("reject", "Reject"),
        ("defer", "Defer"),
    ]
    ACTION_CHOICES = [("BUY", "Buy"), ("SELL", "Sell")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="strategy_recommendations",
    )
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="strategy_recommendations",
    )
    asset = models.ForeignKey("markets.Asset", on_delete=models.CASCADE, related_name="strategy_recommendations")
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField()
    candidate = models.JSONField()
    technical_inputs = models.JSONField()
    context_inputs = models.JSONField()
    sentiment_trajectory_inputs = models.JSONField()
    divergence_inputs = models.JSONField(null=True, blank=True)
    verdict = models.CharField(max_length=10, choices=VERDICT_CHOICES)
    rationale = models.TextField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "strategy_recommendations"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["user", "-recorded_at"]),
            models.Index(fields=["portfolio", "-recorded_at"]),
            models.Index(fields=["asset", "-recorded_at"]),
        ]
