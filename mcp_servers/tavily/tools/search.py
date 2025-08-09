import logging
from typing import Any, Dict

from .auth import get_tavily_client

logger = logging.getLogger(__name__)

_ALLOWED_KEYS = {
    "query",
    "search_depth",
    "topic",
    "days",
    "time_range",
    "start_date",
    "end_date",
    "max_results",
    "include_images",
    "include_image_descriptions",
    "include_raw_content",
    "include_domains",
    "exclude_domains",
    "country",
    "include_favicon",
}

_ALIASES = {
    "searchDepth": "search_depth",
    "timeRange": "time_range",
    "startDate": "start_date",
    "endDate": "end_date",
    "maxResults": "max_results",
    "includeImages": "include_images",
    "includeImageDescriptions": "include_image_descriptions",
    "includeRawContent": "include_raw_content",
    "includeDomains": "include_domains",
    "excludeDomains": "exclude_domains",
    "includeFavicon": "include_favicon",
}


def _coerce_bool(v: Any) -> Any:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return v


def _coerce_int(v: Any) -> Any:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s.isdigit():
            return int(s)
    return v


def _normalize_args(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # apply aliases
    norm: Dict[str, Any] = {}
    for k, v in arguments.items():
        key = _ALIASES.get(k, k)
        norm[key] = v

    # keep only allowed keys
    norm = {k: v for k, v in norm.items() if k in _ALLOWED_KEYS}

    # basic coercions
    if "max_results" in norm:
        norm["max_results"] = _coerce_int(norm["max_results"])

    for b in ("include_images", "include_image_descriptions", "include_raw_content", "include_favicon"):
        if b in norm:
            norm[b] = _coerce_bool(norm[b])

    return norm


def tavily_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Web Search (Tavily).
    Arguments: see server list_tools schema; this function expects a plain dict.
    Returns a dict as provided by Tavily's client.
    """
    client = get_tavily_client()
    params = _normalize_args(arguments)
    if "query" not in params or not params["query"]:
        raise RuntimeError("Parameter 'query' is required for tavily_search")
    logger.info(f"tavily_search: {params.get('query')}")
    return client.search(**params)
