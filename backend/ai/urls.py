from rest_framework.routers import DefaultRouter
from .views import AISettingsViewSet, OpportunityDiscoveryViewSet

router = DefaultRouter()
router.register(r"ai", AISettingsViewSet, basename="ai-settings")
router.register(r"ai/discovery", OpportunityDiscoveryViewSet, basename="opportunity-discovery")

urlpatterns = router.urls
