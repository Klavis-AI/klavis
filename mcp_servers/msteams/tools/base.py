
import os
import msal
import logging
import httpx
from typing import Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.microsoft.com/v1.0"

# Context variable to hold the access token for the current request
ms_graph_token_context: ContextVar[Optional[str]] = ContextVar("ms_graph_token_context", default=None)

def get_access_token() -> str:
    """Gets the access token from the context variable."""
    token = ms_graph_token_context.get()
    if not token:
        raise RuntimeError("Access token not found in context. This should be set by the server.")
    return token


async def make_graph_api_request(method: str, endpoint: str, json_data: Optional[dict] = None) -> dict:
    """Make a generic request to the Microsoft Graph API."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, headers=headers, json=json_data)
            response.raise_for_status() # Raises exception for 4xx/5xx responses
            # Handle 204 No Content responses
            if response.status_code == 204:
                return {"status": "Success, no content"}
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Graph API request failed: {e.response.status_code} - {e.response.text}")
            # Re-raise with a more informative message
            raise Exception(f"Graph API Error {e.response.status_code}: {e.response.text}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Graph API request: {e}")
            raise
