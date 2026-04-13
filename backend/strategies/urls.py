from rest_framework.routers import DefaultRouter
from .views import (
    StrategyRuleViewSet,
    StrategyInstanceViewSet,
    BacktestScenarioViewSet,
    StrategyTradeViewSet,
)

router = DefaultRouter()
router.register(r"strategy-rules", StrategyRuleViewSet, basename="strategy-rule")
router.register(r"strategy-instances", StrategyInstanceViewSet, basename="strategy-instance")
router.register(r"backtest-scenarios", BacktestScenarioViewSet, basename="backtest-scenario")
router.register(r"strategy-trades", StrategyTradeViewSet, basename="strategy-trade")

urlpatterns = router.urls
