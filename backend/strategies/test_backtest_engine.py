import datetime as dt
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from conftest import PositionFactory
from markets.models import OHLCV
from strategies.engine import BacktestEngine
from strategies.models import StrategyInstance, StrategyRule


def _strategy(portfolio):
    rule = StrategyRule.objects.create(name="r", rule_type="bb_bands", description="", conditions={})
    return StrategyInstance.objects.create(
        portfolio=portfolio, rule=rule, enabled=True, backtest_approved_at=timezone.now(), settings={}
    )


def _bars(asset, prices):
    d0 = dt.date(2024, 1, 1)
    for i, p in enumerate(prices):
        OHLCV.objects.create(asset=asset, date=d0 + dt.timedelta(days=i), open=p, high=p, low=p, close=p, volume=1000)


def _run(position, signals, days):
    engine = BacktestEngine(_strategy(position.portfolio))
    with patch.object(BacktestEngine, "_evaluate_conditions", return_value=signals):
        return engine.run_backtest(dt.date(2024, 1, 1), dt.date(2024, 1, days))


@pytest.mark.django_db
def test_backtest_pnl_is_not_multiplied_by_the_number_of_sells():
    """BUY, SELL, SELL is one round trip of 10 shares, 100 -> 110: +100 (was +200)."""
    position = PositionFactory(quantity=10, average_cost=Decimal("50"))
    _bars(position.asset, [100, 100, 110, 120])
    signals = [
        {"date": "2024-01-01", "action": "BUY", "price": 100.0, "pnl": 0},
        {"date": "2024-01-02", "action": "SELL", "price": 100.0, "pnl": 0},
        {"date": "2024-01-03", "action": "SELL", "price": 110.0, "pnl": 0},
    ]
    result = _run(position, signals, 4)
    assert result["total_pnl"] == Decimal("100")
    assert result["total_trades"] == 2  # the second SELL is ignored: nothing is held any more
    assert result["win_rate"] == Decimal("100")  # one winning round trip; BUYs are not counted


@pytest.mark.django_db
def test_backtest_fills_at_next_bar_open_not_at_signal_close():
    """A signal computed on bar i's close fills at bar i+1's open (no look-ahead)."""
    position = PositionFactory(quantity=1, average_cost=Decimal("1"))
    _bars(position.asset, [100, 105, 120, 130])
    signals = [
        {"date": "2024-01-01", "action": "BUY", "price": 100.0, "pnl": 0},
        {"date": "2024-01-03", "action": "SELL", "price": 120.0, "pnl": 0},
    ]
    result = _run(position, signals, 4)
    assert [t["price"] for t in result["trades"]] == [105.0, 130.0]
    assert result["total_pnl"] == Decimal("25")


@pytest.mark.django_db
def test_backtest_max_drawdown_follows_the_pnl_curve():
    """Buy at 100, mark 120 then 90, sell at 110: peak +20, trough -10, drawdown 30."""
    position = PositionFactory(quantity=1, average_cost=Decimal("1"))
    _bars(position.asset, [100, 100, 120, 90, 110])
    signals = [
        {"date": "2024-01-01", "action": "BUY", "price": 100.0, "pnl": 0},
        {"date": "2024-01-04", "action": "SELL", "price": 90.0, "pnl": 0},
    ]
    result = _run(position, signals, 5)
    assert result["max_drawdown"] == Decimal("30")
    assert result["total_pnl"] == Decimal("10")
