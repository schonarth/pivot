from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from markets.models import Asset
from portfolios.models import Portfolio
from .models import Position, Trade
from .serializers import PositionDetailSerializer, PositionSerializer, TradeCreateSerializer, TradeSerializer
from .services import execute_buy, execute_sell


class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PositionDetailSerializer

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