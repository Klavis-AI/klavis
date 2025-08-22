import os
import logging
import ssl
from typing import Any, Dict, Optional
from contextvars import ContextVar
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the Mailchimp API key for each request
mailchimp_token_context: ContextVar[str] = ContextVar('mailchimp_token')

def get_mailchimp_api_key() -> str:
    """Get the Mailchimp API key from context or environment."""
    try:
        # Try to get from context first (for MCP server usage)
        return mailchimp_token_context.get()
    except LookupError:
        # Fall back to environment variable (for standalone usage)
        api_key = os.getenv("MAILCHIMP_API_KEY")
        if not api_key:
            raise RuntimeError("Mailchimp API key not found in request context or environment")
        return api_key

def _extract_datacenter_from_api_key(api_key: str) -> str:
    """Extract the datacenter from the Mailchimp API key."""
    # Mailchimp API keys are formatted as: key-datacenter (e.g., abc123-us6)
    if '-' in api_key:
        return api_key.split('-')[-1]
    else:
        raise ValueError("Invalid Mailchimp API key format. Expected format: key-datacenter")

def _get_mailchimp_base_url() -> str:
    """Get the base URL for Mailchimp API based on the datacenter."""
    api_key = get_mailchimp_api_key()
    datacenter = _extract_datacenter_from_api_key(api_key)
    return f"https://{datacenter}.api.mailchimp.com/3.0"

def _get_mailchimp_headers() -> Dict[str, str]:
    """Create standard headers for Mailchimp API calls."""
    return {
        "Content-Type": "application/json"
    }

def _get_ssl_context():
    """Create secure SSL context."""
    return ssl.create_default_context()

async def make_mailchimp_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict] = None, 
    params: Optional[Dict] = None,
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the Mailchimp API.
    
    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint (should start with /)
        json_data: JSON payload for POST/PATCH requests
        params: Query parameters for GET requests
        expect_empty_response: Whether to expect an empty response (for some operations)
    
    Returns:
        Response data as dict, or None for empty responses
    """
    base_url = _get_mailchimp_base_url()
    url = f"{base_url}{endpoint}"
    headers = _get_mailchimp_headers()
    api_key = get_mailchimp_api_key()
    
    # Mailchimp uses HTTP Basic Auth with 'anystring' as username and API key as password
    auth = aiohttp.BasicAuth('anystring', api_key)
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector, auth=auth) as session:
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
            logger.error(f"Mailchimp API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                if 'detail' in error_body:
                    error_details = error_body['detail']
                elif 'title' in error_body:
                    error_details = error_body['title']
                else:
                    error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"Mailchimp API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Mailchimp API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e