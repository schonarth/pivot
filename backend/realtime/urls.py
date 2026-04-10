from django.urls import path
from .views import health_check, system_stats

urlpatterns = [
    path("health", health_check, name="health-check"),
    path("system/stats", system_stats, name="system-stats"),
]