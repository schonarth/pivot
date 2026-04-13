from django.urls import path
from .views import OTPGenerateView, TokenExchangeView, AgentsListView, AgentRevokeView

urlpatterns = [
    path('otp/generate/', OTPGenerateView.as_view(), name='otp-generate'),
    path('token/exchange/', TokenExchangeView.as_view(), name='token-exchange'),
    path('agents/', AgentsListView.as_view(), name='agents-list'),
    path('agents/<int:agent_id>/', AgentRevokeView.as_view(), name='agents-revoke'),
]
