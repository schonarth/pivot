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
        max_digits=8, decimal_places=2, default=Decimal("10.00"), help_text="Monthly budget in USD for AI calls"
    )
    alert_threshold_pct = models.IntegerField(
        default=10, help_text="Warn when this % of budget remains (e.g., 10 = warn at 90% consumed)"
    )

    task_models = models.JSONField(
        default=dict, blank=True, help_text="Task-specific model overrides: {task_type: model_name}"
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
        max_length=50, help_text="Type of task (e.g., 'asset_filtering', 'indicator_insight', 'trade_validation')"
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
            models.Index(fields=["user", "-recorded_at"], name="strategy_re_user_id_369586_idx"),
            models.Index(fields=["portfolio", "-recorded_at"], name="strategy_re_portfol_a7c5f2_idx"),
            models.Index(fields=["asset", "-recorded_at"], name="strategy_re_asset_i_83688c_idx"),
        ]


class StrategyScenarioFrame(models.Model):
    SCENARIO_CASE_CHOICES = [
        ("base", "Base"),
        ("bull", "Bull"),
        ("bear", "Bear"),
    ]
    CONFIDENCE_BAND_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(
        StrategyRecommendation,
        on_delete=models.CASCADE,
        related_name="scenario_frames",
    )
    scenario_case = models.CharField(max_length=10, choices=SCENARIO_CASE_CHOICES)
    direction = models.CharField(max_length=32)
    catalysts = models.JSONField()
    invalidating_conditions = models.JSONField()
    confidence_band = models.CharField(max_length=10, choices=CONFIDENCE_BAND_CHOICES)
    risk_notes = models.TextField()
    position_size_guidance = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "strategy_scenario_frames"
        ordering = ["generated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["recommendation", "scenario_case"],
                name="unique_strategy_scenario_case_per_recommendation",
            ),
        ]
        indexes = [
            models.Index(fields=["recommendation", "scenario_case"], name="strategy_sc_recomme_68964d_idx"),
        ]


class RecommendationInvalidation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(
        StrategyRecommendation,
        on_delete=models.CASCADE,
        related_name="invalidations",
    )
    fact_correction = models.ForeignKey(
        "FactCorrection",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recommendation_invalidations",
    )
    artifact_review = models.ForeignKey(
        "ArtifactReview",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recommendation_invalidations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_invalidations"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(("fact_correction__isnull", False), ("artifact_review__isnull", True))
                    | models.Q(("fact_correction__isnull", True), ("artifact_review__isnull", False))
                ),
                name="recommendationinvalidation_single_trigger",
            ),
            models.UniqueConstraint(
                fields=["recommendation", "fact_correction"],
                name="unique_recommendation_fact_invalidation",
            ),
            models.UniqueConstraint(
                fields=["recommendation", "artifact_review"],
                name="unique_recommendation_review_invalidation",
            ),
        ]
        indexes = [
            models.Index(fields=["recommendation", "-created_at"], name="rec_inv_rec_created_idx"),
        ]


class FactCorrection(models.Model):
    CORRECTION_STATE_CHOICES = [
        ("corrected", "Corrected"),
        ("disputed", "Disputed"),
        ("stale", "Stale"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fact_corrections")
    source_artifact_type = models.CharField(max_length=50, default="news_item")
    source_artifact_id = models.UUIDField()
    source = models.ForeignKey("markets.NewsSource", on_delete=models.PROTECT, related_name="fact_corrections")
    fact_key = models.CharField(max_length=100)
    original_value = models.TextField(editable=False)
    corrected_value = models.TextField()
    correction_state = models.CharField(max_length=10, choices=CORRECTION_STATE_CHOICES)
    reason = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_fact_corrections"
    )
    created_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="created_fact_corrections"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    superseded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_fact_corrections",
    )
    superseded_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="superseded_fact_corrections"
    )

    class Meta:
        db_table = "fact_corrections"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(correction_state__in=["corrected", "disputed", "stale"]),
                name="factcorrection_valid_state",
            ),
        ]
        indexes = [
            models.Index(fields=["operator", "source_artifact_id", "fact_key"], name="factcor_op_factkey_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            original_value = type(self).objects.filter(pk=self.pk).values_list("original_value", flat=True).first()
            if original_value is not None and self.original_value != original_value:
                raise ValueError("original_value is immutable")
        super().save(*args, **kwargs)


class ArtifactReview(models.Model):
    ARTIFACT_REVIEW_STATE_CHOICES = [
        ("accepted", "Accepted"),
        ("disputed", "Disputed"),
        ("stale", "Stale"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="artifact_reviews")
    source_artifact_type = models.CharField(max_length=50, default="news_item")
    source_artifact_id = models.UUIDField()
    source = models.ForeignKey("markets.NewsSource", on_delete=models.PROTECT, related_name="artifact_reviews")
    artifact_review_state = models.CharField(max_length=10, choices=ARTIFACT_REVIEW_STATE_CHOICES)
    reason = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_artifact_reviews"
    )
    created_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="created_artifact_reviews"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    superseded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_artifact_reviews",
    )
    superseded_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="superseded_artifact_reviews"
    )

    class Meta:
        db_table = "artifact_reviews"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(artifact_review_state__in=["accepted", "disputed", "stale"]),
                name="artifactreview_valid_state",
            ),
        ]
        indexes = [
            models.Index(fields=["operator", "source_artifact_id"], name="artifact_op_artifact_idx"),
        ]


class SourceStance(models.Model):
    SOURCE_STANCE_CHOICES = [
        ("trusted", "Trusted"),
        ("untrusted", "Untrusted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey("markets.NewsSource", on_delete=models.PROTECT, related_name="source_stances")
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="source_stances")
    stance = models.CharField(max_length=10, choices=SOURCE_STANCE_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_source_stances"
    )
    created_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="created_source_stances"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    superseded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_source_stances",
    )
    superseded_by_agent = models.ForeignKey(
        "mcp.AgentToken", on_delete=models.PROTECT, null=True, blank=True, related_name="superseded_source_stances"
    )

    class Meta:
        db_table = "source_stances"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stance__in=["trusted", "untrusted"]),
                name="sourcestance_valid_stance",
            ),
        ]
        indexes = [
            models.Index(fields=["operator", "source"], name="stance_op_source_idx"),
        ]
