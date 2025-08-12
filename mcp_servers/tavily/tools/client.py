# tools/client.py
import os
import uuid
import httpx

BASE = os.getenv("TAVILY_BASE_URL", "https://api.tavily.com")

REQUEST_TIMEOUT_S = float(os.getenv("TAVILY_TIMEOUT_S", "20"))
CONNECT_TIMEOUT_S = float(os.getenv("TAVILY_CONNECT_TIMEOUT_S", "5"))

def auth_headers() -> dict:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("Missing TAVILY_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "KlavisMCP-Tavily/0.1",
        "X-Request-Id": str(uuid.uuid4()),
    }

def http_client() -> httpx.AsyncClient:
    """
    Centralized client factory so every caller gets the same base URL, timeouts, and headers.
    """
    return httpx.AsyncClient(
        base_url=BASE,  # now actually applied
        timeout=httpx.Timeout(REQUEST_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
        headers=auth_headers(),
    )
