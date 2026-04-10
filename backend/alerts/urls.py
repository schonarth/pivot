from django.urls import path
from .views import AlertTriggerListView, AlertViewSet

urlpatterns = [
    path("portfolios/<uuid:portfolio_pk>/alerts/", AlertViewSet.as_view({"get": "list", "post": "create"}), name="alert-list"),
    path("alerts/<uuid:pk>/", AlertViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="alert-detail"),
    path("alerts/<uuid:pk>/pause/", AlertViewSet.as_view({"post": "pause"}), name="alert-pause"),
    path("alerts/<uuid:pk>/resume/", AlertViewSet.as_view({"post": "resume"}), name="alert-resume"),
    path("alert-triggers/", AlertTriggerListView.as_view({"get": "list"}), name="alert-trigger-list"),
]