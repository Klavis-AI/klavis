import os
import logging
import ssl
from typing import Any, Dict, Optional
from contextvars import ContextVar
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the Figma API key for each request
figma_token_context: ContextVar[str] = ContextVar('figma_token')

def get_figma_api_key() -> str:
    """Get the Figma API key from context or environment."""
    try:
        # Try to get from context first (for MCP server usage)
        return figma_token_context.get()
    except LookupError:
        # Fall back to environment variable (for standalone usage)
        api_key = os.getenv("FIGMA_API_KEY")
        if not api_key:
            raise RuntimeError("Figma API key not found in request context or environment")
        return api_key

def _get_figma_base_url() -> str:
    """Get the base URL for Figma API."""
    return "https://api.figma.com"

def _get_figma_headers() -> Dict[str, str]:
    """Create standard headers for Figma API calls."""
    api_key = get_figma_api_key()
    return {
        "Content-Type": "application/json",
        "X-Figma-Token": api_key
    }

def _get_ssl_context():
    """Create secure SSL context."""
    return ssl.create_default_context()

async def make_figma_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict] = None, 
    params: Optional[Dict] = None,
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the Figma API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (should start with /)
        json_data: JSON payload for POST/PUT requests
        params: Query parameters for GET requests
        expect_empty_response: Whether to expect an empty response (for some operations)
    
    Returns:
        Response data as dict, or None for empty responses
    """
    base_url = _get_figma_base_url()
    url = f"{base_url}{endpoint}"
    headers = _get_figma_headers()
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.request(method, url, json=json_data, params=params) as response:
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
            logger.error(f"Figma API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                if 'err' in error_body:
                    error_details = error_body['err']
                elif 'message' in error_body:
                    error_details = error_body['message']
                else:
                    error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"Figma API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Figma API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e