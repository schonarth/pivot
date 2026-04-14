from django.urls import path
from .views import (
    OTPGenerateView, TokenExchangeView, AgentsListView, AgentRevokeView,
    MCPAssetInsightView, AISettingsView, StrategyRulesListView,
    StrategyInstancesListView, StrategyTradesListView, AgentTradesListView,
    BacktestCreateView, BacktestResultsView
)

urlpatterns = [
    path('otp/generate/', OTPGenerateView.as_view(), name='otp-generate'),
    path('token/exchange/', TokenExchangeView.as_view(), name='token-exchange'),
    path('agents/', AgentsListView.as_view(), name='agents-list'),
    path('agents/<int:agent_id>/', AgentRevokeView.as_view(), name='agents-revoke'),
    path('asset-insight/', MCPAssetInsightView.as_view(), name='asset-insight'),
    path('ai-settings/', AISettingsView.as_view(), name='ai-settings'),
    path('strategy-rules/', StrategyRulesListView.as_view(), name='strategy-rules'),
    path('strategy-instances/', StrategyInstancesListView.as_view(), name='strategy-instances'),
    path('strategy-trades/', StrategyTradesListView.as_view(), name='strategy-trades'),
    path('agent-trades/', AgentTradesListView.as_view(), name='agent-trades'),
    path('backtest/create/', BacktestCreateView.as_view(), name='backtest-create'),
    path('backtest/<uuid:backtest_id>/results/', BacktestResultsView.as_view(), name='backtest-results'),
]
