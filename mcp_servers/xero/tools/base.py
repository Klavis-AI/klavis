import os
import logging
import ssl
from typing import Any, Dict, Optional
from contextvars import ContextVar
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

# Xero API constants
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"

# Context variable to store the Xero access token for each request
xero_token_context: ContextVar[str] = ContextVar('xero_token')

def get_xero_access_token() -> str:
    """Get the Xero access token from context or environment."""
    try:
        # Try to get from context first (for MCP server usage)
        return xero_token_context.get()
    except LookupError:
        # Fall back to environment variable (for standalone usage)
        token = os.getenv("XERO_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("Xero access token not found in request context or environment")
        return token

def get_xero_tenant_id() -> str:
    """Get the Xero tenant ID from environment."""
    tenant_id = os.getenv("XERO_TENANT_ID")
    if not tenant_id:
        raise RuntimeError("XERO_TENANT_ID not found in environment")
    return tenant_id

def _get_xero_headers() -> Dict[str, str]:
    """Create standard headers for Xero API calls."""
    access_token = get_xero_access_token()
    tenant_id = get_xero_tenant_id()
    return {
        "Authorization": f"Bearer {access_token}",
        "Xero-tenant-id": tenant_id,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def _get_ssl_context():
    """Create secure SSL context."""
    return ssl.create_default_context()

async def make_xero_api_request(
    endpoint: str, 
    method: str = "GET", 
    data: Optional[Dict] = None, 
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the Xero API.
    
    Args:
        endpoint: API endpoint (should start with / or be a relative path)
        method: HTTP method (GET, POST, PUT, etc.)
        data: JSON payload for POST/PUT requests
        expect_empty_response: Whether to expect an empty response (for some operations)
    
    Returns:
        Response data as dict, or None for empty responses
    """
    # Ensure endpoint starts with proper format
    if not endpoint.startswith('/'):
        endpoint = f"/{endpoint}"
    
    url = f"{XERO_API_BASE}{endpoint}"
    headers = _get_xero_headers()
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.request(method, url, json=data) as response:
                response.raise_for_status()
                
                if expect_empty_response:
                    if response.status in [200, 201, 204]:
                        return None
                    else:
                        logger.warning(f"Expected empty response for {method} {endpoint}, but got status {response.status}")
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()
                else:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        return await response.json()
                    else:
                        text_content = await response.text()
                        logger.warning(f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}...")
                        return {"raw_content": text_content}
                        
        except aiohttp.ClientResponseError as e:
            logger.error(f"Xero API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"Xero API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Xero API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e
