import datetime as dt
from decimal import Decimal

import pytest
from django.utils import timezone

from conftest import AssetFactory, AssetQuoteFactory, PortfolioFactory, PositionFactory
from markets.models import OHLCV
from strategies.executor import StrategyExecutor
from strategies.models import StrategyInstance, StrategyRule
from trading.models import Position, Trade


def _strategy(portfolio):
    rule = StrategyRule.objects.create(name="r", rule_type="bb_bands", description="", conditions={})
    return StrategyInstance.objects.create(
        portfolio=portfolio, rule=rule, enabled=True, backtest_approved_at=timezone.now(), settings={}
    )


def _bar(asset, price):
    return OHLCV.objects.create(
        asset=asset, date=dt.date(2024, 1, 2), open=price, high=price, low=price, close=price, volume=1
    )


@pytest.mark.django_db
def test_strategy_sell_executes():
    """The executor called execute_sell(position=...), a TypeError that was swallowed: SELLs never happened."""
    asset = AssetFactory()
    AssetQuoteFactory(asset=asset, price=Decimal("100"))
    position = PositionFactory(asset=asset, quantity=10, average_cost=Decimal("90"))
    executor = StrategyExecutor(_strategy(position.portfolio))

    assert executor._execute_trade_with_guardrails(position, asset, "SELL", _bar(asset, 100)) is True
    assert not Position.objects.filter(pk=position.pk).exists()
    trade = Trade.objects.get(portfolio=position.portfolio, action="SELL")
    assert trade.executed_by == "autonomous"


@pytest.mark.django_db
def test_strategy_buy_executes_and_only_tops_up_to_the_target_size():
    """The executor called the non-existent Portfolio.get_portfolio_value(): BUYs never happened."""
    asset = AssetFactory()
    AssetQuoteFactory(asset=asset, price=Decimal("100"))
    portfolio = PortfolioFactory(current_cash=Decimal("9000"))
    position = PositionFactory(portfolio=portfolio, asset=asset, quantity=5, average_cost=Decimal("100"))
    executor = StrategyExecutor(_strategy(portfolio))  # default max_position_size_pct = 10 -> $950 of $9,500
    bar = _bar(asset, 100)

    assert executor._execute_trade_with_guardrails(position, asset, "BUY", bar) is True
    position.refresh_from_db()
    assert position.quantity == 9  # topped up to the 10% target, not 5 + 9
    # The signal repeats on the next run; the position is already at its target, so nothing is bought.
    assert executor._execute_trade_with_guardrails(position, asset, "BUY", bar) is False
    assert Trade.objects.filter(portfolio=portfolio, action="BUY").count() == 1
