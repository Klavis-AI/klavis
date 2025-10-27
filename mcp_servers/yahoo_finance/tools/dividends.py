"""Dividend history helpers backed by yfinance."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import anyio
import pandas as pd  # type: ignore
import yfinance as yf  # type: ignore

from .common import YahooFinanceError, clean_value

logger = logging.getLogger(__name__)


async def fetch_dividends(
    symbol: str,
    *,
    period_start: Optional[str],
    period_end: Optional[str],
    limit: Optional[int],
) -> Dict[str, Any]:
    symbol = (symbol or "").strip()
    if not symbol:
        raise YahooFinanceError("Symbol must be provided")

    series = await anyio.to_thread.run_sync(_load_dividends, symbol.upper())
    if series is None or series.empty:
        raise YahooFinanceError(f"No dividend data returned for '{symbol.upper()}'")

    windowed = _apply_window(series, period_start, period_end)
    if windowed.empty:
        raise YahooFinanceError("No dividends found in the requested window")

    records = _series_to_records(windowed, value_key="amount")
    limited = _apply_limit(records, limit)

    return {
        "symbol": symbol.upper(),
        "start": period_start,
        "end": period_end,
        "count": len(limited),
        "total": len(records),
        "results": limited,
        "source": "yfinance",
    }


def _load_dividends(symbol: str) -> pd.Series:
    ticker = yf.Ticker(symbol)
    data = getattr(ticker, "dividends", None)
    if data is None:
        return pd.Series(dtype="float64")
    if isinstance(data, pd.Series):
        return data
    return pd.Series(data)


def _apply_window(series: pd.Series, period_start: Optional[str], period_end: Optional[str]) -> pd.Series:
    start = _parse_timestamp(period_start) if period_start else None
    end = _parse_timestamp(period_end) if period_end else None

    if start and end and start > end:
        raise YahooFinanceError("period_start must be before period_end")

    if start:
        series = series[series.index >= start]
    if end:
        series = series[series.index <= end]
    return series


def _parse_timestamp(raw: str) -> pd.Timestamp:
    try:
        return pd.Timestamp(raw)
    except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
        raise YahooFinanceError(f"Invalid date value '{raw}'") from exc


def _series_to_records(series: pd.Series, *, value_key: str) -> list[Dict[str, Any]]:
    records: list[Dict[str, Any]] = []
    for index, value in series.items():
        records.append({
            "date": clean_value(index),
            value_key: clean_value(value),
        })
    return records


def _apply_limit(records: list[Dict[str, Any]], limit: Optional[int]) -> list[Dict[str, Any]]:
    if limit is None:
        return records
    try:
        as_int = int(limit)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return records
    if as_int <= 0:
        return records
    return records[:as_int]
