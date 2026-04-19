from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CashTransaction, Portfolio, PortfolioSnapshot, PortfolioGuardrails
from .serializers import (
    CashTransactionSerializer,
    CreatePortfolioSerializer,
    DepositWithdrawSerializer,
    PortfolioSerializer,
    PortfolioSnapshotSerializer,
    PortfolioSummarySerializer,
    PortfolioGuardrailsSerializer,
)
from markets.models import Asset
from .services import (
    add_watch_asset,
    calculate_twr,
    create_portfolio,
    deposit,
    get_portfolio_scope_insight,
    get_portfolio_summary,
    remove_watch_asset,
    withdraw,
)


class WatchAssetSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()


class PortfolioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        raise NotImplementedError("Use create action instead")

    def create(self, request):
        input_serializer = CreatePortfolioSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = create_portfolio(
            user=request.user,
            name=input_serializer.validated_data["name"],
            market=input_serializer.validated_data["market"],
            initial_capital=input_serializer.validated_data["initial_capital"],
        )

        portfolio = result["portfolio"]
        output_serializer = PortfolioSerializer(portfolio)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        portfolio = self.get_object()
        summary = get_portfolio_summary(portfolio)
        return Response(summary)

    @action(detail=True, methods=["get"])
    def scope_insight(self, request, pk=None):
        portfolio = self.get_object()
        scope = request.query_params.get("scope")

        if scope not in {"portfolio", "watch"}:
            return Response(
                {"error": "Missing or invalid scope"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        insight = get_portfolio_scope_insight(portfolio, scope)
        return Response({"insight": insight})

    @action(detail=True, methods=["post", "delete"])
    def watch(self, request, pk=None):
        portfolio = self.get_object()
        serializer = WatchAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = get_object_or_404(Asset, id=serializer.validated_data["asset_id"])

        if request.method == "POST":
            result = add_watch_asset(portfolio=portfolio, asset=asset)
            return Response(
                {
                    "asset_id": str(asset.id),
                    "portfolio_id": str(portfolio.id),
                    "created": result["created"],
                },
                status=status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK,
            )

        result = remove_watch_asset(portfolio=portfolio, asset=asset)
        return Response(
            {
                "asset_id": str(asset.id),
                "portfolio_id": str(portfolio.id),
                "deleted": result["deleted"],
            }
        )

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None):
        portfolio = self.get_object()
        twr = calculate_twr(portfolio)
        snapshots = PortfolioSnapshot.objects.filter(portfolio=portfolio).order_by("captured_at")
        return Response(
            {
                "twr": str(twr),
                "snapshots": PortfolioSnapshotSerializer(snapshots, many=True).data,
            }
        )

    @action(detail=True, methods=["post"])
    def refresh_prices(self, request, pk=None):
        portfolio = self.get_object()
        from trading.models import Position
        from markets.quote_provider import refresh_asset_quote

        assets = Position.objects.filter(portfolio=portfolio).values_list("asset_id", flat=True)
        refreshed = 0
        for asset_id in assets:
            try:
                result = refresh_asset_quote(str(asset_id))
                if result:
                    refreshed += 1
            except Exception:
                pass

        from .services import _create_snapshot
        from realtime.services import publish_event

        _create_snapshot(portfolio)
        publish_event(f"portfolio_{portfolio.id}", "price.updated", {"portfolio_id": str(portfolio.id)})

        return Response({"refreshed": refreshed})

    @action(detail=True, methods=["post"])
    def deposit(self, request, pk=None):
        portfolio = self.get_object()
        input_serializer = DepositWithdrawSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = deposit(portfolio=portfolio, amount=input_serializer.validated_data["amount"])
        return Response(
            {
                "transaction": CashTransactionSerializer(result["transaction"]).data,
                "cash": str(portfolio.current_cash),
            }
        )

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        portfolio = self.get_object()
        input_serializer = DepositWithdrawSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = withdraw(portfolio=portfolio, amount=input_serializer.validated_data["amount"])
        response_data = {
            "transaction": CashTransactionSerializer(result["transaction"]).data,
            "cash": str(portfolio.current_cash),
        }
        if result["clamped"]:
            response_data["warning"] = f"Withdrawal clamped to {result['actual_amount']} due to insufficient cash."
        return Response(response_data)

    @action(detail=True, methods=["get"])
    def cash_transactions(self, request, pk=None):
        portfolio = self.get_object()
        transactions = CashTransaction.objects.filter(portfolio=portfolio)
        serializer = CashTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        portfolio = self.get_object()
        from timeline.models import TimelineEvent

        events = TimelineEvent.objects.filter(portfolio=portfolio).order_by("-created_at")
        from timeline.serializers import TimelineEventSerializer

        return Response(TimelineEventSerializer(events, many=True).data)

    @action(detail=True, methods=["get", "put", "patch"])
    def guardrails(self, request, pk=None):
        portfolio = self.get_object()
        guardrails = get_object_or_404(PortfolioGuardrails, portfolio=portfolio)

        if request.method == "GET":
            serializer = PortfolioGuardrailsSerializer(guardrails)
            return Response(serializer.data)

        serializer = PortfolioGuardrailsSerializer(guardrails, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CashTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CashTransactionSerializer

    def get_queryset(self):
        return CashTransaction.objects.filter(portfolio__user=self.request.user)
