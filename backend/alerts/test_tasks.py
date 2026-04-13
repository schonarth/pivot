import pytest
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone

from django.contrib.auth import get_user_model

from alerts.models import Alert, AlertTrigger
from alerts.tasks import evaluate_alerts_for_assets
from markets.models import Asset, AssetQuote
from portfolios.models import Portfolio

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="taskuser", password="pass")


@pytest.fixture
def asset(db):
    return Asset.objects.create(
        display_symbol="TSLA",
        provider_symbol="TSLA",
        name="Tesla Inc.",
        market="US",
        exchange="XNYS",
        currency="USD",
    )


@pytest.fixture
def portfolio(db, user):
    return Portfolio.objects.create(
        user=user,
        name="Test Portfolio",
        market="US",
        initial_capital=Decimal("10000"),
        current_cash=Decimal("10000"),
    )


@pytest.fixture
def quote(db, asset):
    return AssetQuote.objects.create(
        asset=asset,
        price=Decimal("200.00"),
        currency="USD",
        as_of=timezone.now(),
    )


@pytest.fixture
def make_alert(db, portfolio, asset):
    def _make(condition_type, threshold, **kwargs):
        return Alert.objects.create(
            portfolio=portfolio,
            asset=asset,
            condition_type=condition_type,
            threshold=Decimal(str(threshold)),
            notify_enabled=False,
            auto_trade_enabled=False,
            **kwargs,
        )
    return _make


@pytest.mark.django_db(transaction=True)
@patch("realtime.services.publish_event")
class TestEvaluateAlertsForAssetsTask:
    def test_price_above_alert_fires_via_task(self, mock_pub, make_alert, asset, quote):
        alert = make_alert("price_above", "150.00")
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "triggered"
        assert AlertTrigger.objects.filter(alert=alert).count() == 1

    def test_price_below_alert_fires_via_task(self, mock_pub, make_alert, asset, quote):
        alert = make_alert("price_below", "250.00")
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "triggered"
        assert AlertTrigger.objects.filter(alert=alert).count() == 1

    def test_price_above_alert_does_not_fire_when_price_below(self, mock_pub, make_alert, asset, quote):
        alert = make_alert("price_above", "250.00")
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "active"

    def test_price_below_alert_does_not_fire_when_price_above(self, mock_pub, make_alert, asset, quote):
        alert = make_alert("price_below", "150.00")
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "active"

    def test_skips_asset_with_no_quote(self, mock_pub, make_alert, asset):
        alert = make_alert("price_above", "100.00")
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "active"

    def test_skips_unknown_asset_id(self, mock_pub):
        import uuid
        evaluate_alerts_for_assets([str(uuid.uuid4())])

    def test_only_evaluates_active_alerts(self, mock_pub, make_alert, asset, quote):
        triggered = make_alert("price_above", "150.00", status="triggered")
        paused = make_alert("price_above", "150.00", status="paused")
        evaluate_alerts_for_assets([str(asset.id)])
        triggered.refresh_from_db()
        paused.refresh_from_db()
        assert triggered.status == "triggered"
        assert paused.status == "paused"
        assert AlertTrigger.objects.count() == 0

    def test_override_price_skips_alert_on_real_portfolio(self, mock_pub, make_alert, asset, portfolio, db):
        alert = make_alert("price_above", "150.00")
        AssetQuote.objects.all().delete()
        AssetQuote.objects.create(
            asset=asset,
            price=Decimal("180.00"),
            currency="USD",
            is_override=True,
            as_of=timezone.now(),
        )
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "active"
        assert AlertTrigger.objects.count() == 0

    def test_override_price_triggers_alert_on_simulating_portfolio(self, mock_pub, make_alert, asset, portfolio, db):
        portfolio.is_simulating = True
        portfolio.save()
        alert = make_alert("price_above", "150.00")
        AssetQuote.objects.all().delete()
        AssetQuote.objects.create(
            asset=asset,
            price=Decimal("180.00"),
            currency="USD",
            is_override=True,
            as_of=timezone.now(),
        )
        evaluate_alerts_for_assets([str(asset.id)])
        alert.refresh_from_db()
        assert alert.status == "triggered"
        assert AlertTrigger.objects.count() == 1
