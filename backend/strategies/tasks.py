import logging
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import BacktestScenario, StrategyInstance
from .engine import BacktestEngine
from .executor import StrategyExecutor

logger = logging.getLogger("paper_trader.strategies")


def serialize_result(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, dict):
        return {k: serialize_result(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_result(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@shared_task
def run_backtest_async(scenario_id):
    """Run backtest for a scenario asynchronously."""
    try:
        scenario = BacktestScenario.objects.get(id=scenario_id)
    except BacktestScenario.DoesNotExist:
        logger.error(f"BacktestScenario {scenario_id} not found")
        return

    try:
        with transaction.atomic():
            scenario.status = "running"
            scenario.save()

        engine = BacktestEngine(scenario.strategy_instance)
        result = engine.run_backtest(scenario.date_from, scenario.date_to)

        with transaction.atomic():
            scenario.result = serialize_result(result)
            scenario.status = "completed"
            scenario.completed_at = timezone.now()
            scenario.error_message = None
            scenario.save()

        logger.info(f"Backtest {scenario_id} completed successfully")
    except Exception as e:
        logger.exception(f"Backtest {scenario_id} failed with error: {str(e)}")
        with transaction.atomic():
            scenario.status = "failed"
            scenario.error_message = str(e)
            scenario.completed_at = timezone.now()
            scenario.save()


@shared_task
def evaluate_active_strategies():
    """Evaluate all active strategies and execute trades if conditions met.

    Runs periodically (e.g., every 5 minutes via Celery Beat).
    """
    active_strategies = StrategyInstance.objects.filter(
        enabled=True,
        backtest_approved_at__isnull=False
    ).select_related("portfolio", "rule")

    executed_count = 0
    failed_count = 0

    for strategy in active_strategies:
        try:
            executor = StrategyExecutor(strategy)
            if executor.execute_if_conditions_met():
                executed_count += 1
        except Exception as e:
            logger.exception(f"Error evaluating strategy {strategy.id}: {str(e)}")
            failed_count += 1

    logger.info(
        f"Strategy evaluation complete: {executed_count} executed, {failed_count} failed, "
        f"{active_strategies.count() - executed_count - failed_count} evaluated without execution"
    )

    return {"executed": executed_count, "failed": failed_count}
