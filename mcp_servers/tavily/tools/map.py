import logging
from typing import Any, Dict

from .auth import get_tavily_client

logger = logging.getLogger(__name__)


def tavily_map(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Website Map — discover reachable URLs from a root without heavy extraction.
    Expected args include: url (required), max_depth, max_breadth, limit,
    instructions, select_paths, select_domains, allow_external, categories.
    """
    client = get_tavily_client()

    url = arguments.get("url")
    if not url:
        raise RuntimeError("Parameter 'url' is required for tavily_map")

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
    }

    # Coercions
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

    params["allow_external"] = _b(params["allow_external"])

    logger.info(f"tavily_map: {url}")
    return client.map(**{k: v for k, v in params.items() if v is not None})
