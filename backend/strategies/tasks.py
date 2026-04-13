import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import BacktestScenario
from .engine import BacktestEngine

logger = logging.getLogger("paper_trader.strategies")


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
            scenario.result = result
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
