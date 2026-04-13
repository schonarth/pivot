from rest_framework.routers import DefaultRouter
from .views import AISettingsViewSet

router = DefaultRouter()
router.register(r"ai", AISettingsViewSet, basename="ai-settings")

urlpatterns = router.urls
