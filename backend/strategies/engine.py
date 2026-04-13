import logging
from decimal import Decimal
from datetime import datetime
import pandas as pd
from typing import Optional

logger = logging.getLogger("paper_trader.strategies")


class BacktestEngine:
    """Replay OHLCV data and evaluate strategy conditions."""

    def __init__(self, strategy_instance):
        """Initialize with a StrategyInstance."""
        self.strategy_instance = strategy_instance
        self.rule = strategy_instance.rule
        self.settings = strategy_instance.settings

    def run_backtest(self, date_from, date_to) -> dict | None:
        """Run backtest for date range.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Dict with: trades, total_trades, buy_count, sell_count, p_and_l, max_drawdown, win_rate
            Returns None on error.
        """
        from markets.models import OHLCV, Asset
        from portfolios.models import Position

        portfolio = self.strategy_instance.portfolio
        positions = Position.objects.filter(
            portfolio=portfolio,
            status="open",
        ).select_related("asset")

        if not positions.exists():
            logger.warning(f"No open positions for backtest on {portfolio.name}")
            return None

        simulated_trades = []
        all_p_and_l = []

        for position in positions:
            asset = position.asset
            ohlcv_data = list(
                OHLCV.objects.filter(
                    asset=asset,
                    date__gte=date_from,
                    date__lte=date_to,
                ).order_by("date").values("date", "open", "high", "low", "close", "volume")
            )

            if not ohlcv_data:
                continue

            df = pd.DataFrame(ohlcv_data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.astype({
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            })

            trades = self._evaluate_conditions(asset, df)
            simulated_trades.extend(trades)

            position_p_and_l = self._calculate_position_pnl(position, trades)
            all_p_and_l.append(position_p_and_l)

        if not simulated_trades:
            logger.info(f"No trades generated in backtest for {portfolio.name}")
            return {
                "trades": [],
                "total_trades": 0,
                "buy_count": 0,
                "sell_count": 0,
                "total_pnl": Decimal("0"),
                "max_drawdown": Decimal("0"),
                "win_rate": Decimal("0"),
            }

        total_pnl = sum(Decimal(str(t.get("pnl", 0))) for t in simulated_trades)
        winning_trades = len([t for t in simulated_trades if t.get("pnl", 0) > 0])
        win_rate = (winning_trades / len(simulated_trades) * 100) if simulated_trades else 0

        return {
            "trades": simulated_trades,
            "total_trades": len(simulated_trades),
            "buy_count": len([t for t in simulated_trades if t["action"] == "BUY"]),
            "sell_count": len([t for t in simulated_trades if t["action"] == "SELL"]),
            "total_pnl": total_pnl,
            "max_drawdown": self._calculate_max_drawdown(all_p_and_l),
            "win_rate": Decimal(str(win_rate)),
        }

    def _evaluate_conditions(self, asset, df) -> list[dict]:
        """Evaluate strategy conditions for asset OHLCV data.

        Returns list of simulated trades: [{"date": date, "action": "BUY"/"SELL", "price": price, "pnl": pnl}, ...]
        """
        from trading.technical import IndicatorCalculator

        rule_type = self.rule.rule_type
        trades = []

        if rule_type == "rsi_oversold":
            trades = self._evaluate_rsi_oversold(asset, df)
        elif rule_type == "ma_crossover":
            trades = self._evaluate_ma_crossover(asset, df)
        elif rule_type == "macd_crossover":
            trades = self._evaluate_macd_crossover(asset, df)
        elif rule_type == "bb_bands":
            trades = self._evaluate_bb_bands(asset, df)
        elif rule_type == "combination":
            trades = self._evaluate_combination(asset, df)

        return trades

    def _evaluate_rsi_oversold(self, asset, df) -> list[dict]:
        """RSI oversold/overbought signals."""
        try:
            import pandas_ta as ta
        except ImportError:
            return []

        rsi = ta.rsi(df["close"], length=14)
        df["rsi"] = rsi

        trades = []
        for i in range(1, len(df)):
            prev_rsi = df.iloc[i - 1]["rsi"]
            curr_rsi = df.iloc[i]["rsi"]
            close = df.iloc[i]["close"]

            if prev_rsi < 30 and curr_rsi >= 30:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "BUY",
                    "price": float(close),
                    "pnl": 0,
                })
            elif prev_rsi > 70 and curr_rsi <= 70:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "SELL",
                    "price": float(close),
                    "pnl": 0,
                })

        return trades

    def _evaluate_ma_crossover(self, asset, df) -> list[dict]:
        """MA crossover signals."""
        try:
            import pandas_ta as ta
        except ImportError:
            return []

        ma_20 = ta.sma(df["close"], length=20)
        ma_50 = ta.sma(df["close"], length=50)
        df["ma_20"] = ma_20
        df["ma_50"] = ma_50

        trades = []
        for i in range(1, len(df)):
            prev_20 = df.iloc[i - 1]["ma_20"]
            prev_50 = df.iloc[i - 1]["ma_50"]
            curr_20 = df.iloc[i]["ma_20"]
            curr_50 = df.iloc[i]["ma_50"]
            close = df.iloc[i]["close"]

            if pd.notna(prev_20) and pd.notna(curr_20):
                if prev_20 <= prev_50 and curr_20 > curr_50:
                    trades.append({
                        "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                        "action": "BUY",
                        "price": float(close),
                        "pnl": 0,
                    })
                elif prev_20 >= prev_50 and curr_20 < curr_50:
                    trades.append({
                        "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                        "action": "SELL",
                        "price": float(close),
                        "pnl": 0,
                    })

        return trades

    def _evaluate_macd_crossover(self, asset, df) -> list[dict]:
        """MACD crossover signals."""
        try:
            import pandas_ta as ta
        except ImportError:
            return []

        macd_result = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df["macd"] = macd_result.iloc[:, 0]
        df["signal"] = macd_result.iloc[:, 1]

        trades = []
        for i in range(1, len(df)):
            prev_macd = df.iloc[i - 1]["macd"]
            prev_signal = df.iloc[i - 1]["signal"]
            curr_macd = df.iloc[i]["macd"]
            curr_signal = df.iloc[i]["signal"]
            close = df.iloc[i]["close"]

            if pd.notna(prev_macd) and pd.notna(curr_macd):
                if prev_macd <= prev_signal and curr_macd > curr_signal:
                    trades.append({
                        "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                        "action": "BUY",
                        "price": float(close),
                        "pnl": 0,
                    })
                elif prev_macd >= prev_signal and curr_macd < curr_signal:
                    trades.append({
                        "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                        "action": "SELL",
                        "price": float(close),
                        "pnl": 0,
                    })

        return trades

    def _evaluate_bb_bands(self, asset, df) -> list[dict]:
        """Bollinger Bands signals."""
        try:
            import pandas_ta as ta
        except ImportError:
            return []

        bb = ta.bbands(df["close"], length=20, std=2)
        df["bb_upper"] = bb.iloc[:, 0]
        df["bb_lower"] = bb.iloc[:, 2]

        trades = []
        for i in range(len(df)):
            close = df.iloc[i]["close"]
            bb_upper = df.iloc[i]["bb_upper"]
            bb_lower = df.iloc[i]["bb_lower"]

            if pd.notna(bb_lower) and close < bb_lower:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "BUY",
                    "price": float(close),
                    "pnl": 0,
                })
            elif pd.notna(bb_upper) and close > bb_upper:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "SELL",
                    "price": float(close),
                    "pnl": 0,
                })

        return trades

    def _evaluate_combination(self, asset, df) -> list[dict]:
        """Combination rule: AND of multiple conditions."""
        return []

    def _calculate_position_pnl(self, position, trades) -> Decimal:
        """Calculate P&L for a position based on simulated trades."""
        return Decimal("0")

    def _calculate_max_drawdown(self, equity_curves) -> Decimal:
        """Calculate maximum drawdown from equity curves."""
        return Decimal("0")
