from django.utils import timezone
from unittest.mock import patch

import pytest

from strategies.executor import StrategyExecutor
from strategies.models import StrategyInstance, StrategyRule


@pytest.mark.django_db
def test_strategy_executor_handles_positions_without_status_field(position):
    rule = StrategyRule.objects.create(
        name="RSI Oversold",
        rule_type="rsi_oversold",
        description="Test rule",
        conditions={},
    )
    strategy = StrategyInstance.objects.create(
        portfolio=position.portfolio,
        rule=rule,
        enabled=True,
        backtest_approved_at=timezone.now(),
        settings={},
    )

    executor = StrategyExecutor(strategy)

    with patch.object(StrategyExecutor, "_evaluate_and_execute", return_value=False) as evaluate:
        assert executor.execute_if_conditions_met() is False

    assert evaluate.called
