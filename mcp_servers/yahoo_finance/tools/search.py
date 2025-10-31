"""Entity search helpers backed by yfinance."""

from __future__ import annotations

import logging
from typing import Any, Dict

import anyio
import yfinance as yf  # type: ignore

from .common import YahooFinanceError, clean_mapping

logger = logging.getLogger(__name__)


async def search_entities(query: str, *, limit: int) -> Dict[str, Any]:
    query = (query or "").strip()
    if not query:
        raise YahooFinanceError("Query must be provided")

    raw_results = await anyio.to_thread.run_sync(_search, query)
    items = _normalise_results(raw_results, limit)
    return {
        "query": query,
        "count": len(items),
        "results": items,
        "source": "yfinance",
    }


def _search(query: str) -> Any:
    logger.debug("Searching tickers for query=%s", query)
    try:
        return yf.search_tickers(query)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - compatibility with older yfinance versions
        utils = getattr(yf, "utils", None)
        if utils is None or not hasattr(utils, "search"):
            raise YahooFinanceError("Current yfinance version does not expose search functionality")
        return utils.search(query)


def _normalise_results(raw: Any, limit: int) -> list[Dict[str, Any]]:
    if raw is None:
        return []

    if isinstance(raw, dict):
        values = list(raw.values())
    elif isinstance(raw, (list, tuple)):
        values = list(raw)
    else:
        values = [raw]

    normalised = [clean_mapping(item) if isinstance(item, dict) else {"value": item} for item in values]
    if limit > 0:
        normalised = normalised[:limit]
    return normalised
