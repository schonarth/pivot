from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import StrategyRule, StrategyInstance, BacktestScenario, StrategyTrade
from .serializers import StrategyRuleSerializer, StrategyInstanceSerializer, BacktestScenarioSerializer, StrategyTradeSerializer
from portfolios.models import Portfolio


class StrategyRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """List available predefined strategy rules."""
    queryset = StrategyRule.objects.all()
    serializer_class = StrategyRuleSerializer
    permission_classes = [IsAuthenticated]


class StrategyInstanceViewSet(viewsets.ModelViewSet):
    """Manage strategy instances per portfolio."""
    serializer_class = StrategyInstanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = StrategyInstance.objects.filter(
            portfolio__user=self.request.user
        )
        portfolio_id = self.request.query_params.get('portfolio_id')
        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)
        return queryset

    def perform_create(self, serializer):
        portfolio_id = self.request.data.get("portfolio_id")
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)
        serializer.save(portfolio=portfolio)

    @action(detail=True, methods=["post"])
    def run_backtest(self, request, pk=None):
        """Run backtest for this strategy.

        Request body: {"date_from": "2024-01-01", "date_to": "2024-06-30"}
        """
        strategy = self.get_object()
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")

        if not date_from or not date_to:
            return Response(
                {"error": "date_from and date_to are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import run_backtest_async

        scenario = BacktestScenario.objects.create(
            strategy_instance=strategy,
            date_from=date_from,
            date_to=date_to,
            status="pending",
        )

        run_backtest_async.delay(str(scenario.id))

        serializer = BacktestScenarioSerializer(scenario)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"])
    def backtests(self, request, pk=None):
        """List all backtests for this strategy."""
        strategy = self.get_object()
        backtests = strategy.backtest_scenarios.all().order_by("-created_at")
        serializer = BacktestScenarioSerializer(backtests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def trades(self, request, pk=None):
        """List all trades executed by this strategy."""
        strategy = self.get_object()
        trades = strategy.trades.all().order_by("-executed_at")
        serializer = StrategyTradeSerializer(trades, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve_backtest(self, request, pk=None):
        """Approve a backtest and enable auto-execution."""
        strategy = self.get_object()
        strategy.enabled = True
        strategy.backtest_approved_at = timezone.now()
        strategy.save()

        serializer = StrategyInstanceSerializer(strategy)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """Disable auto-execution for this strategy."""
        strategy = self.get_object()
        strategy.enabled = False
        strategy.save()

        serializer = StrategyInstanceSerializer(strategy)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BacktestScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    """View backtest scenarios and results."""
    serializer_class = BacktestScenarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BacktestScenario.objects.filter(
            strategy_instance__portfolio__user=self.request.user
        )


class StrategyTradeViewSet(viewsets.ReadOnlyModelViewSet):
    """View trades executed by strategies."""
    serializer_class = StrategyTradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StrategyTrade.objects.filter(
            strategy_instance__portfolio__user=self.request.user
        )
