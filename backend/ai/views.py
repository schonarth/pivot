from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AIAuth
from .serializers import AIAuthSettingsSerializer, AIBudgetSerializer
from .services import AIService


class AISettingsViewSet(viewsets.ViewSet):
    """Manage AI settings and API key configuration."""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def budget(self, request):
        """Get current AI budget and usage info."""
        service = AIService(request.user)
        budget_info = service.get_budget_info()
        serializer = AIBudgetSerializer(budget_info)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_settings(self, request):
        """Get current AI settings."""
        ai_auth, created = AIAuth.objects.get_or_create(user=request.user)
        serializer = AIAuthSettingsSerializer(ai_auth)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_settings(self, request):
        """Update AI settings (budget, provider, threshold, task models)."""
        ai_auth, created = AIAuth.objects.get_or_create(user=request.user)

        if "monthly_budget_usd" in request.data:
            ai_auth.monthly_budget_usd = request.data["monthly_budget_usd"]

        if "alert_threshold_pct" in request.data:
            ai_auth.alert_threshold_pct = request.data["alert_threshold_pct"]

        if "provider_name" in request.data:
            ai_auth.provider_name = request.data["provider_name"]

        if "task_models" in request.data:
            ai_auth.task_models = request.data["task_models"]

        ai_auth.save()
        serializer = AIAuthSettingsSerializer(ai_auth)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def set_api_key(self, request):
        """Store encrypted API key."""
        api_key = request.data.get("api_key")
        use_as_instance_default = bool(request.data.get("use_as_instance_default"))
        allow_other_users = bool(request.data.get("allow_other_users"))
        if not api_key:
            return Response(
                {"error": "api_key is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = AIService(request.user)
        provider_name = request.data.get("provider_name") or service.ai_auth.provider_name
        if use_as_instance_default:
            instance_default_key = AIService.get_instance_default_key()
            if instance_default_key and instance_default_key.owner_id not in (None, request.user.id):
                return Response(
                    {"error": "instance default key is managed by another user"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        service.ai_auth.provider_name = provider_name
        service.ai_auth.save(update_fields=["provider_name"])
        service.set_api_key(api_key)
        if use_as_instance_default:
            service.set_instance_default_api_key(
                api_key,
                provider_name=provider_name,
                allow_other_users=allow_other_users,
            )
        else:
            service.clear_instance_default_api_key_if_owned()

        return Response(
            {"status": "API key updated"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def remove_api_key(self, request):
        """Remove stored API key."""
        service = AIService(request.user)
        service.clear_api_key()
        service.clear_instance_default_api_key_if_owned()

        return Response(
            {"status": "API key removed"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def test_connection(self, request):
        provider = request.data.get("provider_name")
        api_key = request.data.get("api_key")

        if not provider:
            ai_auth = AIAuth.objects.filter(user=request.user).first()
            provider = ai_auth.provider_name if ai_auth else "openai"

        if not api_key:
            service = AIService(request.user)
            api_key = service.get_api_key()

        if not api_key:
            return Response(
                {"error": "api_key is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = AIService.test_connection(provider=provider, api_key=api_key)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "ok", **result},
            status=status.HTTP_200_OK,
        )
