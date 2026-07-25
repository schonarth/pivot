from rest_framework import serializers

from .models import (
    PROVIDER_CHOICES,
    TASK_MODELS,
    AIAuth,
    AIInstanceKey,
    ArtifactReview,
    FactCorrection,
    SourceStance,
    StrategyRecommendation,
    StrategyScenarioFrame,
)
from .services import EvidenceReviewService


class FactCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactCorrection
        fields = (
            "id",
            "source_artifact_type",
            "source_artifact_id",
            "source",
            "fact_key",
            "original_value",
            "corrected_value",
            "correction_state",
            "reason",
            "created_at",
            "superseded_at",
        )
        read_only_fields = ("original_value", "created_at", "superseded_at")


class ArtifactReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtifactReview
        fields = (
            "id",
            "source_artifact_type",
            "source_artifact_id",
            "source",
            "artifact_review_state",
            "reason",
            "created_at",
            "superseded_at",
        )


class SourceStanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceStance
        fields = ("id", "source", "stance", "created_at", "superseded_at")


class FactCorrectionRequestSerializer(serializers.Serializer):
    news_item_id = serializers.UUIDField()
    fact_key = serializers.CharField(max_length=100)
    corrected_value = serializers.CharField()
    correction_state = serializers.ChoiceField(choices=("corrected", "disputed", "stale"))
    reason = serializers.CharField()


class ArtifactReviewRequestSerializer(serializers.Serializer):
    news_item_id = serializers.UUIDField()
    artifact_review_state = serializers.ChoiceField(choices=("accepted", "disputed", "stale"))
    reason = serializers.CharField()


class SourceStanceRequestSerializer(serializers.Serializer):
    source_id = serializers.IntegerField()
    stance = serializers.ChoiceField(choices=("trusted", "untrusted"))


class AIAuthSettingsSerializer(serializers.ModelSerializer):
    """Serializer for AI auth settings (no API key exposed)."""

    has_api_key = serializers.SerializerMethodField()
    available_providers = serializers.SerializerMethodField()
    available_models = serializers.SerializerMethodField()
    available_tasks = serializers.SerializerMethodField()
    instance_default_enabled = serializers.SerializerMethodField()
    instance_default_allow_other_users = serializers.SerializerMethodField()
    instance_default_owned_by_current_user = serializers.SerializerMethodField()
    instance_default_owner_username = serializers.SerializerMethodField()
    can_use_instance_default = serializers.SerializerMethodField()

    class Meta:
        model = AIAuth
        fields = (
            "provider_name",
            "enabled",
            "monthly_budget_usd",
            "alert_threshold_pct",
            "task_models",
            "has_api_key",
            "available_providers",
            "available_models",
            "available_tasks",
            "instance_default_enabled",
            "instance_default_allow_other_users",
            "instance_default_owned_by_current_user",
            "instance_default_owner_username",
            "can_use_instance_default",
        )
        read_only_fields = ("available_providers", "available_models", "available_tasks")

    def get_has_api_key(self, obj) -> bool:
        return obj.api_key_encrypted is not None

    def get_available_providers(self, obj) -> list:
        return [{"value": choice[0], "label": choice[1]} for choice in PROVIDER_CHOICES]

    def get_available_models(self, obj) -> dict:
        return {
            provider: models
            for provider, models in {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "anthropic": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
                "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
            }.items()
        }

    def get_available_tasks(self, obj) -> dict:
        return TASK_MODELS

    def _get_instance_default_key(self) -> AIInstanceKey | None:
        if not hasattr(self, "_instance_default_key"):
            self._instance_default_key = AIInstanceKey.objects.select_related("owner").filter(pk=1).first()
        return self._instance_default_key

    def get_instance_default_enabled(self, obj) -> bool:
        instance_key = self._get_instance_default_key()
        return bool(instance_key and instance_key.api_key_encrypted)

    def get_instance_default_allow_other_users(self, obj) -> bool:
        instance_key = self._get_instance_default_key()
        return bool(instance_key and instance_key.allow_other_users)

    def get_instance_default_owned_by_current_user(self, obj) -> bool:
        instance_key = self._get_instance_default_key()
        return bool(instance_key and instance_key.owner_id == obj.user_id)

    def get_instance_default_owner_username(self, obj) -> str | None:
        instance_key = self._get_instance_default_key()
        if not instance_key or not instance_key.owner:
            return None
        return instance_key.owner.username

    def get_can_use_instance_default(self, obj) -> bool:
        instance_key = self._get_instance_default_key()
        if not instance_key or not instance_key.api_key_encrypted:
            return False
        return bool(instance_key.allow_other_users or instance_key.owner_id == obj.user_id)


class AIBudgetSerializer(serializers.Serializer):
    """Serializer for AI budget info (for header/display)."""

    enabled = serializers.BooleanField()
    monthly_budget_usd = serializers.CharField()
    usage_usd = serializers.CharField()
    remaining_usd = serializers.CharField()
    percentage_used = serializers.CharField()
    at_limit = serializers.BooleanField()
    should_warn = serializers.BooleanField()


class StrategyValidationRequestSerializer(serializers.Serializer):
    portfolio_id = serializers.UUIDField()
    asset_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=["BUY", "SELL"])
    quantity = serializers.IntegerField(min_value=1)
    rationale = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_action(self, value):
        return value.upper()


class StrategyScenarioFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyScenarioFrame
        fields = (
            "id",
            "scenario_case",
            "direction",
            "catalysts",
            "invalidating_conditions",
            "confidence_band",
            "risk_notes",
            "position_size_guidance",
            "generated_at",
        )


class StrategyRecommendationSerializer(serializers.ModelSerializer):
    asset_display_symbol = serializers.CharField(source="asset.display_symbol", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    scenario_frames = StrategyScenarioFrameSerializer(many=True, read_only=True)
    evidence = serializers.SerializerMethodField()
    is_invalidated = serializers.SerializerMethodField()
    latest_invalidation = serializers.SerializerMethodField()

    class Meta:
        model = StrategyRecommendation
        fields = (
            "id",
            "candidate_id",
            "portfolio",
            "asset",
            "asset_display_symbol",
            "asset_name",
            "action",
            "quantity",
            "candidate",
            "technical_inputs",
            "context_inputs",
            "sentiment_trajectory_inputs",
            "divergence_inputs",
            "verdict",
            "rationale",
            "scenario_frames",
            "evidence",
            "is_invalidated",
            "latest_invalidation",
            "recorded_at",
        )

    def get_evidence(self, obj):
        return EvidenceReviewService(obj.user).evidence_for_recommendation(obj)

    def get_is_invalidated(self, obj):
        return self._latest_invalidation(obj) is not None

    def get_latest_invalidation(self, obj):
        invalidation = self._latest_invalidation(obj)
        if invalidation is None:
            return None
        trigger = invalidation.fact_correction or invalidation.artifact_review
        return {
            "trigger_type": "fact_correction" if invalidation.fact_correction_id else "artifact_review",
            "trigger_record_id": str(trigger.id),
            "reason": trigger.reason,
            "created_at": invalidation.created_at,
        }

    @staticmethod
    def _latest_invalidation(obj):
        prefetched = getattr(obj, "_latest_invalidations", None)
        if prefetched is not None:
            return prefetched[0] if prefetched else None
        return obj.invalidations.select_related("fact_correction", "artifact_review").first()
