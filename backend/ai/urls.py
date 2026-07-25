from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AISettingsViewSet, EvidenceReviewViewSet, OpportunityDiscoveryViewSet

router = DefaultRouter()
router.register(r"ai", AISettingsViewSet, basename="ai-settings")
router.register(r"ai/discovery", OpportunityDiscoveryViewSet, basename="opportunity-discovery")

urlpatterns = [
    path(
        "ai/strategy-recommendations/<uuid:recommendation_id>/evidence/",
        EvidenceReviewViewSet.as_view({"get": "recommendation_evidence"}),
    ),
    path("ai/evidence/news-items/<uuid:news_item_id>/", EvidenceReviewViewSet.as_view({"get": "news_item_evidence"})),
    path("ai/fact-key-suggestions/", EvidenceReviewViewSet.as_view({"get": "fact_key_suggestions"})),
    path("ai/evidence/corrections/", EvidenceReviewViewSet.as_view({"post": "create_correction"})),
    path(
        "ai/evidence/artifact-reviews/",
        EvidenceReviewViewSet.as_view({"post": "create_artifact_review"}),
    ),
    path("ai/evidence/source-stances/", EvidenceReviewViewSet.as_view({"post": "create_source_stance"})),
    path(
        "ai/evidence/source-stances/<int:source_id>/",
        EvidenceReviewViewSet.as_view({"delete": "clear_source_stance"}),
    ),
] + router.urls
