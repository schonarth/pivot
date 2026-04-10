from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PositionViewSet, TradeDetailView, TradeViewSet

router = DefaultRouter()

urlpatterns = [
    path("portfolios/<uuid:portfolio_pk>/positions/", PositionViewSet.as_view({"get": "list"}), name="position-list"),
    path("portfolios/<uuid:portfolio_pk>/positions/<uuid:asset_id>/", PositionViewSet.as_view({"get": "retrieve"}), name="position-detail"),
    path("portfolios/<uuid:portfolio_pk>/trades/", TradeViewSet.as_view({"get": "list", "post": "create"}), name="trade-list"),
    path("trades/<uuid:pk>/", TradeDetailView.as_view({"get": "retrieve"}), name="trade-detail"),
]