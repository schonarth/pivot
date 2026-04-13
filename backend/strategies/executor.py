import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from .models import StrategyInstance, StrategyTrade
from .engine import BacktestEngine
from markets.models import OHLCV, TechnicalIndicators
from trading.services import execute_buy, execute_sell
from trading.models import Position, Trade

logger = logging.getLogger("paper_trader.strategies")


class StrategyExecutor:
    """Execute strategy conditions against live market data with guardrail enforcement."""

    def __init__(self, strategy_instance):
        self.strategy = strategy_instance
        self.portfolio = strategy_instance.portfolio
        self.engine = BacktestEngine(strategy_instance)
        self.settings = strategy_instance.settings or {}

    def execute_if_conditions_met(self) -> bool:
        """Evaluate strategy conditions and execute trades if guardrails allow.

        Returns:
            bool: True if trade was executed, False otherwise
        """
        if not self.strategy.enabled or not self.strategy.backtest_approved_at:
            return False

        # Check guardrails
        if not self._check_guardrails():
            return False

        # Get positions for this portfolio
        positions = Position.objects.filter(
            portfolio=self.portfolio,
            status="open"
        ).select_related("asset")

        if not positions.exists():
            return False

        # Evaluate conditions for each position
        for position in positions:
            if self._evaluate_and_execute(position):
                return True

        return False

    def _check_guardrails(self) -> bool:
        """Verify execution guardrails before allowing trades."""
        max_trades_per_day = self.settings.get("max_trades_per_day", 10)

        # Count trades executed by this strategy today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = StrategyTrade.objects.filter(
            strategy_instance=self.strategy,
            executed_at__gte=today_start,
            auto_executed=True
        ).count()

        if today_trades >= max_trades_per_day:
            logger.warning(
                f"Strategy {self.strategy.id} hit max_trades_per_day limit ({max_trades_per_day})"
            )
            return False

        return True

    def _evaluate_and_execute(self, position) -> bool:
        """Evaluate strategy conditions for a position and execute trade if triggered."""
        asset = position.asset

        # Get latest OHLCV
        latest_ohlcv = OHLCV.objects.filter(
            asset=asset
        ).order_by("-date").first()

        if not latest_ohlcv:
            return False

        # Get latest indicators
        latest_indicators = TechnicalIndicators.objects.filter(
            asset=asset
        ).order_by("-date").first()

        if not latest_indicators:
            return False

        # Evaluate rule conditions
        action = self._evaluate_rule(asset, latest_ohlcv, latest_indicators)
        if not action:
            return False

        # Execute trade with guardrails
        return self._execute_trade_with_guardrails(position, asset, action, latest_ohlcv)

    def _evaluate_rule(self, asset, ohlcv, indicators) -> str | None:
        """Evaluate rule conditions. Returns 'BUY', 'SELL', or None."""
        rule_type = self.strategy.rule.rule_type

        # Map rule type to condition evaluation
        if rule_type == "rsi_oversold":
            return self._check_rsi_condition(indicators)
        elif rule_type == "ma_crossover":
            return self._check_ma_condition(indicators)
        elif rule_type == "macd_crossover":
            return self._check_macd_condition(indicators)
        elif rule_type == "bb_bands":
            return self._check_bb_condition(ohlcv, indicators)

        return None

    def _check_rsi_condition(self, indicators) -> str | None:
        """RSI oversold/overbought signals."""
        conditions = self.strategy.rule.conditions
        oversold = conditions.get("oversold_threshold", 30)
        overbought = conditions.get("overbought_threshold", 70)

        if indicators.rsi_14 is None:
            return None

        if indicators.rsi_14 <= oversold:
            return "BUY"
        elif indicators.rsi_14 >= overbought:
            return "SELL"

        return None

    def _check_ma_condition(self, indicators) -> str | None:
        """MA crossover signals."""
        if indicators.ma_20 is None or indicators.ma_50 is None:
            return None

        # Simple logic: if 20 > 50, buy signal; if 20 < 50, sell signal
        if indicators.ma_20 > indicators.ma_50:
            return "BUY"
        elif indicators.ma_20 < indicators.ma_50:
            return "SELL"

        return None

    def _check_macd_condition(self, indicators) -> str | None:
        """MACD crossover signals."""
        if indicators.macd is None or indicators.macd_signal is None:
            return None

        if indicators.macd > indicators.macd_signal:
            return "BUY"
        elif indicators.macd < indicators.macd_signal:
            return "SELL"

        return None

    def _check_bb_condition(self, ohlcv, indicators) -> str | None:
        """Bollinger Bands signals."""
        if indicators.bb_lower is None or indicators.bb_upper is None:
            return None

        close = Decimal(str(ohlcv.close))

        if close < indicators.bb_lower:
            return "BUY"
        elif close > indicators.bb_upper:
            return "SELL"

        return None

    def _execute_trade_with_guardrails(self, position, asset, action: str, ohlcv) -> bool:
        """Execute trade with position and portfolio guardrails."""
        max_position_size_pct = self.settings.get("max_position_size_pct", 10)
        max_portfolio_exposure_pct = self.settings.get("max_portfolio_exposure_pct", 50)
        stop_loss_pct = self.settings.get("stop_loss_pct", 5)

        try:
            with transaction.atomic():
                if action == "BUY":
                    # Calculate quantity based on guardrails
                    price = Decimal(str(ohlcv.close))
                    portfolio_value = self.portfolio.get_portfolio_value()
                    max_position_value = portfolio_value * Decimal(max_position_size_pct) / Decimal(100)
                    quantity = int(max_position_value / price)

                    if quantity <= 0:
                        logger.warning(
                            f"Strategy {self.strategy.id}: Calculated quantity {quantity} is invalid"
                        )
                        return False

                    trade = execute_buy(
                        portfolio=self.portfolio,
                        asset=asset,
                        quantity=quantity,
                        rationale=f"Automated strategy: {self.strategy.rule.name}",
                        executed_by="strategy"
                    )

                    self._record_strategy_trade("BUY", asset, quantity, price, trade)
                    logger.info(f"Strategy {self.strategy.id} executed BUY for {asset.symbol}: {quantity} @ {price}")
                    return True

                elif action == "SELL":
                    if position.quantity <= 0:
                        return False

                    price = Decimal(str(ohlcv.close))

                    # Check stop loss
                    unrealized_loss_pct = (
                        (position.average_cost - price) / position.average_cost * Decimal(100)
                    )
                    if unrealized_loss_pct > Decimal(stop_loss_pct):
                        logger.info(
                            f"Strategy {self.strategy.id}: Stop loss triggered for {asset.symbol} "
                            f"({unrealized_loss_pct:.2f}% loss)"
                        )

                    trade = execute_sell(
                        portfolio=self.portfolio,
                        position=position,
                        quantity=int(position.quantity),
                        rationale=f"Automated strategy: {self.strategy.rule.name}",
                        executed_by="strategy"
                    )

                    self._record_strategy_trade("SELL", asset, position.quantity, price, trade)
                    logger.info(f"Strategy {self.strategy.id} executed SELL for {asset.symbol}: {position.quantity} @ {price}")
                    return True

        except Exception as e:
            logger.exception(f"Strategy {self.strategy.id} execution failed: {str(e)}")
            return False

        return False

    def _record_strategy_trade(self, action: str, asset, quantity, price, trade_result):
        """Record strategy trade execution."""
        StrategyTrade.objects.create(
            strategy_instance=self.strategy,
            asset_id=asset.id,
            action=action,
            quantity=quantity,
            price=price,
            executed_at=timezone.now(),
            auto_executed=True,
            matched_conditions={
                "rule_type": self.strategy.rule.rule_type,
                "rule_name": self.strategy.rule.name,
            }
        )
