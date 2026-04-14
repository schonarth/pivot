from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, MarketConfigViewSet, MarketStatusView

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"markets", MarketConfigViewSet, basename="market-config")

urlpatterns = [
    path("markets/status/", MarketStatusView.as_view({"get": "list"}), name="market-status"),
    path("", include(router.urls)),
]