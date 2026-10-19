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
        from trading.models import Position

        portfolio = self.strategy_instance.portfolio
        positions = Position.objects.filter(
            portfolio=portfolio
        ).select_related("asset")

        if not positions.exists():
            logger.warning(f"No open positions for backtest on {portfolio.name}")
            return None

        from portfolios.services import get_fee_rate

        fee_rate = get_fee_rate(portfolio.market)
        simulated_trades = []
        pnl_by_date: dict = {}
        closed_pnls = []

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

            signals = self._evaluate_conditions(asset, df)
            trades, curve, closed = self._simulate(signals, df, Decimal(position.quantity), fee_rate)
            simulated_trades.extend(trades)
            closed_pnls.extend(closed)
            for day, value in curve.items():
                pnl_by_date[day] = pnl_by_date.get(day, Decimal("0")) + value

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

        curve = [pnl_by_date[d] for d in sorted(pnl_by_date)]
        total_pnl = curve[-1] if curve else Decimal("0")
        winning = len([p for p in closed_pnls if p > 0])
        win_rate = Decimal(winning * 100) / Decimal(len(closed_pnls)) if closed_pnls else Decimal("0")

        return {
            "trades": simulated_trades,
            "total_trades": len(simulated_trades),
            "buy_count": len([t for t in simulated_trades if t["action"] == "BUY"]),
            "sell_count": len([t for t in simulated_trades if t["action"] == "SELL"]),
            "total_pnl": total_pnl,
            "max_drawdown": self._calculate_max_drawdown(curve),
            "win_rate": win_rate,
        }

    @staticmethod
    def _simulate(signals, df, quantity: Decimal, fee_rate: Decimal):
        """Turn signals into fills with a long-only, one-lot position.

        A signal is computed on a bar's close, so it fills at the NEXT bar's open (no look-ahead); a signal on the
        last bar does not fill. BUY only opens from flat, SELL only closes an open lot (repeated signals are ignored).
        Fees use the portfolio market's fee rate on both sides. Returns (fills, mark-to-market P&L per bar date,
        P&L of each closed round trip); an open lot at the end is marked at the last close.
        """
        by_signal_date = {}
        for sig in signals:
            by_signal_date.setdefault(sig["date"], sig)  # one signal per bar
        dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
        opens = [Decimal(str(v)) for v in df["open"]]
        closes = [Decimal(str(v)) for v in df["close"]]

        fills, curve, closed = [], {}, []
        realized = Decimal("0")
        entry_cost = None  # cash paid for the open lot, fees included
        for i, day in enumerate(dates):
            if i > 0 and dates[i - 1] in by_signal_date:
                action = by_signal_date[dates[i - 1]]["action"]
                price = opens[i]
                fee = price * quantity * fee_rate
                if action == "BUY" and entry_cost is None:
                    entry_cost = price * quantity + fee
                    fills.append({"date": day, "action": "BUY", "price": float(price), "pnl": 0.0})
                elif action == "SELL" and entry_cost is not None:
                    trip = price * quantity - fee - entry_cost
                    realized += trip
                    closed.append(trip)
                    entry_cost = None
                    fills.append({"date": day, "action": "SELL", "price": float(price), "pnl": float(trip)})
            marked = closes[i] * quantity - entry_cost if entry_cost is not None else Decimal("0")
            curve[day] = realized + marked
        return fills, curve, closed

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
        df["bb_upper"] = bb.iloc[:, 2]
        df["bb_lower"] = bb.iloc[:, 0]

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
        try:
            import pandas_ta as ta
        except ImportError:
            return []

        conditions = self.rule.conditions
        trades = []

        for i in range(1, len(df)):
            rsi = ta.rsi(df["close"].iloc[:i+1], length=14)
            ma_20 = ta.sma(df["close"].iloc[:i+1], length=20)
            ma_50 = ta.sma(df["close"].iloc[:i+1], length=50)

            curr_rsi = rsi.iloc[-1] if len(rsi) > 0 and pd.notna(rsi.iloc[-1]) else None
            curr_20 = ma_20.iloc[-1] if len(ma_20) > 0 and pd.notna(ma_20.iloc[-1]) else None
            curr_50 = ma_50.iloc[-1] if len(ma_50) > 0 and pd.notna(ma_50.iloc[-1]) else None
            close = df.iloc[i]["close"]

            buy_signal = False
            sell_signal = False

            if curr_rsi is not None and curr_20 is not None and curr_50 is not None:
                buy_signal = curr_rsi < 30 and curr_20 > curr_50
                sell_signal = curr_rsi > 70 and curr_20 < curr_50

            if buy_signal:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "BUY",
                    "price": float(close),
                    "pnl": 0,
                })
            elif sell_signal:
                trades.append({
                    "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
                    "action": "SELL",
                    "price": float(close),
                    "pnl": 0,
                })

        return trades

    def _calculate_max_drawdown(self, pnl_curve) -> Decimal:
        """Largest peak-to-trough fall of the cumulative P&L curve, in portfolio currency."""
        peak = Decimal("0")
        max_drawdown = Decimal("0")
        for value in pnl_curve:
            peak = max(peak, value)
            max_drawdown = max(max_drawdown, peak - value)
        return max_drawdown
