"""Options chain helpers backed by yfinance."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import anyio
import pandas as pd  # type: ignore
import yfinance as yf  # type: ignore

from .common import YahooFinanceError, clean_value

logger = logging.getLogger(__name__)

_OPTION_FIELDS = (
    "contractSymbol",
    "lastTradeDate",
    "strike",
    "lastPrice",
    "bid",
    "ask",
    "change",
    "percentChange",
    "volume",
    "openInterest",
    "impliedVolatility",
    "inTheMoney",
    "contractSize",
    "expiration",
)


async def fetch_option_chain(
    symbol: str,
    *,
    expiration: Optional[str],
    contract_type: str,
    limit: Optional[int],
) -> Dict[str, Any]:
    symbol = (symbol or "").strip()
    if not symbol:
        raise YahooFinanceError("Symbol must be provided")

    contract_type_normalised = (contract_type or "both").lower()
    if contract_type_normalised not in {"calls", "puts", "both"}:
        raise YahooFinanceError("contract_type must be one of 'calls', 'puts', or 'both'")

    selected_expiration, expirations, calls, puts = await anyio.to_thread.run_sync(
        _load_option_chain,
        symbol.upper(),
        expiration,
    )

    limited_calls = _apply_limit(calls, limit)
    limited_puts = _apply_limit(puts, limit)

    contracts: Dict[str, List[Dict[str, Any]]] = {}
    if contract_type_normalised in {"calls", "both"}:
        contracts["calls"] = limited_calls
    if contract_type_normalised in {"puts", "both"}:
        contracts["puts"] = limited_puts

    if not contracts:
        raise YahooFinanceError("No option data returned for requested filters")

    return {
        "symbol": symbol.upper(),
        "expiration": selected_expiration,
        "contractType": contract_type_normalised,
        "availableExpirations": expirations,
        "counts": {key: len(value) for key, value in contracts.items()},
        "contracts": contracts,
        "source": "yfinance",
    }


def _load_option_chain(symbol: str, expiration: Optional[str]) -> Tuple[str, List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    ticker = yf.Ticker(symbol)

    expirations = list(getattr(ticker, "options", []) or [])
    if not expirations:
        raise YahooFinanceError(f"No expiration dates available for '{symbol}'")

    selected = expiration or expirations[0]
    if selected not in expirations:
        raise YahooFinanceError(
            f"Expiration '{selected}' not found. Available options: {', '.join(expirations)}"
        )

    chain = ticker.option_chain(selected)

    calls = _frame_to_records(chain.calls)
    puts = _frame_to_records(chain.puts)
    if not calls and not puts:
        raise YahooFinanceError(f"No option contracts returned for '{symbol}' expiring {selected}")

    return selected, expirations, calls, puts


def _frame_to_records(frame: Any) -> List[Dict[str, Any]]:
    if frame is None or not isinstance(frame, pd.DataFrame):
        return []
    records = []
    for row in frame.to_dict(orient="records"):
        cleaned = {field: clean_value(row.get(field)) for field in _OPTION_FIELDS if field in row}
        if cleaned:
            records.append(cleaned)
    return records


def _apply_limit(records: List[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    if limit is None:
        return records
    try:
        as_int = int(limit)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return records
    if as_int <= 0:
        return records
    return records[:as_int]
