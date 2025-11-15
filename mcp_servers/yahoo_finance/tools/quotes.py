"""Quote retrieval helpers backed by yfinance."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import anyio
import yfinance as yf  # type: ignore

from .common import YahooFinanceError, clean_mapping, clean_value


logger = logging.getLogger(__name__)


_FAST_KEY_MAPPING = {
    "last_price": "regularMarketPrice",
    "previous_close": "regularMarketPreviousClose",
    "open": "regularMarketOpen",
    "day_low": "regularMarketDayLow",
    "day_high": "regularMarketDayHigh",
    "fifty_two_week_low": "fiftyTwoWeekLow",
    "fifty_two_week_high": "fiftyTwoWeekHigh",
    "ten_day_average_volume": "tenDayAverageVolume",
    "three_month_average_volume": "threeMonthAverageVolume",
    "market_cap": "marketCap",
    "regular_market_previous_close": "regularMarketPreviousClose",
    "regular_market_open": "regularMarketOpen",
    "regular_market_day_low": "regularMarketDayLow",
    "regular_market_day_high": "regularMarketDayHigh",
    "regular_market_time": "regularMarketTime",
}

_INFO_KEYS = {
    "shortName",
    "longName",
    "quoteType",
    "currency",
    "marketState",
    "exchange",
    "fullExchangeName",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",
    "regularMarketVolume",
    "regularMarketDayRange",
    "regularMarketChange",
    "regularMarketChangePercent",
}


async def fetch_quote(symbol: str, *, region: Optional[str] = None) -> Dict[str, Any]:
    """Return a curated quote payload for ``symbol`` using yfinance."""

    symbol = (symbol or "").strip()
    if not symbol:
        raise YahooFinanceError("Symbol must be provided")

    data = await anyio.to_thread.run_sync(_load_quote_data, symbol.upper())
    cleaned_fast = {clean_key: clean_value(data["fast"].get(raw_key)) for raw_key, clean_key in _FAST_KEY_MAPPING.items() if raw_key in data["fast"]}

    info_section = {
        key: clean_value(data["info"].get(key)) for key in _INFO_KEYS if key in data["info"]
    }

    payload: Dict[str, Any] = {
        "symbol": symbol.upper(),
        "region": region,
        "source": "yfinance",
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "quote": cleaned_fast,
        "profile": info_section,
    }

    # Provide backward-compatible top-level shorthands for common fields
    for alias, target in (
        ("regularMarketPrice", "regularMarketPrice"),
        ("regularMarketPreviousClose", "regularMarketPreviousClose"),
        ("regularMarketOpen", "regularMarketOpen"),
        ("regularMarketDayHigh", "regularMarketDayHigh"),
        ("regularMarketDayLow", "regularMarketDayLow"),
        ("marketCap", "marketCap"),
    ):
        if target in payload["quote"] and payload["quote"][target] is not None:
            payload[alias] = payload["quote"][target]

    if not any(value is not None for value in payload["quote"].values()):
        raise YahooFinanceError(f"No quote data returned for symbol '{symbol}'")

    return payload


def _load_quote_data(symbol: str) -> Dict[str, Dict[str, Any]]:
    ticker = yf.Ticker(symbol)

    fast_data: Dict[str, Any] = {}
    fast = getattr(ticker, "fast_info", None)
    if fast:
        if hasattr(fast, "as_dict"):
            fast_data = fast.as_dict()  # type: ignore[attr-defined]
        elif isinstance(fast, dict):
            fast_data = fast
        else:
            fast_data = {name: getattr(fast, name) for name in dir(fast) if not name.startswith("_")}

    info_data: Dict[str, Any] = {}
    try:
        raw_info = getattr(ticker, "info", {}) or {}
        if isinstance(raw_info, dict):
            info_data = clean_mapping(raw_info)
    except Exception as exc:  # pragma: no cover - yfinance may raise when info unavailable
        logger.debug("Profile lookup failed for %s: %s", symbol, exc)

    return {"fast": clean_mapping(fast_data), "info": info_data}
