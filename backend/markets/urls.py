from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, MarketConfigViewSet, MarketStatusView, OhlcvBackfillView, OhlcvRepairView

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"markets", MarketConfigViewSet, basename="market-config")

urlpatterns = [
    path("markets/status/", MarketStatusView.as_view({"get": "list"}), name="market-status"),
    path("markets/ohlcv-backfill/", OhlcvBackfillView.as_view(), name="ohlcv-backfill"),
    path("markets/ohlcv-repair/", OhlcvRepairView.as_view(), name="ohlcv-repair"),
    path("", include(router.urls)),
]
