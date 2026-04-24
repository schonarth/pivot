from collections import deque
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from alerts.models import Alert
from markets.models import Asset, AssetQuote
from markets import tasks as market_tasks
from portfolios.models import Portfolio, PortfolioWatchMembership
from trading.models import Position


User = get_user_model()


@pytest.fixture(autouse=True)
def reset_untracked_price_refresh_state():
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["seeded_for"] = None
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["pending"] = deque()
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["failed"] = set()
    yield
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["seeded_for"] = None
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["pending"] = deque()
    market_tasks.UNTRACKED_PRICE_REFRESH_STATE["failed"] = set()


def _create_user_and_portfolio(symbol: str):
    user = User.objects.create_user(username=f"{symbol.lower()}-user", email=f"{symbol.lower()}@test.com", password="testpass123")
    portfolio = Portfolio.objects.create(
        user=user,
        name=f"{symbol} Portfolio",
        market="US",
        initial_capital=Decimal("10000.00"),
        current_cash=Decimal("10000.00"),
    )
    return user, portfolio


def _create_asset(symbol: str):
    return Asset.objects.create(
        display_symbol=symbol,
        provider_symbol=symbol,
        name=f"{symbol} Corp",
        market="US",
        exchange="XNYS",
        currency="USD",
    )


def _set_quote_age(quote: AssetQuote, hours: int):
    AssetQuote.objects.filter(pk=quote.pk).update(fetched_at=timezone.now() - timedelta(hours=hours))


@pytest.mark.django_db
def test_fetch_market_prices_prioritizes_held_then_watched_then_alerts():
    _, held_portfolio = _create_user_and_portfolio("held")
    _, watched_portfolio = _create_user_and_portfolio("watch")
    _, alert_portfolio = _create_user_and_portfolio("alert")

    held_asset = _create_asset("HELD")
    watched_asset = _create_asset("WATCH")
    alert_asset = _create_asset("ALERT")

    Position.objects.create(
        portfolio=held_portfolio,
        asset=held_asset,
        quantity=Decimal("1.00"),
        average_cost=Decimal("100.00"),
    )
    PortfolioWatchMembership.objects.create(portfolio=watched_portfolio, asset=watched_asset)
    Alert.objects.create(
        portfolio=alert_portfolio,
        asset=alert_asset,
        condition_type="price_above",
        threshold=Decimal("150.00"),
        notify_enabled=False,
        auto_trade_enabled=False,
        status="active",
    )

    with patch("markets.services.is_market_open", return_value=True), patch(
        "markets.quote_provider.refresh_asset_quote",
        return_value=object(),
    ) as refresh_quote, patch("realtime.services.publish_event") as publish_event, patch(
        "alerts.tasks.evaluate_alerts_for_assets.delay"
    ) as evaluate_alerts:
        market_tasks.fetch_market_prices()

    assert [call.args[0] for call in refresh_quote.call_args_list] == [
        str(held_asset.id),
        str(watched_asset.id),
        str(alert_asset.id),
    ]
    assert {call.args[0] for call in publish_event.call_args_list} == {
        f"portfolio_{held_portfolio.id}",
        f"portfolio_{watched_portfolio.id}",
    }
    evaluate_alerts.assert_called_once()


@pytest.mark.django_db
def test_refresh_untracked_asset_prices_batches_old_assets_and_excludes_failures_for_the_day():
    _, held_portfolio = _create_user_and_portfolio("held")
    _, watched_portfolio = _create_user_and_portfolio("watch")

    old_one = _create_asset("OLD1")
    old_two = _create_asset("OLD2")
    old_three = _create_asset("OLD3")
    recent = _create_asset("RECENT")
    held_asset = _create_asset("HELD2")
    watched_asset = _create_asset("WATCH2")

    _set_quote_age(AssetQuote.objects.create(asset=old_one, price=Decimal("100.00"), currency="USD", as_of=timezone.now()), 30)
    _set_quote_age(AssetQuote.objects.create(asset=old_two, price=Decimal("100.00"), currency="USD", as_of=timezone.now()), 29)
    _set_quote_age(AssetQuote.objects.create(asset=old_three, price=Decimal("100.00"), currency="USD", as_of=timezone.now()), 28)
    _set_quote_age(AssetQuote.objects.create(asset=recent, price=Decimal("100.00"), currency="USD", as_of=timezone.now()), 2)

    Position.objects.create(
        portfolio=held_portfolio,
        asset=held_asset,
        quantity=Decimal("1.00"),
        average_cost=Decimal("100.00"),
    )
    PortfolioWatchMembership.objects.create(portfolio=watched_portfolio, asset=watched_asset)

    with patch.object(market_tasks, "UNTRACKED_PRICE_REFRESH_BATCH_SIZE", 2), patch(
        "markets.quote_provider.refresh_asset_quote",
        side_effect=[None, object(), object()],
    ) as refresh_quote:
        assert market_tasks.refresh_untracked_asset_prices() == 1
        assert market_tasks.refresh_untracked_asset_prices() == 1

    assert [call.args[0] for call in refresh_quote.call_args_list] == [
        str(old_one.id),
        str(old_two.id),
        str(old_three.id),
    ]
    assert str(old_one.id) in market_tasks.UNTRACKED_PRICE_REFRESH_STATE["failed"]
    assert str(recent.id) not in {call.args[0] for call in refresh_quote.call_args_list}
    assert str(held_asset.id) not in {call.args[0] for call in refresh_quote.call_args_list}
    assert str(watched_asset.id) not in {call.args[0] for call in refresh_quote.call_args_list}
