# tools/errors.py
import httpx

# Map common statuses to actionable messages
ERROR_HINTS = {
    400: "ERR_BAD_REQUEST: invalid parameters for Tavily. Check your inputs.",
    401: "ERR_UNAUTHORIZED: check TAVILY_API_KEY.",
    402: "ERR_PAYMENT_REQUIRED: billing or quota issue.",
    403: "ERR_FORBIDDEN: your key does not have permission for this operation.",
    404: "ERR_NOT_FOUND: resource not found at Tavily.",
    408: "ERR_TIMEOUT: Tavily took too long to respond.",
    409: "ERR_CONFLICT: request conflicts with current state.",
    413: "ERR_PAYLOAD_TOO_LARGE: reduce input size.",
    415: "ERR_UNSUPPORTED_MEDIA: unsupported content type.",
    422: "ERR_UNPROCESSABLE_ENTITY: validation failed at Tavily.",
    429: "ERR_RATE_LIMIT: Tavily rate limited the request. Retry later or reduce load.",
    500: "ERR_UPSTREAM_500: Tavily internal error.",
    502: "ERR_UPSTREAM_502: bad gateway from Tavily.",
    503: "ERR_UPSTREAM_503: Tavily service unavailable.",
    504: "ERR_UPSTREAM_504: Tavily gateway timeout.",
}

def _short_body(resp: httpx.Response, limit: int = 300) -> str:
    """Return a short, single-line snippet of the upstream response body."""
    try:
        text = resp.text or ""
    except Exception:
        text = ""
    return text[:limit].replace("\n", " ").strip()

def normalize(resp: httpx.Response) -> None:
    """
    Raise RuntimeError with a stable, AI-friendly message on non-2xx.
    Includes a short upstream body snippet for debugging and self-correction.
    """
    status = resp.status_code
    if 200 <= status < 300:
        return
    hint = ERROR_HINTS.get(status, f"ERR_UPSTREAM_{status}: unexpected error.")
    snippet = _short_body(resp)
    # Prefer a concise message the LLM can act on
    raise RuntimeError(f"{hint} Upstream says: {snippet or '<no body>'}")
