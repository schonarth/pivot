from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User
from .models import AgentToken
from .serializers import OTPSerializer, AgentTokenSerializer
from .services import generate_otp, validate_and_use_otp, generate_agent_token


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
        return Response({'token': token}, status=status.HTTP_201_CREATED)


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
