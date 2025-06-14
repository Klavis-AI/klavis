import logging
import base64
from typing import Any, Dict
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

GONG_API_ENDPOINT = "https://api.gong.io"

# Context variable to store the basic auth header for each request
# We expect the server to set this value from the incoming HTTP header "x-auth-token",
# where the value is already formatted as "Basic <base64(key:secret)>".
# This mirrors the pattern used by the Linear server for easy re-use by callers.
auth_token_context: ContextVar[str] = ContextVar("auth_token")

def get_auth_header() -> str:
    """Return the Authorization header value stored in the context, or raise."""
    try:
        return auth_token_context.get()
    except LookupError:  # pragma: no cover
        raise RuntimeError("Authentication token not found in request context")

def build_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """Helper to construct request headers with Authorization and JSON content type."""
    headers: Dict[str, str] = {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers

async def get(path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Perform a GET request to the Gong API and return JSON."""
    url = f"{GONG_API_ENDPOINT}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=build_headers())
        resp.raise_for_status()
        return resp.json()

async def post(path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a POST request to the Gong API and return JSON."""
    url = f"{GONG_API_ENDPOINT}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=json_body, headers=build_headers())
        resp.raise_for_status()
        return resp.json() 