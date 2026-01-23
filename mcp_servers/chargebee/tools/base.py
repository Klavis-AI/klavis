import logging
import os
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the API key for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')
site_context: ContextVar[str] = ContextVar('site')


def get_auth_token() -> str:
    """Get the authentication token from context or environment."""
    try:
        token = auth_token_context.get()
        if token:
            return token
    except LookupError:
        pass

    # Fall back to environment variable
    token = os.getenv("CHARGEBEE_ACCESS_TOKEN", "")
    if token:
        return token

    raise RuntimeError("No API key provided. Please set the CHARGEBEE_ACCESS_TOKEN.")


def get_site() -> str:
    """Get the Chargebee site from context or environment."""
    try:
        site = site_context.get()
        if site:
            return site
    except LookupError:
        pass

    # Fall back to environment variable
    site = os.getenv("CHARGEBEE_SITE", "")
    if site:
        return site

    raise RuntimeError("No site provided. Please set the CHARGEBEE_SITE.")


class ChargebeeClient:
    """Client for Chargebee API using Basic Authentication."""

    @staticmethod
    async def make_request(
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Chargebee API."""
        api_key = get_auth_token()
        site = get_site()

        if not api_key:
            raise RuntimeError("No API key provided. Please set the CHARGEBEE_ACCESS_TOKEN.")

        if not site:
            raise RuntimeError("No site provided. Please set the CHARGEBEE_SITE.")

        # Chargebee uses HTTP Basic Auth with API key as username and empty password
        auth = httpx.BasicAuth(api_key, "")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        url = f"https://{site}.chargebee.com/api/v2{endpoint}"

        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, auth=auth, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, auth=auth, headers=headers, data=data)
            elif method.upper() == "PUT":
                response = await client.put(url, auth=auth, headers=headers, data=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, auth=auth, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            # Handle empty responses for DELETE operations
            if response.status_code == 204 or not response.content:
                return {"success": True}

            try:
                json_response = response.json()
                if json_response is None:
                    return {"data": None, "message": "API returned null response"}
                return json_response
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.content}")
                return {"error": "Invalid JSON response", "content": response.text}


async def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Chargebee API."""
    return await ChargebeeClient.make_request(method, endpoint, data, params)
