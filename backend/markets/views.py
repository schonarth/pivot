from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Asset, AssetQuote, MarketConfig
from .serializers import AssetQuoteSerializer, AssetSerializer, MarketConfigSerializer
from .services import is_market_open, seed_market_configs


class MarketConfigViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MarketConfigSerializer
    queryset = MarketConfig.objects.all()


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AssetSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Asset.objects.all()
        market = self.request.query_params.get("market")
        q = self.request.query_params.get("q")
        if market:
            queryset = queryset.filter(market=market)
        if q:
            queryset = queryset.filter(Q(display_symbol__icontains=q) | Q(name__icontains=q))
        return queryset.order_by("market", "display_symbol")

    @action(detail=True, methods=["get"], url_path="price")
    def price(self, request, pk=None):
        asset = self.get_object()
        quote = AssetQuote.objects.filter(asset=asset).order_by("-fetched_at").first()
        if quote is None:
            return Response(
                {"error": {"code": "no_quote", "message": "No quote available for this asset."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AssetQuoteSerializer(quote)
        data = serializer.data
        data["market_open"] = is_market_open(asset.market)
        return Response(data)

    @action(detail=True, methods=["post"], url_path="refresh-price")
    def refresh_price(self, request, pk=None):
        asset = self.get_object()
        from .quote_provider import refresh_asset_quote

        try:
            result = refresh_asset_quote(str(asset.id))
        except Exception:
            result = None
        if result is None:
            quote = AssetQuote.objects.filter(asset=asset).order_by("-fetched_at").first()
            if quote is None:
                return Response(
                    {"error": {"code": "no_quote", "message": "No quote available."}},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = AssetQuoteSerializer(quote)
            data = serializer.data
            data["stale"] = True
        else:
            data = AssetQuoteSerializer(result).data
        data["market_open"] = is_market_open(asset.market)
        return Response(data)


class MarketStatusView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from .services import MARKET_CONFIGS

        statuses = {}
        for code in MARKET_CONFIGS:
            statuses[code] = {"open": is_market_open(code)}
        return Response(statuses)