import pytest
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model

from alerts.models import Alert, AlertTrigger
from alerts.services import evaluate_alert
from markets.models import Asset
from portfolios.models import Portfolio

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.fixture
def asset(db):
    return Asset.objects.create(
        display_symbol="AAPL",
        provider_symbol="AAPL",
        name="Apple Inc.",
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
def make_alert(portfolio, asset):
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


@patch("realtime.services.publish_event")
class TestEvaluateAlertPriceAbove:
    def test_fires_when_price_exceeds_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        trigger = evaluate_alert(alert, Decimal("100.01"))
        assert trigger is not None
        assert AlertTrigger.objects.filter(alert=alert).count() == 1
        alert.refresh_from_db()
        assert alert.status == "triggered"
        assert alert.triggered_at is not None

    def test_fires_well_above_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        trigger = evaluate_alert(alert, Decimal("200.00"))
        assert trigger is not None

    def test_does_not_fire_at_exact_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        trigger = evaluate_alert(alert, Decimal("100.00"))
        assert trigger is None
        alert.refresh_from_db()
        assert alert.status == "active"

    def test_does_not_fire_below_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        trigger = evaluate_alert(alert, Decimal("99.99"))
        assert trigger is None
        alert.refresh_from_db()
        assert alert.status == "active"


@patch("realtime.services.publish_event")
class TestEvaluateAlertPriceBelow:
    def test_fires_when_price_under_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_below", "50.00")
        trigger = evaluate_alert(alert, Decimal("49.99"))
        assert trigger is not None
        assert AlertTrigger.objects.filter(alert=alert).count() == 1
        alert.refresh_from_db()
        assert alert.status == "triggered"
        assert alert.triggered_at is not None

    def test_fires_well_below_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_below", "50.00")
        trigger = evaluate_alert(alert, Decimal("1.00"))
        assert trigger is not None

    def test_does_not_fire_at_exact_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_below", "50.00")
        trigger = evaluate_alert(alert, Decimal("50.00"))
        assert trigger is None
        alert.refresh_from_db()
        assert alert.status == "active"

    def test_does_not_fire_above_threshold(self, mock_pub, make_alert):
        alert = make_alert("price_below", "50.00")
        trigger = evaluate_alert(alert, Decimal("50.01"))
        assert trigger is None
        alert.refresh_from_db()
        assert alert.status == "active"


@patch("realtime.services.publish_event")
class TestEvaluateAlertTriggerRecord:
    def test_trigger_records_price_and_condition(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        trigger = evaluate_alert(alert, Decimal("150.00"))
        assert trigger.triggered_price == Decimal("150.00")
        assert trigger.details["condition_type"] == "price_above"
        assert trigger.details["threshold"] == "100.00"

    def test_publishes_event_on_trigger(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        evaluate_alert(alert, Decimal("101.00"))
        mock_pub.assert_called_once()
        channel, event_type, _ = mock_pub.call_args[0]
        assert channel == f"portfolio_{alert.portfolio_id}"
        assert event_type == "alert.triggered"

    def test_no_event_published_when_not_triggered(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        evaluate_alert(alert, Decimal("99.00"))
        mock_pub.assert_not_called()

    def test_last_evaluated_at_updated_regardless_of_match(self, mock_pub, make_alert):
        alert = make_alert("price_above", "100.00")
        evaluate_alert(alert, Decimal("50.00"))
        alert.refresh_from_db()
        assert alert.last_evaluated_at is not None
