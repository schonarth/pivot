from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from portfolios.models import Portfolio
from .models import Alert, AlertTrigger
from .serializers import AlertCreateSerializer, AlertSerializer, AlertTriggerSerializer


class AlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertSerializer

    def get_queryset(self):
        portfolio_id = self.kwargs.get("portfolio_pk")
        queryset = Alert.objects.filter(portfolio__user=self.request.user).select_related("asset").prefetch_related("triggers__trade")

        if portfolio_id:
            queryset = queryset.filter(portfolio_id=portfolio_id)

        return queryset

    def create(self, request, *args, **kwargs):
        portfolio_id = self.kwargs.get("portfolio_pk")
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

        input_serializer = AlertCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        from markets.models import Asset

        asset = get_object_or_404(Asset, id=input_serializer.validated_data["asset_id"])

        if asset.market != portfolio.market:
            return Response(
                {"error": {"code": "market_mismatch", "message": f"Asset market {asset.market} does not match portfolio market {portfolio.market}."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alert = Alert.objects.create(
            portfolio=portfolio,
            asset=asset,
            **{k: v for k, v in input_serializer.validated_data.items() if k != "asset_id"},
        )

        return Response(AlertSerializer(alert).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        alert = self.get_object()
        input_serializer = AlertCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        for key, value in input_serializer.validated_data.items():
            if key == "asset_id":
                from markets.models import Asset

                asset = get_object_or_404(Asset, id=value)
                alert.asset = asset
            else:
                setattr(alert, key, value)

        alert.save()
        return Response(AlertSerializer(alert).data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None, **kwargs):
        alert = self.get_object()
        if alert.status != "active":
            return Response(
                {"error": {"code": "invalid_status", "message": f"Cannot pause alert in {alert.status} status."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alert.status = "paused"
        alert.save(update_fields=["status", "updated_at"])
        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None, **kwargs):
        alert = self.get_object()
        if alert.status != "paused":
            return Response(
                {"error": {"code": "invalid_status", "message": f"Cannot resume alert in {alert.status} status."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alert.status = "active"
        alert.save(update_fields=["status", "updated_at"])
        return Response(AlertSerializer(alert).data)


class AlertTriggerListView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertTriggerSerializer

    def get_queryset(self):
        return AlertTrigger.objects.filter(alert__portfolio__user=self.request.user)