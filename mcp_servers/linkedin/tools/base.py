import os
import logging
import ssl
from typing import Any, Dict, Optional
from contextvars import ContextVar
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

# LinkedIn API constants
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

# Context variable to store the LinkedIn access token for each request
linkedin_token_context: ContextVar[str] = ContextVar('linkedin_token')

def get_linkedin_access_token() -> str:
    """Get the LinkedIn access token from context or environment."""
    try:
        # Try to get from context first (for MCP server usage)
        return linkedin_token_context.get()
    except LookupError:
        # Fall back to environment variable (for standalone usage)
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("LinkedIn access token not found in request context or environment")
        return token

def _get_linkedin_headers() -> Dict[str, str]:
    """Create standard headers for LinkedIn API calls."""
    access_token = get_linkedin_access_token()
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

def _get_ssl_context():
    """Create secure SSL context."""
    return ssl.create_default_context()

async def make_linkedin_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict] = None, 
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the LinkedIn API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (should start with /)
        json_data: JSON payload for POST/PUT requests
        expect_empty_response: Whether to expect an empty response (for some operations)
    
    Returns:
        Response data as dict, or None for empty responses
    """
    url = f"{LINKEDIN_API_BASE}{endpoint}"
    headers = _get_linkedin_headers()
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
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
            logger.error(f"LinkedIn API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"LinkedIn API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during LinkedIn API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e
