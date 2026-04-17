import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

logger = logging.getLogger("paper_trader.markets")


@dataclass(frozen=True)
class OhlcvFetchResult:
    source: str
    records: list[dict]


def is_valid_ohlcv_record(record: dict) -> bool:
    try:
        open_price = Decimal(str(record["open"]))
        high_price = Decimal(str(record["high"]))
        low_price = Decimal(str(record["low"]))
        close_price = Decimal(str(record["close"]))
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return False

    if min(open_price, high_price, low_price, close_price) <= 0:
        return False

    if high_price < max(open_price, close_price, low_price):
        return False

    if low_price > min(open_price, close_price, high_price):
        return False

    return True


def invalid_ohlcv_dates(records: list[dict]) -> list:
    return [record.get("date") for record in records if not is_valid_ohlcv_record(record)]


def fetch_yahoo_historical(
    provider_symbol: str,
    period: str = "5y",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict] | None:
    """Fetch historical OHLCV from Yahoo Finance.

    Args:
        provider_symbol: Ticker symbol (e.g., "AAPL")
        period: Period to fetch (default: 5 years). Supported: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'

    Returns:
        List of OHLCV dicts with keys: date, open, high, low, close, volume
        Returns None if fetch fails.
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(provider_symbol)
        history_kwargs = {}
        if start_date:
            history_kwargs["start"] = start_date.isoformat()
        if end_date:
            history_kwargs["end"] = (end_date + timedelta(days=1)).isoformat()
        if history_kwargs:
            hist = ticker.history(**history_kwargs)
        else:
            hist = ticker.history(period=period)

        if hist.empty:
            return None

        ohlcv_list = []
        for date, row in hist.iterrows():
            ohlcv_list.append({
                "date": date.date(),
                "open": Decimal(str(row["Open"])).quantize(Decimal("0.0001")),
                "high": Decimal(str(row["High"])).quantize(Decimal("0.0001")),
                "low": Decimal(str(row["Low"])).quantize(Decimal("0.0001")),
                "close": Decimal(str(row["Close"])).quantize(Decimal("0.0001")),
                "volume": int(row["Volume"]),
            })

        logger.info(f"Fetched {len(ohlcv_list)} OHLCV records for {provider_symbol} from Yahoo Finance")
        return ohlcv_list
    except Exception:
        logger.exception(f"Failed to fetch OHLCV for {provider_symbol} from Yahoo Finance")
        return None


def fetch_alpha_vantage_historical(
    provider_symbol: str,
    api_key: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict] | None:
    """Fetch historical OHLCV from Alpha Vantage (daily).

    Args:
        provider_symbol: Ticker symbol (e.g., "AAPL")
        api_key: Alpha Vantage API key

    Returns:
        List of OHLCV dicts with keys: date, open, high, low, close, volume
        Returns None if fetch fails or API key is invalid.
    """
    try:
        from alpha_vantage.timeseries import TimeSeries

        ts = TimeSeries(key=api_key, output_format="pandas")
        data, _meta_data = ts.get_daily_adjusted(symbol=provider_symbol, outputsize="full")

        if data.empty:
            return None

        if start_date:
            data = data[data.index.date >= start_date]
        if end_date:
            data = data[data.index.date <= end_date]

        if data.empty:
            return None

        ohlcv_list = []
        for date, row in data.iterrows():
            ohlcv_list.append({
                "date": date.date(),
                "open": Decimal(str(row["1. open"])).quantize(Decimal("0.0001")),
                "high": Decimal(str(row["2. high"])).quantize(Decimal("0.0001")),
                "low": Decimal(str(row["3. low"])).quantize(Decimal("0.0001")),
                "close": Decimal(str(row["4. close"])).quantize(Decimal("0.0001")),
                "volume": int(row["6. volume"]),
            })

        logger.info(f"Fetched {len(ohlcv_list)} OHLCV records for {provider_symbol} from Alpha Vantage")
        return ohlcv_list
    except Exception:
        logger.exception(f"Failed to fetch OHLCV for {provider_symbol} from Alpha Vantage")
        return None


def fetch_ohlcv_with_fallback(
    provider_symbol: str,
    alpha_vantage_key: Optional[str] = None,
    period: str = "5y",
    start_date: date | None = None,
    end_date: date | None = None,
) -> OhlcvFetchResult | None:
    """Fetch historical OHLCV with automatic provider fallback.

    Provider chain: Yahoo Finance → Alpha Vantage

    Args:
        provider_symbol: Ticker symbol
        alpha_vantage_key: Alpha Vantage API key (optional, used as fallback)
        period: Period to fetch (for Yahoo Finance)

    Returns:
        List of OHLCV dicts, or None if all providers fail.
    """
    ohlcv_list = fetch_yahoo_historical(
        provider_symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )
    if ohlcv_list:
        invalid_dates = invalid_ohlcv_dates(ohlcv_list)
        if not invalid_dates:
            return OhlcvFetchResult(source="yahoo_finance", records=ohlcv_list)
        logger.warning(
            "Discarding invalid Yahoo Finance OHLCV rows for %s: %s",
            provider_symbol,
            ", ".join(str(date) for date in invalid_dates[:5]),
        )

    if alpha_vantage_key:
        logger.info(f"Yahoo Finance failed for {provider_symbol}, trying Alpha Vantage")
        ohlcv_list = fetch_alpha_vantage_historical(
            provider_symbol,
            alpha_vantage_key,
            start_date=start_date,
            end_date=end_date,
        )
        if ohlcv_list:
            invalid_dates = invalid_ohlcv_dates(ohlcv_list)
            if not invalid_dates:
                return OhlcvFetchResult(source="alpha_vantage", records=ohlcv_list)
            logger.warning(
                "Discarding invalid Alpha Vantage OHLCV rows for %s: %s",
                provider_symbol,
                ", ".join(str(date) for date in invalid_dates[:5]),
            )

    logger.error(f"All OHLCV providers failed for {provider_symbol}")
    return None
