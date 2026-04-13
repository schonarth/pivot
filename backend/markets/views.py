from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Asset, AssetQuote, MarketConfig, OHLCV, TechnicalIndicators
from .serializers import (
    AssetQuoteSerializer,
    AssetSerializer,
    MarketConfigSerializer,
    OHLCVSerializer,
    TechnicalIndicatorsSerializer,
)
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

    @action(detail=True, methods=["get"], url_path="ohlcv")
    def ohlcv(self, request, pk=None):
        asset = self.get_object()
        days = request.query_params.get("days", "90")
        try:
            days = int(days)
        except ValueError:
            days = 90

        from django.utils import timezone
        from datetime import timedelta

        start_date = timezone.now().date() - timedelta(days=days)
        ohlcv_data = OHLCV.objects.filter(asset=asset, date__gte=start_date).order_by("date")

        serializer = OHLCVSerializer(ohlcv_data, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="indicators")
    def indicators(self, request, pk=None):
        asset = self.get_object()
        days = request.query_params.get("days", "90")
        try:
            days = int(days)
        except ValueError:
            days = 90

        from django.utils import timezone
        from datetime import timedelta
        import pandas as pd
        import logging

        logger = logging.getLogger("paper_trader.markets")

        try:
            import pandas_ta as ta
        except ImportError:
            return Response(
                {"error": {"code": "missing_dependency", "message": "pandas-ta not installed"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        start_date = timezone.now().date() - timedelta(days=days)

        # Get all OHLCV data for the asset (need full history for indicator calculation)
        all_ohlcv = OHLCV.objects.filter(asset=asset).order_by("date").values(
            "date", "open", "high", "low", "close", "volume"
        )

        if not all_ohlcv:
            return Response([])

        ohlcv_list = list(all_ohlcv)
        if len(ohlcv_list) < 20:  # Minimum for MA 20
            return Response([])

        df = pd.DataFrame(ohlcv_list)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.astype({
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,
        })

        try:
            # Calculate full indicator series
            rsi = ta.rsi(df["close"], length=14)
            macd_result = ta.macd(df["close"], fast=12, slow=26, signal=9)
            ma_20 = ta.sma(df["close"], length=20)
            ma_50 = ta.sma(df["close"], length=50)
            ma_200 = ta.sma(df["close"], length=200)
            bb = ta.bbands(df["close"], length=20, std=2)
            volume_20d_avg = df["volume"].rolling(window=20).mean()

            # Filter to requested date range and build result
            result = []
            for idx_pos in range(len(df)):
                idx = df.index[idx_pos]
                if idx.date() < start_date:
                    continue
                result.append({
                    "date": idx.date(),
                    "rsi_14": float(rsi.iloc[idx_pos]) if pd.notna(rsi.iloc[idx_pos]) else None,
                    "macd": float(macd_result.iloc[idx_pos, 0]) if pd.notna(macd_result.iloc[idx_pos, 0]) else None,
                    "macd_signal": float(macd_result.iloc[idx_pos, 1]) if pd.notna(macd_result.iloc[idx_pos, 1]) else None,
                    "macd_histogram": float(macd_result.iloc[idx_pos, 2]) if pd.notna(macd_result.iloc[idx_pos, 2]) else None,
                    "ma_20": float(ma_20.iloc[idx_pos]) if pd.notna(ma_20.iloc[idx_pos]) else None,
                    "ma_50": float(ma_50.iloc[idx_pos]) if pd.notna(ma_50.iloc[idx_pos]) else None,
                    "ma_200": float(ma_200.iloc[idx_pos]) if pd.notna(ma_200.iloc[idx_pos]) else None,
                    "bb_upper": float(bb.iloc[idx_pos, 0]) if pd.notna(bb.iloc[idx_pos, 0]) else None,
                    "bb_middle": float(bb.iloc[idx_pos, 1]) if pd.notna(bb.iloc[idx_pos, 1]) else None,
                    "bb_lower": float(bb.iloc[idx_pos, 2]) if pd.notna(bb.iloc[idx_pos, 2]) else None,
                    "volume_20d_avg": int(volume_20d_avg.iloc[idx_pos]) if pd.notna(volume_20d_avg.iloc[idx_pos]) else None,
                })

            return Response(result)
        except Exception:
            logger.exception(f"Failed to calculate indicators for asset {asset.id}")
            return Response(
                {"error": {"code": "calculation_error", "message": "Failed to calculate indicators"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MarketStatusView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from .services import MARKET_CONFIGS

        statuses = {}
        for code in MARKET_CONFIGS:
            statuses[code] = {"open": is_market_open(code)}
        return Response(statuses)