"""Shared utilities for the Yahoo Finance MCP tools."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Any

try:
    import numpy as _np  # type: ignore
except Exception:  # pragma: no cover - numpy is an optional dependency of yfinance
    _np = None

try:
    import pandas as _pd  # type: ignore
except Exception:  # pragma: no cover - pandas is an optional dependency of yfinance
    _pd = None

__all__ = [
    "YahooFinanceError",
    "clean_value",
    "clean_mapping",
]


class YahooFinanceError(RuntimeError):
    """Domain specific exception for Yahoo Finance tooling."""


def clean_value(value: Any) -> Any:
    """Convert values returned from yfinance into JSON-serialisable primitives."""
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):  # pragma: no cover - defensive
            return None
        return value

    if isinstance(value, Decimal):
        return float(value)

    if _np is not None and isinstance(value, _np.generic):  # type: ignore[attr-defined]
        return value.item()

    if isinstance(value, datetime):
        return value.isoformat()

    if _pd is not None:
        if isinstance(value, _pd.Timestamp):  # type: ignore[attr-defined]
            return value.to_pydatetime().isoformat()
        if isinstance(value, _pd.Timedelta):  # type: ignore[attr-defined]
            return value.isoformat()

    if isinstance(value, dict):
        return clean_mapping(value)

    if isinstance(value, (list, tuple, set)):
        return [clean_value(item) for item in value]

    return value


def clean_mapping(mapping: dict[Any, Any]) -> dict[str, Any]:
    """Recursively clean mapping keys and values."""
    return {str(key): clean_value(val) for key, val in mapping.items()}
