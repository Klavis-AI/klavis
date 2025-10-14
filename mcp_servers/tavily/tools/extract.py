import logging
from typing import Any, Dict, List

from .auth import get_tavily_client

logger = logging.getLogger(__name__)


def tavily_extract(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Web Content — fetch and parse content from one or more URLs.
    Expected args: urls (List[str]), extract_depth, include_images, format, include_favicon
    """
    client = get_tavily_client()

    urls = arguments.get("urls")
    if not urls or not isinstance(urls, list):
        raise RuntimeError("Parameter 'urls' (list) is required for tavily_extract")

    params: Dict[str, Any] = {
        "urls": urls,
        "extract_depth": arguments.get("extract_depth", "basic"),
        "include_images": arguments.get("include_images", False),
        "format": arguments.get("format", "markdown"),
        "include_favicon": arguments.get("include_favicon", False),
    }

    # Coerce booleans passed as strings
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

    params["include_images"] = _b(params["include_images"])
    params["include_favicon"] = _b(params["include_favicon"])

    logger.info(f"tavily_extract: {len(urls)} url(s)")
    return client.extract(**{k: v for k, v in params.items() if v is not None})
