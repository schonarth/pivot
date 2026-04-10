from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    return JsonResponse({"name": "Paper Trader API", "version": "1.0", "endpoints": {"health": "/api/health", "auth": "/api/auth/", "portfolios": "/api/portfolios/", "assets": "/api/assets/", "markets": "/api/markets/status"}})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_root),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("markets.urls")),
    path("api/", include("portfolios.urls")),
    path("api/", include("trading.urls")),
    path("api/", include("alerts.urls")),
    path("api/", include("timeline.urls")),
    path("api/", include("realtime.urls")),
]