"""Historical price retrieval backed by yfinance."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import anyio
import pandas as pd  # type: ignore
import yfinance as yf  # type: ignore

from .common import YahooFinanceError, clean_value

logger = logging.getLogger(__name__)


async def fetch_historical_prices(
    symbol: str,
    *,
    interval: str,
    range_label: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
    auto_adjust: bool = False,
) -> Dict[str, Any]:
    symbol = (symbol or "").strip()
    if not symbol:
        raise YahooFinanceError("Symbol must be provided")

    df = await anyio.to_thread.run_sync(
        _download_history,
        symbol.upper(),
        interval,
        range_label,
        period_start,
        period_end,
        auto_adjust,
    )

    if df.empty:
        raise YahooFinanceError(f"No historical data returned for '{symbol.upper()}'")

    df = df.reset_index()

    timestamp_column = None
    for candidate in ("Datetime", "Date", "index"):
        if candidate in df.columns:
            timestamp_column = candidate
            break

    if timestamp_column is None:
        raise YahooFinanceError("Unable to identify timestamp column in history frame")

    prices = []
    for row in df.to_dict(orient="records"):
        timestamp = row.pop(timestamp_column)
        prices.append(
            {
                "timestamp": clean_value(timestamp),
                "open": clean_value(row.get("Open")),
                "high": clean_value(row.get("High")),
                "low": clean_value(row.get("Low")),
                "close": clean_value(row.get("Close")),
                "volume": clean_value(row.get("Volume")),
            }
        )

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "range": range_label,
        "start": period_start,
        "end": period_end,
        "autoAdjust": auto_adjust,
        "prices": prices,
        "source": "yfinance",
    }


def _download_history(
    symbol: str,
    interval: str,
    range_label: Optional[str],
    period_start: Optional[str],
    period_end: Optional[str],
    auto_adjust: bool,
) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)

    kwargs: Dict[str, Any] = {"interval": interval, "auto_adjust": auto_adjust}
    if period_start and period_end:
        kwargs["start"] = period_start
        kwargs["end"] = period_end
    else:
        kwargs["period"] = range_label or "1mo"

    logger.debug("Downloading history for %s with %s", symbol, kwargs)
    frame = ticker.history(**kwargs)
    if not isinstance(frame, pd.DataFrame):  # pragma: no cover - defensive
        raise YahooFinanceError("Unexpected data structure returned from yfinance.history")

    return frame
