import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

import factory
from factory.django import DjangoModelFactory

from accounts.models import User
from markets.models import Asset, AssetQuote, MarketConfig
from portfolios.models import Portfolio, CashTransaction
from trading.models import Position, Trade
from alerts.models import Alert, AlertTrigger

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password = "testpass123"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.set_password(kwargs.pop("password", "testpass123"))
        obj.save()
        return obj


class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset

    display_symbol = factory.Sequence(lambda n: f"TST{n}")
    provider_symbol = factory.Sequence(lambda n: f"TST{n}")
    name = factory.Sequence(lambda n: f"Test Asset {n}")
    market = "US"
    exchange = "XNYS"
    currency = "USD"


class AssetQuoteFactory(DjangoModelFactory):
    class Meta:
        model = AssetQuote

    asset = factory.SubFactory(AssetFactory)
    price = Decimal("100.00")
    currency = "USD"
    fetched_at = timezone.now()
    as_of = timezone.now()


class MarketConfigFactory(DjangoModelFactory):
    class Meta:
        model = MarketConfig

    code = "US"
    name = "United States"
    currency = "USD"
    exchange = "XNYS"
    fee_rate = Decimal("0.00")


class PortfolioFactory(DjangoModelFactory):
    class Meta:
        model = Portfolio

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Portfolio {n}")
    market = "US"
    initial_capital = Decimal("10000.00")
    current_cash = Decimal("10000.00")


class PositionFactory(DjangoModelFactory):
    class Meta:
        model = Position

    portfolio = factory.SubFactory(PortfolioFactory)
    asset = factory.SubFactory(AssetFactory)
    quantity = Decimal("10.00")
    average_cost = Decimal("100.00")


class TradeFactory(DjangoModelFactory):
    class Meta:
        model = Trade

    portfolio = factory.SubFactory(PortfolioFactory)
    asset = factory.SubFactory(AssetFactory)
    action = "BUY"
    quantity = 10
    price = Decimal("100.00")
    gross_value = Decimal("1000.00")
    fees = Decimal("0.00")
    net_cash_impact = Decimal("1000.00")
    executed_by = "manual"
    rationale = "Test trade"


class AlertFactory(DjangoModelFactory):
    class Meta:
        model = Alert

    portfolio = factory.SubFactory(PortfolioFactory)
    asset = factory.SubFactory(AssetFactory)
    condition_type = "price_above"
    threshold = Decimal("150.00")
    status = "active"
    notify_enabled = False
    auto_trade_enabled = False


class AlertTriggerFactory(DjangoModelFactory):
    class Meta:
        model = AlertTrigger

    alert = factory.SubFactory(AlertFactory)
    triggered_price = Decimal("150.00")


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def user2(db):
    return UserFactory()


@pytest.fixture
def asset(db):
    return AssetFactory()


@pytest.fixture
def asset_with_quote(db):
    asset = AssetFactory()
    AssetQuoteFactory(asset=asset)
    return asset


@pytest.fixture
def portfolio(db, user):
    return PortfolioFactory(user=user)


@pytest.fixture
def portfolio_with_cash(db, user):
    return PortfolioFactory(user=user, current_cash=Decimal("50000.00"))


@pytest.fixture
def position(db, portfolio, asset):
    return PositionFactory(portfolio=portfolio, asset=asset)


@pytest.fixture
def position_with_quote(db, portfolio, asset_with_quote):
    return PositionFactory(portfolio=portfolio, asset=asset_with_quote)


@pytest.fixture
def trade(db, portfolio, asset):
    return TradeFactory(portfolio=portfolio, asset=asset)


@pytest.fixture
def alert(db, portfolio, asset):
    return AlertFactory(portfolio=portfolio, asset=asset)


@pytest.fixture
def authenticated_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    from rest_framework.test import APIClient

    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client
