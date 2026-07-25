from django.conf import settings
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from markets.models import NewsItem, NewsSource

from .discovery import OpportunityDiscoveryService
from .models import AIAuth, ArtifactReview, FactCorrection, RecommendationInvalidation, StrategyRecommendation
from .serializers import (
    AIAuthSettingsSerializer,
    AIBudgetSerializer,
    ArtifactReviewRequestSerializer,
    ArtifactReviewSerializer,
    FactCorrectionRequestSerializer,
    FactCorrectionSerializer,
    SourceStanceRequestSerializer,
    SourceStanceSerializer,
    StrategyRecommendationSerializer,
    StrategyValidationRequestSerializer,
)
from .services import AIService, EvidenceReviewService
from .strategy_validation import StrategyValidationService


class AISettingsViewSet(viewsets.ViewSet):
    """Manage AI settings and API key configuration."""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def budget(self, request):
        """Get current AI budget and usage info."""
        service = AIService(request.user)
        budget_info = service.get_budget_info()
        serializer = AIBudgetSerializer(budget_info)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_settings(self, request):
        """Get current AI settings."""
        ai_auth, created = AIAuth.objects.get_or_create(user=request.user)
        serializer = AIAuthSettingsSerializer(ai_auth)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_settings(self, request):
        """Update AI settings (budget, provider, threshold, task models)."""
        ai_auth, created = AIAuth.objects.get_or_create(user=request.user)

        if "monthly_budget_usd" in request.data:
            ai_auth.monthly_budget_usd = request.data["monthly_budget_usd"]

        if "alert_threshold_pct" in request.data:
            ai_auth.alert_threshold_pct = request.data["alert_threshold_pct"]

        if "provider_name" in request.data:
            ai_auth.provider_name = request.data["provider_name"]

        if "enabled" in request.data:
            ai_auth.enabled = request.data["enabled"]

        if "task_models" in request.data:
            ai_auth.task_models = request.data["task_models"]

        ai_auth.save()
        serializer = AIAuthSettingsSerializer(ai_auth)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def set_api_key(self, request):
        """Store encrypted API key."""
        api_key = request.data.get("api_key")
        use_as_instance_default = bool(request.data.get("use_as_instance_default"))
        allow_other_users = bool(request.data.get("allow_other_users"))
        if not api_key:
            return Response(
                {"error": "api_key is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = AIService(request.user)
        provider_name = request.data.get("provider_name") or service.ai_auth.provider_name
        if use_as_instance_default:
            instance_default_key = AIService.get_instance_default_key()
            if instance_default_key and instance_default_key.owner_id not in (None, request.user.id):
                return Response(
                    {"error": "instance default key is managed by another user"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service.ai_auth.provider_name = provider_name
        service.ai_auth.save(update_fields=["provider_name"])
        service.set_api_key(api_key)
        if use_as_instance_default:
            service.set_instance_default_api_key(
                api_key,
                provider_name=provider_name,
                allow_other_users=allow_other_users,
            )
        else:
            service.clear_instance_default_api_key_if_owned()

        return Response(
            {"status": "API key updated"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def remove_api_key(self, request):
        """Remove stored API key."""
        service = AIService(request.user)
        service.clear_api_key()
        service.clear_instance_default_api_key_if_owned()

        return Response(
            {"status": "API key removed"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def test_connection(self, request):
        provider = request.data.get("provider_name")
        api_key = request.data.get("api_key")
        service = AIService(request.user)

        if not service.has_ai_enabled():
            return Response(
                {"error": "AI features are disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not provider:
            ai_auth = AIAuth.objects.filter(user=request.user).first()
            provider = ai_auth.provider_name if ai_auth else "openai"

        if not api_key:
            api_key = service.get_api_key()

        if not api_key:
            return Response(
                {"error": "api_key is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = AIService.test_connection(provider=provider, api_key=api_key)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "ok", **result},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="strategy-validation")
    def strategy_validation(self, request):
        serializer = StrategyValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = StrategyValidationService(request.user)
        try:
            recommendation = service.validate(**serializer.validated_data)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_candidate", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(StrategyRecommendationSerializer(recommendation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="strategy-recommendations")
    def strategy_recommendations(self, request):
        queryset = (
            StrategyRecommendation.objects.filter(user=request.user)
            .select_related("asset", "portfolio")
            .prefetch_related("scenario_frames")
            .prefetch_related(
                Prefetch(
                    "invalidations",
                    queryset=(
                        RecommendationInvalidation.objects.select_related("fact_correction", "artifact_review")
                        .order_by("-created_at")
                    ),
                    to_attr="_latest_invalidations",
                )
            )
        )
        portfolio_id = request.query_params.get("portfolio_id")
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        return Response(StrategyRecommendationSerializer(queryset[:20], many=True).data)


class OpportunityDiscoveryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        market = request.query_params.get("market")
        refine = str(request.query_params.get("refine", "")).lower() in {"1", "true", "yes"}
        refresh = str(request.query_params.get("refresh", "")).lower() in {"1", "true", "yes"}

        service = OpportunityDiscoveryService(request.user)
        try:
            result = service.discover(market, refine=refine, force_refresh=refresh)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_market", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result)


class EvidenceReviewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def recommendation_evidence(self, request, recommendation_id):
        recommendation = get_object_or_404(
            StrategyRecommendation.objects.select_related("asset"), id=recommendation_id, user=request.user
        )
        service = EvidenceReviewService(request.user)
        eligible_source_count = NewsSource.objects.filter(
            Q(market=recommendation.asset.market) | Q(market__isnull=True) | Q(market="")
        ).count()
        override_enabled = settings.DEBUG and request.query_params.get("enable_source_stance_controls") == "true"
        evidence = service.evidence_for_recommendation(recommendation)
        news_items = {
            str(item.id): item
            for item in NewsItem.objects.filter(
                id__in=[item["news_item_id"] for item in evidence]
            ).select_related("news_source")
        }
        for item in evidence:
            news_item = news_items.get(item["news_item_id"])
            if news_item is None:
                continue
            active_stance = service.active_source_stance(news_item.news_source)
            item.update(
                original_value=news_item.headline,
                source_id=str(news_item.news_source_id),
                source_name=news_item.news_source.institution_name,
                source_stance=active_stance.stance if active_stance else None,
                eligible_source_count=eligible_source_count,
                source_stance_controls_enabled=eligible_source_count >= 2 or override_enabled,
            )
        return Response({"evidence": evidence, "fact_key_suggestions": service.fact_key_suggestions()})

    def fact_key_suggestions(self, request):
        return Response(EvidenceReviewService(request.user).fact_key_suggestions())

    def news_item_evidence(self, request, news_item_id):
        news_item = self._scoped_news_item(request.user, news_item_id)
        service = EvidenceReviewService(request.user)
        treatment = service.treatment_for_news_item(news_item)
        corrections = FactCorrection.objects.filter(
            operator=request.user, source_artifact_type="news_item", source_artifact_id=news_item.id
        ).order_by("-created_at")
        reviews = ArtifactReview.objects.filter(
            operator=request.user, source_artifact_type="news_item", source_artifact_id=news_item.id
        ).order_by("-created_at")
        eligible_source_count = NewsSource.objects.filter(
            Q(market=news_item.asset.market) | Q(market__isnull=True) | Q(market="")
        ).count()
        active_stance = service.active_source_stance(news_item.news_source)
        return Response({
            "evidence": [{
                "news_item_id": str(news_item.id), "excerpt": news_item.headline, "original_value": news_item.headline,
                "source_id": str(news_item.news_source_id), "source_name": news_item.news_source.institution_name,
                "source_stance": active_stance.stance if active_stance else None,
                "eligible_source_count": eligible_source_count,
                "source_stance_controls_enabled": eligible_source_count >= 2,
                "current_treatment": treatment,
                "correction_history": FactCorrectionSerializer(corrections, many=True).data,
                "artifact_review_history": ArtifactReviewSerializer(reviews, many=True).data,
                "categorical_uncertainty": treatment["state"] if treatment["state"] in {"disputed", "stale"} else None,
            }],
            "fact_key_suggestions": service.fact_key_suggestions(),
        })

    def create_correction(self, request):
        serializer = FactCorrectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        news_item = self._scoped_news_item(request.user, serializer.validated_data["news_item_id"])
        try:
            correction = EvidenceReviewService(request.user).create_fact_correction(
                news_item=news_item,
                fact_key=serializer.validated_data["fact_key"],
                corrected_value=serializer.validated_data["corrected_value"],
                correction_state=serializer.validated_data["correction_state"],
                reason=serializer.validated_data["reason"],
            )
        except ValueError as exc:
            return Response({"fact_key": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FactCorrectionSerializer(correction).data, status=status.HTTP_201_CREATED)

    def create_artifact_review(self, request):
        serializer = ArtifactReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        news_item = self._scoped_news_item(request.user, serializer.validated_data["news_item_id"])
        review = EvidenceReviewService(request.user).set_artifact_review(
            news_item,
            serializer.validated_data["artifact_review_state"],
            serializer.validated_data["reason"],
        )
        return Response(ArtifactReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    def create_source_stance(self, request):
        serializer = SourceStanceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = self._scoped_source(request.user, serializer.validated_data["source_id"])
        stance = EvidenceReviewService(request.user).set_source_stance(source, serializer.validated_data["stance"])
        return Response(SourceStanceSerializer(stance).data, status=status.HTTP_201_CREATED)

    def clear_source_stance(self, request, source_id):
        source = self._scoped_source(request.user, source_id)
        EvidenceReviewService(request.user).clear_source_stance(source)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _scoped_news_item(user, news_item_id):
        news_item = EvidenceReviewService(user).scoped_news_item(news_item_id)
        if news_item is None:
            raise Http404
        return news_item

    @staticmethod
    def _scoped_source(user, source_id):
        source = EvidenceReviewService(user).scoped_source(source_id)
        if source is None:
            raise Http404
        return source
