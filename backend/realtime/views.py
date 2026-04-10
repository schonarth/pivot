from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.db import connection
from django.core.cache import cache


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    checks = {}
    try:
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        cache.set("health_check", "1", 1)
        checks["redis"] = "ok" if cache.get("health_check") == "1" else "error"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    status_code = 200 if all(v == "ok" for v in checks.values()) else 503
    return Response(checks, status=status_code)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def system_stats(request):
    from portfolios.models import Portfolio
    from trading.models import Trade
    from alerts.models import Alert
    from markets.models import Asset, AssetQuote

    stats = {
        "users": 0,
        "portfolios": Portfolio.objects.count(),
        "trades": Trade.objects.count(),
        "alerts_active": Alert.objects.filter(status="active").count(),
        "assets": Asset.objects.count(),
        "quotes": AssetQuote.objects.count(),
    }
    return Response(stats)