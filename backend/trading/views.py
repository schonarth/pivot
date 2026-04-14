from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from markets.models import Asset
from portfolios.models import Portfolio
from .models import Position, Trade
from .serializers import PositionDetailSerializer, PositionSerializer, TradeCreateSerializer, TradeSerializer
from .services import execute_buy, execute_sell, check_guardrails


class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PositionDetailSerializer
    lookup_field = 'asset_id'

    def get_queryset(self):
        portfolio_id = self.kwargs.get("portfolio_pk")
        return Position.objects.filter(
            portfolio_id=portfolio_id,
            portfolio__user=self.request.user,
        ).select_related("asset")

    def retrieve(self, request, *args, **kwargs):
        position = self.get_object()
        serializer = PositionDetailSerializer(position)
        return Response(serializer.data)


class TradeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TradeSerializer

    def get_queryset(self):
        portfolio_id = self.kwargs.get("portfolio_pk")
        return Trade.objects.filter(portfolio_id=portfolio_id, portfolio__user=self.request.user).select_related("asset")

    def create(self, request, *args, **kwargs):
        portfolio_id = self.kwargs.get("portfolio_pk")
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

        input_serializer = TradeCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data
        asset = get_object_or_404(Asset, id=data["asset_id"])

        from markets.quote_provider import get_latest_quote

        quote = get_latest_quote(str(asset.id))
        if quote is None:
            from markets.quote_provider import refresh_asset_quote

            quote = refresh_asset_quote(str(asset.id))
            if quote is None:
                return Response(
                    {
                        "error": {
                            "code": "quote_error",
                            "message": f"No quote available for asset {asset.display_symbol}",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        guardrails_check = check_guardrails(portfolio, asset, data["action"], data["quantity"], quote.price)
        if not guardrails_check["valid"] and not data.get("bypass_guardrails", False):
            return Response(
                {
                    "error": {
                        "code": "guardrails_violation",
                        "message": "Trade violates portfolio guardrails",
                        "violations": guardrails_check["violations"],
                        "allow_bypass": True,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if data["action"] == "BUY":
                result = execute_buy(
                    portfolio=portfolio,
                    asset=asset,
                    quantity=data["quantity"],
                    rationale=data.get("rationale", "Manual operation"),
                    executed_by="manual",
                )
            else:
                result = execute_sell(
                    portfolio=portfolio,
                    asset=asset,
                    quantity=data["quantity"],
                    rationale=data.get("rationale", "Manual operation"),
                    executed_by="manual",
                )
        except ValueError as e:
            error_msg = str(e)
            details = e.args[1] if len(e.args) > 1 and isinstance(e.args[1], dict) else {}
            return Response(
                {
                    "error": {
                        "code": "trade_error",
                        "message": error_msg,
                        "details": {k: str(v) for k, v in details.items()},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        trade_serializer = TradeSerializer(result["trade"])
        from portfolios.services import get_portfolio_summary
        from portfolios.serializers import PortfolioSummarySerializer

        portfolio.refresh_from_db()
        summary = get_portfolio_summary(portfolio)

        response_data = {
            "trade": trade_serializer.data,
            "cash": str(portfolio.current_cash),
            "summary": summary,
        }
        if result.get("position"):
            response_data["position"] = PositionSerializer(result["position"]).data

        return Response(response_data, status=status.HTTP_201_CREATED)


class TradeDetailView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TradeSerializer

    def get_queryset(self):
        return Trade.objects.filter(portfolio__user=self.request.user).select_related("asset")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agent_execute_trade(request):
    """Execute a trade on behalf of an agent.

    Request:
    {
        "portfolio_id": "uuid",
        "asset_id": "uuid",
        "action": "BUY" | "SELL",
        "quantity": number,
        "reason": "string (optional)"
    }
    """
    portfolio_id = request.data.get("portfolio_id")
    asset_id = request.data.get("asset_id")
    action = request.data.get("action")
    quantity = request.data.get("quantity")
    reason = request.data.get("reason", "Autonomous execution")

    if not all([portfolio_id, asset_id, action, quantity]):
        return Response(
            {"error": {"code": "missing_fields", "message": "portfolio_id, asset_id, action, quantity required"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    asset = get_object_or_404(Asset, id=asset_id)

    if portfolio.market != asset.market:
        return Response(
            {"error": {"code": "market_mismatch", "message": "Portfolio and asset markets do not match"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from markets.quote_provider import get_latest_quote, refresh_asset_quote

    quote = get_latest_quote(str(asset.id))
    if quote is None:
        quote = refresh_asset_quote(str(asset.id))
        if quote is None:
            return Response(
                {
                    "error": {
                        "code": "quote_error",
                        "message": f"No quote available for asset {asset.display_symbol}",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    guardrails_check = check_guardrails(portfolio, asset, action, quantity, quote.price)
    if not guardrails_check["valid"]:
        return Response(
            {
                "error": {
                    "code": "guardrails_violation",
                    "message": "Trade violates portfolio guardrails",
                    "violations": guardrails_check["violations"],
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if action == "BUY":
            result = execute_buy(
                portfolio=portfolio,
                asset=asset,
                quantity=quantity,
                rationale=reason,
                executed_by="agent",
            )
        elif action == "SELL":
            result = execute_sell(
                portfolio=portfolio,
                asset=asset,
                quantity=quantity,
                rationale=reason,
                executed_by="agent",
            )
        else:
            return Response(
                {"error": {"code": "invalid_action", "message": "action must be BUY or SELL"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ValueError as e:
        error_msg = str(e)
        details = e.args[1] if len(e.args) > 1 and isinstance(e.args[1], dict) else {}
        return Response(
            {
                "error": {
                    "code": "trade_error",
                    "message": error_msg,
                    "details": {k: str(v) for k, v in details.items()},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    trade_serializer = TradeSerializer(result["trade"])
    from portfolios.services import get_portfolio_summary

    portfolio.refresh_from_db()
    summary = get_portfolio_summary(portfolio)

    response_data = {
        "trade": trade_serializer.data,
        "cash": str(portfolio.current_cash),
        "summary": summary,
    }
    if result.get("position"):
        response_data["position"] = PositionSerializer(result["position"]).data

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agent_portfolio_state(request):
    """Get current portfolio state for agent decision-making.

    Query params:
        portfolio_id: uuid (required)

    Returns:
    {
        "portfolio": {...},
        "positions": [
            {
                "asset": {...},
                "quantity": number,
                "average_cost": "decimal",
                "current_price": "decimal",
                "market_value": "decimal",
                "unrealized_pnl": "decimal"
            }
        ],
        "cash": "decimal",
        "total_equity": "decimal",
        "assets_with_indicators": [
            {
                "asset": {...},
                "latest_indicators": {
                    "date": "2026-04-13",
                    "rsi_14": number,
                    "macd": number,
                    ...
                }
            }
        ]
    }
    """
    portfolio_id = request.query_params.get("portfolio_id")
    if not portfolio_id:
        return Response(
            {"error": {"code": "missing_portfolio_id", "message": "portfolio_id query param required"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

    from portfolios.serializers import PortfolioSummarySerializer
    from markets.models import TechnicalIndicators

    positions = Position.objects.filter(portfolio=portfolio).select_related("asset")
    position_data = []

    for pos in positions:
        quote = pos.asset.get_latest_quote()
        market_value = quote.price * pos.quantity if quote else 0
        unrealized_pnl = (quote.price - pos.average_cost) * pos.quantity if quote else 0

        position_data.append({
            "asset": {
                "id": str(pos.asset.id),
                "symbol": pos.asset.display_symbol,
                "name": pos.asset.name,
                "market": pos.asset.market,
            },
            "quantity": pos.quantity,
            "average_cost": str(pos.average_cost),
            "current_price": str(quote.price) if quote else None,
            "market_value": str(market_value),
            "unrealized_pnl": str(unrealized_pnl),
        })

    assets_in_portfolio = {pos.asset_id for pos in positions}
    assets_with_indicators = []

    for asset_id in assets_in_portfolio:
        asset = Asset.objects.get(id=asset_id)
        latest_indicators = TechnicalIndicators.objects.filter(asset=asset).order_by("-date").first()

        if latest_indicators:
            assets_with_indicators.append({
                "asset": {
                    "id": str(asset.id),
                    "symbol": asset.display_symbol,
                    "name": asset.name,
                    "market": asset.market,
                },
                "latest_indicators": {
                    "date": str(latest_indicators.date),
                    "rsi_14": float(latest_indicators.rsi_14) if latest_indicators.rsi_14 else None,
                    "macd": float(latest_indicators.macd) if latest_indicators.macd else None,
                    "macd_signal": float(latest_indicators.macd_signal) if latest_indicators.macd_signal else None,
                    "macd_histogram": float(latest_indicators.macd_histogram) if latest_indicators.macd_histogram else None,
                    "ma_20": float(latest_indicators.ma_20) if latest_indicators.ma_20 else None,
                    "ma_50": float(latest_indicators.ma_50) if latest_indicators.ma_50 else None,
                    "ma_200": float(latest_indicators.ma_200) if latest_indicators.ma_200 else None,
                    "bb_upper": float(latest_indicators.bb_upper) if latest_indicators.bb_upper else None,
                    "bb_middle": float(latest_indicators.bb_middle) if latest_indicators.bb_middle else None,
                    "bb_lower": float(latest_indicators.bb_lower) if latest_indicators.bb_lower else None,
                    "volume_20d_avg": int(latest_indicators.volume_20d_avg) if latest_indicators.volume_20d_avg else None,
                },
            })

    summary = get_portfolio_summary(portfolio)

    return Response({
        "portfolio": {
            "id": str(portfolio.id),
            "name": portfolio.name,
            "market": portfolio.market,
        },
        "positions": position_data,
        "cash": str(portfolio.current_cash),
        "total_equity": summary.get("total_equity"),
        "assets_with_indicators": assets_with_indicators,
    })
