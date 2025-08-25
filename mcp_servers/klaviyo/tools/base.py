import logging
import os
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv
import httpx  # async HTTP client

# Configure logging (handlers set up in your entrypoint)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Context variable to store the API key for each request
auth_token_context: ContextVar[Optional[str]] = ContextVar("klaviyo_auth_token", default=None)

BASE_URL = "https://a.klaviyo.com/api"

async def _async_request(method: str, endpoint: str, params: Optional[dict] = None, json: Optional[dict] = None) -> dict:
    """Generic async HTTP request to Klaviyo API."""
    token = get_auth_token()
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Klaviyo-API-Key {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "revision": "2025-07-15",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.request(method, url, params=params, json=json, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Klaviyo {method} {endpoint} failed: {e}")
            return {"error": str(e)}
        
async def _async_paginate_get(endpoint: str, params: dict = None) -> list[dict]:
    """Helper for handling paginated GET requests."""
    results = []
    page_cursor = None

    while True:
        query_params = params.copy() if params else {}
        if page_cursor:
            query_params["page[cursor]"] = page_cursor

        data = await _async_request("GET", endpoint, params=query_params)
        if "error" in data:
            return results

        items = data.get("data", [])
        results.extend(items)

        # Stop if no next page
        links = data.get("links", {})
        if not links.get("next"):
            break

        # Extract cursor from "next" URL (Klaviyo uses ?page[cursor]=...)
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(links["next"])
            page_cursor = parse_qs(parsed.query).get("page[cursor]", [None])[0]
        except Exception:
            break

    return results

def get_auth_token() -> str:
    """Get the Klaviyo authentication token from context or environment."""
    token = os.getenv("KLAVIYO_API_KEY")
    if token is None:
        token = os.getenv("KLAVIYO_API_KEY")
        if not token:
            raise RuntimeError("Klaviyo API key not found in context or environment")
    logger.debug(f"Using Klaviyo API key: {token[:6]}... (truncated)")
    return token


async def get_klaviyo_client() -> Optional[httpx.AsyncClient]:
    """Return an async httpx client for Klaviyo API calls."""
    try:
        auth_token = get_auth_token()
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Klaviyo-API-Key {auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get Klaviyo API key: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Klaviyo client: {e}")
        return None


async def klaviyo_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """Helper for GET requests to Klaviyo API (async)."""
    client = await get_klaviyo_client()
    if not client:
        return None
    try:
        resp = await client.get(endpoint.lstrip("/"), params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Klaviyo GET {endpoint} failed: {e}")
        return None
    finally:
        await client.aclose()
