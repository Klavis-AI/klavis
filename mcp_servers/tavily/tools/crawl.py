import logging
from typing import Any, Dict, List

from .auth import get_tavily_client

logger = logging.getLogger(__name__)


def tavily_crawl(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crawl Website — start from a root URL and follow links with depth/breadth controls.
    Expected args include: url (required), max_depth, max_breadth, limit,
    instructions, select_paths, select_domains, allow_external, categories,
    extract_depth, format, include_favicon.
    """
    client = get_tavily_client()

    url = arguments.get("url")
    if not url:
        raise RuntimeError("Parameter 'url' is required for tavily_crawl")

    params: Dict[str, Any] = {
        "url": url,
        "max_depth": arguments.get("max_depth", 1),
        "max_breadth": arguments.get("max_breadth", 20),
        "limit": arguments.get("limit", 50),
        "instructions": arguments.get("instructions"),
        "select_paths": arguments.get("select_paths") or [],
        "select_domains": arguments.get("select_domains") or [],
        "allow_external": arguments.get("allow_external", False),
        "categories": arguments.get("categories") or [],
        "extract_depth": arguments.get("extract_depth", "basic"),
        "format": arguments.get("format", "markdown"),
        "include_favicon": arguments.get("include_favicon", False),
    }

    def _b(v: Any) -> Any:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            s = v.strip().lower()
            if s in {"true", "1", "yes", "y"}:
                return True
            if s in {"false", "0", "no", "n"}:
                return False
        return v

    def _i(v: Any) -> Any:
        if isinstance(v, int):
            return v
        if isinstance(v, str) and v.strip().isdigit():
            return int(v)
        return v

    for k in ("max_depth", "max_breadth", "limit"):
        params[k] = _i(params[k])

    for k in ("allow_external", "include_favicon"):
        params[k] = _b(params[k])

    logger.info(f"tavily_crawl: {url}")
    return client.crawl(**{k: v for k, v in params.items() if v is not None})
