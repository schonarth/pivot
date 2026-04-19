from datetime import date

from django.db.models import Avg, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .backfill_progress import get_backfill_status, queue_ohlcv_backfill
from .repair_progress import get_repair_status, queue_ohlcv_repair
from .models import Asset, AssetQuote, MarketConfig, NewsItem, OHLCV
from .serializers import (
    AssetQuoteSerializer,
    AssetSerializer,
    MarketConfigSerializer,
    OHLCVSerializer,
)
from .services import NewsService, is_market_open
from .services import search_asset_symbols


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

    @action(detail=False, methods=["post"], url_path="lookup-symbol")
    def lookup_symbol(self, request):
        symbol = str(request.data.get("symbol") or "").strip()
        market = str(request.data.get("market") or "").strip().upper() or None
        if not symbol:
            return Response(
                {"error": {"code": "invalid_symbol", "message": "Symbol is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if market and not MarketConfig.objects.filter(code=market).exists():
            return Response(
                {"error": {"code": "invalid_market", "message": "Invalid market."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assets = search_asset_symbols(symbol, market=market)
        if not assets:
            return Response(
                {"error": {"code": "not_found", "message": "Symbol not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

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

        from datetime import timedelta
        from django.utils import timezone

        start_date = timezone.now().date() - timedelta(days=days)
        ohlcv_data = OHLCV.objects.filter(asset=asset, date__gte=start_date).order_by("date")

        serializer = OHLCVSerializer(ohlcv_data, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="news")
    def news(self, request, pk=None):
        asset = self.get_object()
        limit = request.query_params.get("limit", "10")
        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        NewsService.fetch_and_store_news(asset)

        news_queryset = NewsItem.objects.filter(asset=asset).order_by("-published_at", "-fetched_at")
        news_items = news_queryset[:limit]
        avg_sentiment = news_queryset.filter(sentiment_score__isnull=False).aggregate(Avg("sentiment_score"))

        return Response({
            "asset_id": str(asset.id),
            "symbol": asset.display_symbol,
            "average_sentiment": (
                float(avg_sentiment["sentiment_score__avg"])
                if avg_sentiment["sentiment_score__avg"]
                else None
            ),
            "news_items": [
                {
                    "headline": item.headline,
                    "summary": item.summary,
                    "url": item.url,
                    "source": item.source,
                    "sentiment_score": float(item.sentiment_score) if item.sentiment_score else None,
                    "published_at": item.published_at,
                    "fetched_at": item.fetched_at,
                }
                for item in news_items
            ],
        })

    @action(detail=True, methods=["get"], url_path="indicators")
    def indicators(self, request, pk=None):
        asset = self.get_object()
        days = request.query_params.get("days", "90")
        try:
            days = int(days)
        except ValueError:
            days = 90

        import logging
        from datetime import timedelta

        import pandas as pd
        from django.utils import timezone

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
            def series_value(series, index):
                if series is None:
                    return None
                value = series.iloc[index]
                return float(value) if pd.notna(value) else None

            def frame_value(frame, row_index, col_index):
                if frame is None:
                    return None
                value = frame.iloc[row_index, col_index]
                return float(value) if pd.notna(value) else None

            for idx_pos in range(len(df)):
                idx = df.index[idx_pos]
                if idx.date() < start_date:
                    continue
                result.append({
                    "date": idx.date(),
                    "rsi_14": series_value(rsi, idx_pos),
                    "macd": frame_value(macd_result, idx_pos, 0),
                    "macd_signal": frame_value(macd_result, idx_pos, 1),
                    "macd_histogram": frame_value(macd_result, idx_pos, 2),
                    "ma_20": series_value(ma_20, idx_pos),
                    "ma_50": series_value(ma_50, idx_pos),
                    "ma_200": series_value(ma_200, idx_pos),
                    "bb_upper": frame_value(bb, idx_pos, 2),
                    "bb_middle": frame_value(bb, idx_pos, 1),
                    "bb_lower": frame_value(bb, idx_pos, 0),
                    "volume_20d_avg": (
                        int(volume_20d_avg.iloc[idx_pos])
                        if pd.notna(volume_20d_avg.iloc[idx_pos])
                        else None
                    ),
                })

            return Response(result)
        except Exception:
            logger.exception(f"Failed to calculate indicators for asset {asset.id}")
            return Response(
                {"error": {"code": "calculation_error", "message": "Failed to calculate indicators"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="ai-insight")
    def ai_insight(self, request, pk=None):
        asset = self.get_object()

        from ai.services import AIBudgetError, AIService

        service = AIService(request.user)
        try:
            insight = service.analyze_asset(asset)
        except AIBudgetError as exc:
            return Response(
                {"error": {"code": "budget_exceeded", "message": str(exc)}},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "ai_unavailable", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": {"code": "ai_error", "message": "Failed to generate AI insight"}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(insight)


class MarketStatusView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        from rest_framework.response import Response

        from .services import MARKET_CONFIGS

        statuses = {}
        for code in MARKET_CONFIGS:
            status = is_market_open(code)
            statuses[code] = {"open": status if status is not None else False}
        return Response(statuses)


class OhlcvBackfillView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_backfill_status())

    def post(self, request):
        queued, status_data = queue_ohlcv_backfill(
            source="manual",
            initiated_by=str(request.user.id),
        )
        status_data["queued"] = queued
        return Response(status_data, status=status.HTTP_202_ACCEPTED if queued else status.HTTP_200_OK)


class OhlcvRepairView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_repair_status())

    def post(self, request):
        symbol = request.data.get("symbol")
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")
        try:
            if date_from:
                date.fromisoformat(date_from)
            if date_to:
                date.fromisoformat(date_to)
        except ValueError:
            return Response(
                {"error": {"code": "invalid_date", "message": "Dates must use YYYY-MM-DD format."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queued, status_data = queue_ohlcv_repair(
            source="manual",
            initiated_by=str(request.user.id),
            symbol=symbol or None,
            date_from=date_from or None,
            date_to=date_to or None,
        )
        status_data["queued"] = queued
        return Response(status_data, status=status.HTTP_202_ACCEPTED if queued else status.HTTP_200_OK)
