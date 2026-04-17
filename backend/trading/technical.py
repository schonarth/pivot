import logging
from decimal import Decimal
import pandas as pd
import numpy as np
from django.utils import timezone

logger = logging.getLogger("paper_trader.trading")


class IndicatorCalculator:
    """Calculate technical indicators using pandas-ta."""

    @staticmethod
    def calculate_indicators(asset_id: str, asset_symbol: str) -> dict | None:
        """Calculate all technical indicators for an asset using latest OHLCV data.

        Args:
            asset_id: Asset UUID
            asset_symbol: Display symbol for logging

        Returns:
            Dict with keys: date, rsi_14, macd, macd_signal, macd_histogram,
            ma_20, ma_50, ma_200, bb_upper, bb_middle, bb_lower, volume_20d_avg
            Returns None if insufficient data.
        """
        from markets.models import OHLCV

        try:
            import pandas_ta as ta
        except ImportError:
            logger.error("pandas-ta not installed; cannot calculate indicators")
            return None

        ohlcv_records = (
            OHLCV.objects.filter(asset_id=asset_id)
            .order_by("date")
            .values("date", "open", "high", "low", "close", "volume")
        )

        if not ohlcv_records:
            logger.warning(f"No OHLCV data for {asset_symbol}")
            return None

        ohlcv_list = list(ohlcv_records)
        if len(ohlcv_list) < 200:
            logger.debug(f"Insufficient OHLCV data for {asset_symbol} ({len(ohlcv_list)} < 200)")
            return None

        df = pd.DataFrame(ohlcv_list)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.astype({
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,
        })

        try:
            rsi = ta.rsi(df["close"], length=14)
            macd_result = ta.macd(df["close"], fast=12, slow=26, signal=9)
            ma_20 = ta.sma(df["close"], length=20)
            ma_50 = ta.sma(df["close"], length=50)
            ma_200 = ta.sma(df["close"], length=200)
            bb = ta.bbands(df["close"], length=20, std=2)
            volume_20d_avg = df["volume"].rolling(window=20).mean()

            last_idx = df.index[-1]
            return {
                "date": last_idx.date(),
                "rsi_14": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None,
                "macd": float(macd_result.iloc[-1, 0]) if pd.notna(macd_result.iloc[-1, 0]) else None,
                "macd_signal": float(macd_result.iloc[-1, 1]) if pd.notna(macd_result.iloc[-1, 1]) else None,
                "macd_histogram": float(macd_result.iloc[-1, 2]) if pd.notna(macd_result.iloc[-1, 2]) else None,
                "ma_20": float(ma_20.iloc[-1]) if pd.notna(ma_20.iloc[-1]) else None,
                "ma_50": float(ma_50.iloc[-1]) if pd.notna(ma_50.iloc[-1]) else None,
                "ma_200": float(ma_200.iloc[-1]) if pd.notna(ma_200.iloc[-1]) else None,
                "bb_upper": float(bb.iloc[-1, 2]) if pd.notna(bb.iloc[-1, 2]) else None,
                "bb_middle": float(bb.iloc[-1, 1]) if pd.notna(bb.iloc[-1, 1]) else None,
                "bb_lower": float(bb.iloc[-1, 0]) if pd.notna(bb.iloc[-1, 0]) else None,
                "volume_20d_avg": int(volume_20d_avg.iloc[-1]) if pd.notna(volume_20d_avg.iloc[-1]) else None,
            }
        except Exception:
            logger.exception(f"Failed to calculate indicators for {asset_symbol}")
            return None

    @staticmethod
    def ingest_indicators(asset_id: str, indicators: dict) -> bool:
        """Store calculated indicators in database.

        Args:
            asset_id: Asset UUID
            indicators: Dict from calculate_indicators

        Returns:
            True if ingested, False otherwise.
        """
        from markets.models import TechnicalIndicators

        if not indicators:
            return False

        try:
            TechnicalIndicators.objects.update_or_create(
                asset_id=asset_id,
                date=indicators["date"],
                defaults={
                    "rsi_14": Decimal(str(indicators["rsi_14"])) if indicators["rsi_14"] else None,
                    "macd": Decimal(str(indicators["macd"])).quantize(Decimal("0.0001")) if indicators["macd"] else None,
                    "macd_signal": Decimal(str(indicators["macd_signal"])).quantize(Decimal("0.0001")) if indicators["macd_signal"] else None,
                    "macd_histogram": Decimal(str(indicators["macd_histogram"])).quantize(Decimal("0.0001")) if indicators["macd_histogram"] else None,
                    "ma_20": Decimal(str(indicators["ma_20"])).quantize(Decimal("0.0001")) if indicators["ma_20"] else None,
                    "ma_50": Decimal(str(indicators["ma_50"])).quantize(Decimal("0.0001")) if indicators["ma_50"] else None,
                    "ma_200": Decimal(str(indicators["ma_200"])).quantize(Decimal("0.0001")) if indicators["ma_200"] else None,
                    "bb_upper": Decimal(str(indicators["bb_upper"])).quantize(Decimal("0.0001")) if indicators["bb_upper"] else None,
                    "bb_middle": Decimal(str(indicators["bb_middle"])).quantize(Decimal("0.0001")) if indicators["bb_middle"] else None,
                    "bb_lower": Decimal(str(indicators["bb_lower"])).quantize(Decimal("0.0001")) if indicators["bb_lower"] else None,
                    "volume_20d_avg": indicators["volume_20d_avg"],
                },
            )
            return True
        except Exception:
            logger.exception(f"Failed to ingest indicators for asset {asset_id}")
            return False
