from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User
from .models import AgentToken
from .serializers import (
    OTPSerializer,
    AgentTokenSerializer,
    TokenExchangeSerializer,
    FactCorrectionCreateSerializer,
    ArtifactReviewCreateSerializer,
    SourceStanceCreateSerializer,
    EvidenceRecordSerializer,
)
from .services import generate_otp, validate_and_use_otp, generate_agent_token
from realtime.services import publish_event


class OTPGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate a new OTP for the authenticated user."""
        code = generate_otp(request.user)
        otp = request.user.otps.get(code=code)
        serializer = OTPSerializer(otp)
        return Response(serializer.data)


class TokenExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Exchange OTP for an agent token. Public endpoint—OTP is the authentication."""
        serializer = TokenExchangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data['user_id']
        code = data['otp']
        name = data['name']
        origin = data.get('origin') or 'unknown'
        llm_model = data['llm_model']
        llm_provider = data['llm_provider']

        # Look up user by api_uuid
        try:
            user = User.objects.get(api_uuid=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid user ID'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validate OTP
        if not validate_and_use_otp(user, code):
            return Response(
                {'error': 'Invalid or expired OTP'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate agent token
        token = generate_agent_token(user, name, origin, llm_provider=llm_provider, llm_model=llm_model)

        # Notify user via websocket that agent connected
        publish_event(
            f"user_{user.id}",
            "agent_connected",
            {"agent_name": name, "agent_origin": origin, "llm_provider": llm_provider, "llm_model": llm_model}
        )

        return Response({
            'token': token,
            'ttl': None,
            'note': 'Token is permanent until revoked. Use with /api/* endpoints (portfolios, assets, strategies, backtest-scenarios, ai, markets, etc.).'
        }, status=status.HTTP_201_CREATED)


class AgentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all authenticated agents for the current user."""
        agents = request.user.agent_tokens.all()
        serializer = AgentTokenSerializer(agents, many=True)
        return Response(serializer.data)


class AgentRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, agent_id):
        """Revoke an agent token."""
        try:
            agent = request.user.agent_tokens.get(id=agent_id)
            agent.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TokenValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate an agent token. Useful for checking token status mid-operation."""
        agent_token = request.data.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
            return Response({
                'valid': True,
                'agent_name': agent.name,
                'agent_origin': agent.origin,
                'created_at': agent.created_at,
                'last_used_at': agent.last_used_at,
                'note': 'Token is permanent. If invalid, token was revoked via user dashboard.'
            })
        except AgentToken.DoesNotExist:
            return Response(
                {
                    'valid': False,
                    'error': 'Token not found or revoked',
                    'possible_causes': [
                        'Token was revoked via user dashboard',
                        'Invalid token provided',
                        'Token belongs to different user'
                    ]
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


class MCPAssetInsightView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Get AI insight for an asset via MCP agent."""
        from markets.models import Asset
        from ai.services import AIBudgetError, AIService

        agent_token = request.data.get('agent_token')
        asset_id = request.data.get('asset_id')

        if not agent_token or not asset_id:
            return Response(
                {'error': 'Missing agent_token or asset_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return Response(
                {'error': 'Asset not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        service = AIService(agent.user)
        try:
            insight = service.analyze_asset(asset)
        except AIBudgetError as exc:
            return Response(
                {'error': 'Budget exceeded', 'details': str(exc)},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except ValueError as exc:
            return Response(
                {'error': 'AI unavailable', 'details': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {'error': 'Failed to generate insight'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(insight)


class MCPAssetLookupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Look up an asset by symbol and create it from trusted sources when missing."""
        from markets.models import MarketConfig
        from markets.serializers import AssetSerializer
        from markets.services import search_asset_symbols

        agent_token = request.data.get('agent_token')
        symbol = request.data.get('symbol')
        market = str(request.data.get('market') or '').strip().upper() or None

        if not agent_token or not symbol:
            return Response(
                {'error': 'Missing agent_token or symbol'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if market and not MarketConfig.objects.filter(code=market).exists():
            return Response(
                {'error': 'Invalid market'},
                status=status.HTTP_400_BAD_REQUEST
            )

        assets = search_asset_symbols(symbol, market=market)
        if not assets:
            return Response(
                {'error': 'Symbol not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)


class AISettingsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Get AI settings and budget info via MCP agent."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        ai_auth = user.ai_auth

        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        from ai.models import AICost

        # Calculate this month's costs
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_costs = AICost.objects.filter(
            ai_auth=ai_auth,
            created_at__gte=month_start
        ).values_list('cost_usd', flat=True)

        total_cost = sum(month_costs)
        budget = Decimal(str(ai_auth.monthly_budget_usd))
        remaining = budget - Decimal(str(total_cost))
        usage_percent = int((float(total_cost) / float(budget) * 100)) if budget > 0 else 0

        return Response({
            'provider_name': ai_auth.provider_name,
            'monthly_budget_usd': str(budget),
            'alert_threshold_pct': ai_auth.alert_threshold_pct,
            'task_models': ai_auth.task_models,
            'has_api_key': ai_auth.api_key_encrypted is not None,
            'total_cost_month_usd': str(total_cost),
            'usage_percent': min(usage_percent, 100),
            'remaining_budget_usd': str(max(remaining, Decimal('0'))),
        })


class StrategyRulesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List all available strategy rules."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        from strategies.models import StrategyRule
        from strategies.serializers import StrategyRuleSerializer

        rules = StrategyRule.objects.all()
        serializer = StrategyRuleSerializer(rules, many=True)
        return Response(serializer.data)


class StrategyInstancesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List user's strategy instances for their portfolios."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        from strategies.models import StrategyInstance
        from strategies.serializers import StrategyInstanceSerializer

        # Get all strategy instances for user's portfolios
        instances = StrategyInstance.objects.filter(
            portfolio__user=user
        ).select_related('portfolio', 'rule')

        serializer = StrategyInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class StrategyTradesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List trades executed by strategies."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        from strategies.models import StrategyTrade, StrategyInstance
        from strategies.serializers import StrategyTradeSerializer

        # Get all trades from strategy instances belonging to user's portfolios
        trades = StrategyTrade.objects.filter(
            strategy_instance__portfolio__user=user
        ).select_related('strategy_instance').order_by('-executed_at')

        serializer = StrategyTradeSerializer(trades, many=True)
        return Response(serializer.data)


class AgentTradesListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List trades executed by agents."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        from trading.models import Trade
        from trading.serializers import TradeSerializer

        # Get all agent-executed trades for user's portfolios
        trades = Trade.objects.filter(
            portfolio__user=user,
            executed_by='agent'
        ).select_related('portfolio', 'asset').order_by('-executed_at')

        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)


class BacktestCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Create a new backtest scenario."""
        agent_token = request.data.get('agent_token')
        strategy_instance_id = request.data.get('strategy_instance_id')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')

        if not all([agent_token, strategy_instance_id, date_from, date_to]):
            return Response(
                {'error': 'Missing agent_token, strategy_instance_id, date_from, or date_to'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        from strategies.models import StrategyInstance, BacktestScenario
        from strategies.serializers import BacktestScenarioSerializer

        try:
            strategy_instance = StrategyInstance.objects.get(
                id=strategy_instance_id,
                portfolio__user=user
            )
        except StrategyInstance.DoesNotExist:
            return Response(
                {'error': 'Strategy instance not found or not owned by user'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            backtest = BacktestScenario.objects.create(
                strategy_instance=strategy_instance,
                date_from=date_from,
                date_to=date_to,
                status='pending'
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create backtest: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BacktestScenarioSerializer(backtest)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BacktestResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, backtest_id):
        """Get backtest scenario results."""
        agent_token = request.query_params.get('agent_token')

        if not agent_token:
            return Response(
                {'error': 'Missing agent_token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = AgentToken.objects.get(token=agent_token)
        except AgentToken.DoesNotExist:
            return Response(
                {'error': 'Invalid agent token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = agent.user
        from strategies.models import BacktestScenario
        from strategies.serializers import BacktestScenarioSerializer

        try:
            backtest = BacktestScenario.objects.get(
                id=backtest_id,
                strategy_instance__portfolio__user=user
            )
        except BacktestScenario.DoesNotExist:
            return Response(
                {'error': 'Backtest not found or not owned by user'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BacktestScenarioSerializer(backtest)
        return Response(serializer.data)


class MCPEvidenceView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def _agent(request, location):
        token = request.query_params.get("agent_token") if location == "query" else request.data.get("agent_token")
        if not token:
            return None, Response({"error": "Missing agent_token"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return AgentToken.objects.select_related("user").get(token=token), None
        except AgentToken.DoesNotExist:
            return None, Response({"error": "Invalid agent token"}, status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def _news_item_for_operator(operator, news_item_id):
        from ai.models import StrategyRecommendation
        from markets.models import NewsItem

        for recommendation in StrategyRecommendation.objects.filter(user=operator).only("context_inputs"):
            context_items = recommendation.context_inputs.get("items", [])
            if any(
                str(item.get("news_item_id")) == str(news_item_id)
                for item in context_items
                if isinstance(item, dict)
            ):
                return NewsItem.objects.filter(id=news_item_id).select_related("news_source").first()
        return None


class MCPEvidenceRetrieveView(MCPEvidenceView):
    def get(self, request, recommendation_id):
        agent, error = self._agent(request, "query")
        if error:
            return error

        from ai.models import StrategyRecommendation
        from ai.serializers import StrategyRecommendationSerializer
        from ai.services import EvidenceReviewService

        recommendation = StrategyRecommendation.objects.filter(user=agent.user, id=recommendation_id).first()
        if recommendation is None:
            return Response({"error": "Recommendation not found"}, status=status.HTTP_404_NOT_FOUND)
        data = StrategyRecommendationSerializer(recommendation).data
        return Response(
            {
                "recommendation_id": data["id"],
                "evidence": data["evidence"],
                "is_invalidated": data["is_invalidated"],
                "latest_invalidation": data["latest_invalidation"],
                "fact_key_suggestions": EvidenceReviewService(agent.user).fact_key_suggestions(),
            }
        )


class MCPFactCorrectionCreateView(MCPEvidenceView):
    def post(self, request):
        agent, error = self._agent(request, "body")
        if error:
            return error
        serializer = FactCorrectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        news_item = self._news_item_for_operator(agent.user, data["news_item_id"])
        if news_item is None:
            return Response({"error": "Evidence artifact not found"}, status=status.HTTP_404_NOT_FOUND)

        from ai.services import EvidenceReviewService

        correction = EvidenceReviewService(agent.user).create_fact_correction(
            news_item=news_item,
            fact_key=data["fact_key"],
            corrected_value=data["corrected_value"],
            correction_state=data["correction_state"],
            reason=data["reason"],
            actor=agent,
        )
        return Response(EvidenceRecordSerializer(correction).data, status=status.HTTP_201_CREATED)


class MCPArtifactReviewCreateView(MCPEvidenceView):
    def post(self, request):
        agent, error = self._agent(request, "body")
        if error:
            return error
        serializer = ArtifactReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        news_item = self._news_item_for_operator(agent.user, data["news_item_id"])
        if news_item is None:
            return Response({"error": "Evidence artifact not found"}, status=status.HTTP_404_NOT_FOUND)

        from ai.services import EvidenceReviewService

        review = EvidenceReviewService(agent.user).set_artifact_review(
            news_item,
            data["artifact_review_state"],
            data["reason"],
            actor=agent,
        )
        return Response(EvidenceRecordSerializer(review).data, status=status.HTTP_201_CREATED)


class MCPSourceStanceCreateView(MCPEvidenceView):
    def post(self, request):
        agent, error = self._agent(request, "body")
        if error:
            return error
        serializer = SourceStanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from markets.models import NewsSource

        source = NewsSource.objects.filter(id=data["source_id"]).first()
        if source is None or not any(
            self._news_item_for_operator(agent.user, item.id)
            for item in source.news_items.only("id")
        ):
            return Response({"error": "Evidence source not found"}, status=status.HTTP_404_NOT_FOUND)

        from ai.services import EvidenceReviewService

        service = EvidenceReviewService(agent.user)
        if data["clear"]:
            service.clear_source_stance(source, actor=agent)
            return Response(status=status.HTTP_204_NO_CONTENT)
        stance = service.set_source_stance(source, data["stance"], actor=agent)
        return Response(EvidenceRecordSerializer(stance).data, status=status.HTTP_201_CREATED)


class MCPSchemaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Discovery endpoint listing all MCP API endpoints and their capabilities."""
        endpoints = [
            {
                'name': 'OTP Generate',
                'method': 'POST',
                'path': '/api/mcp/otp/generate/',
                'description': 'Generate a one-time password for agent authentication',
                'auth': 'User session (authenticated)',
                'params': [],
                'response': {'code': 'string', 'expires_at': 'ISO 8601 datetime'}
            },
            {
                'name': 'Token Exchange',
                'method': 'POST',
                'path': '/api/mcp/token/exchange/',
                'description': 'Exchange OTP for agent token',
                'auth': 'OTP-based',
                'params': [
                    {'name': 'user_id', 'type': 'string', 'required': True, 'description': 'User API UUID'},
                    {'name': 'otp', 'type': 'string', 'required': True, 'description': 'One-time password'},
                    {'name': 'name', 'type': 'string', 'required': False, 'description': 'Agent name'},
                    {'name': 'origin', 'type': 'string', 'required': False, 'description': 'Agent origin/source'}
                ],
                'response': {'token': 'string'}
            },
            {
                'name': 'Agents List',
                'method': 'GET',
                'path': '/api/mcp/agents/',
                'description': 'List all authenticated agents for the current user',
                'auth': 'User session (authenticated)',
                'params': [],
                'response': [{'id': 'UUID', 'name': 'string', 'token': 'string', 'created_at': 'ISO 8601'}]
            },
            {
                'name': 'Agent Revoke',
                'method': 'DELETE',
                'path': '/api/mcp/agents/<id>/',
                'description': 'Revoke an agent token',
                'auth': 'User session (authenticated)',
                'params': [{'name': 'id', 'type': 'UUID', 'required': True, 'location': 'path'}],
                'response': {}
            },
            {
                'name': 'Asset Insight',
                'method': 'POST',
                'path': '/api/mcp/asset-insight/',
                'description': 'Get AI-powered insight for a specific asset',
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'asset_id', 'type': 'UUID', 'required': True}
                ],
                'response': {'summary': 'string', 'technical_analysis': 'object', 'sentiment': 'object', 'recommendation': 'string'}
            },
            {
                'name': 'Asset Lookup',
                'method': 'POST',
                'path': '/api/mcp/assets/lookup-symbol/',
                'description': 'Look up an asset symbol and create it from trusted sources when missing',
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'symbol', 'type': 'string', 'required': True},
                    {'name': 'market', 'type': 'string', 'required': False}
                ],
                'response': [{'id': 'UUID', 'display_symbol': 'string', 'provider_symbol': 'string', 'market': 'string'}]
            },
            {
                'name': 'Discovery Search',
                'method': 'GET',
                'path': '/api/ai/discovery/',
                'description': 'Surface a bounded discovery shortlist for a selected market',
                'auth': 'User session (authenticated)',
                'params': [
                    {'name': 'market', 'type': 'string', 'required': True, 'location': 'query'},
                    {'name': 'refine', 'type': 'boolean', 'required': False, 'location': 'query'},
                    {'name': 'refresh', 'type': 'boolean', 'required': False, 'location': 'query'}
                ],
                'response': {'market': 'string', 'shortlist': 'array', 'refined': 'boolean', 'cache_key': 'string'}
            },
            {
                'name': 'AI Settings',
                'method': 'GET',
                'path': '/api/mcp/ai-settings/',
                'description': 'Get user AI budget and settings (read-only)',
                'auth': 'Agent token',
                'params': [{'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}],
                'response': {
                    'provider_name': 'string',
                    'monthly_budget_usd': 'string',
                    'alert_threshold_pct': 'integer',
                    'has_api_key': 'boolean',
                    'total_cost_month_usd': 'string',
                    'usage_percent': 'integer',
                    'remaining_budget_usd': 'string'
                }
            },
            {
                'name': 'Strategy Rules',
                'method': 'GET',
                'path': '/api/mcp/strategy-rules/',
                'description': 'List all available strategy rules',
                'auth': 'Agent token',
                'params': [{'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}],
                'response': [{'id': 'UUID', 'name': 'string', 'description': 'string', 'parameters': 'object'}]
            },
            {
                'name': 'Strategy Instances',
                'method': 'GET',
                'path': '/api/mcp/strategy-instances/',
                'description': 'List user\'s strategy instances',
                'auth': 'Agent token',
                'params': [{'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}],
                'response': [{'id': 'UUID', 'rule_id': 'UUID', 'portfolio_id': 'UUID', 'status': 'string'}]
            },
            {
                'name': 'Strategy Trades',
                'method': 'GET',
                'path': '/api/mcp/strategy-trades/',
                'description': 'List trades executed by strategies',
                'auth': 'Agent token',
                'params': [{'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}],
                'response': [{'id': 'UUID', 'strategy_instance_id': 'UUID', 'asset_id': 'UUID', 'quantity': 'number', 'executed_at': 'ISO 8601'}]
            },
            {
                'name': 'Agent Trades',
                'method': 'GET',
                'path': '/api/mcp/agent-trades/',
                'description': 'List trades executed by agents',
                'auth': 'Agent token',
                'params': [{'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}],
                'response': [{'id': 'UUID', 'portfolio_id': 'UUID', 'asset_id': 'UUID', 'side': 'string', 'quantity': 'number', 'executed_at': 'ISO 8601'}]
            },
            {
                'name': 'Create Backtest',
                'method': 'POST',
                'path': '/api/mcp/backtest/create/',
                'description': 'Create a new backtest scenario',
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'strategy_instance_id', 'type': 'UUID', 'required': True},
                    {'name': 'date_from', 'type': 'ISO 8601', 'required': True},
                    {'name': 'date_to', 'type': 'ISO 8601', 'required': True}
                ],
                'response': {'id': 'UUID', 'status': 'string', 'strategy_instance_id': 'UUID'}
            },
            {
                'name': 'Backtest Results',
                'method': 'GET',
                'path': '/api/mcp/backtest/<id>/results/',
                'description': 'Get backtest scenario results',
                'auth': 'Agent token',
                'params': [
                    {'name': 'id', 'type': 'UUID', 'required': True, 'location': 'path'},
                    {'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'}
                ],
                'response': {'id': 'UUID', 'status': 'string', 'result': 'object', 'created_at': 'ISO 8601'}
            },
            {
                'name': 'Evidence Review',
                'method': 'GET',
                'path': '/api/mcp/evidence/<recommendation_id>/',
                'description': (
                    'Retrieve scoped evidence, correction history, treatment, invalidation state, and fact-key suggestions.'
                ),
                'auth': 'Agent token',
                'params': [
                    {'name': 'recommendation_id', 'type': 'UUID', 'required': True, 'location': 'path'},
                    {'name': 'agent_token', 'type': 'string', 'required': True, 'location': 'query'},
                ],
                'response': {
                    'recommendation_id': 'UUID',
                    'evidence': 'array',
                    'is_invalidated': 'boolean',
                    'fact_key_suggestions': 'array',
                },
            },
            {
                'name': 'Create Fact Correction',
                'method': 'POST',
                'path': '/api/mcp/evidence/fact-corrections/',
                'description': (
                    'Create or supersede a scoped fact correction. Reuse a suggested fact_key when suitable; '
                    'original_value is platform-captured and must not be supplied.'
                ),
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'news_item_id', 'type': 'UUID', 'required': True},
                    {'name': 'fact_key', 'type': 'string', 'required': True},
                    {'name': 'corrected_value', 'type': 'string', 'required': True},
                    {'name': 'correction_state', 'type': 'corrected|disputed|stale', 'required': True},
                    {'name': 'reason', 'type': 'string', 'required': True},
                ],
                'response': {
                    'id': 'UUID',
                    'fact_key': 'string',
                    'original_value': 'string',
                    'created_by_agent': 'object',
                },
            },
            {
                'name': 'Create Artifact Review',
                'method': 'POST',
                'path': '/api/mcp/evidence/artifact-reviews/',
                'description': 'Create or supersede a scoped artifact review.',
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'news_item_id', 'type': 'UUID', 'required': True},
                    {'name': 'artifact_review_state', 'type': 'accepted|disputed|stale', 'required': True},
                    {'name': 'reason', 'type': 'string', 'required': True},
                ],
                'response': {'id': 'UUID', 'artifact_review_state': 'string', 'created_by_agent': 'object'}
            },
            {
                'name': 'Set or Clear Source Stance',
                'method': 'POST',
                'path': '/api/mcp/evidence/source-stances/',
                'description': (
                    'Set trusted or untrusted for a scoped source, or clear the active stance with clear=true.'
                ),
                'auth': 'Agent token',
                'params': [
                    {'name': 'agent_token', 'type': 'string', 'required': True},
                    {'name': 'source_id', 'type': 'integer', 'required': True},
                    {'name': 'stance', 'type': 'trusted|untrusted', 'required': False},
                    {'name': 'clear', 'type': 'boolean', 'required': False},
                ],
                'response': {'id': 'UUID', 'stance': 'string', 'created_by_agent': 'object'}
            }
        ]

        return Response({
            'version': '1.0',
            'base_url': '/api/mcp/',
            'authentication': {
                'user': 'Django session or JWT',
                'agent': 'Agent token (obtained via OTP exchange)'
            },
            'endpoints': endpoints,
            'caching': {
                'asset_insights': '24 hours',
                'news_sentiment': '24 hours',
                'strategy_data': 'No cache (real-time)',
                'discovery_refinement': '24 hours'
            }
        })
