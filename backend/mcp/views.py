from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User
from .models import AgentToken
from .serializers import OTPSerializer, AgentTokenSerializer
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
        user_id = request.data.get('user_id')
        code = request.data.get('otp')
        name = request.data.get('name', 'Unknown Agent')
        origin = request.data.get('origin', 'unknown')

        if not user_id or not code:
            return Response(
                {'error': 'Missing user_id or otp'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        token = generate_agent_token(user, name, origin)

        # Notify user via websocket that agent connected
        publish_event(
            f"user_{user.id}",
            "agent_connected",
            {"agent_name": name, "agent_origin": origin}
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
            agent = AgentToken.objects.get(token=agent_token)
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
                'strategy_data': 'No cache (real-time)'
            }
        })
