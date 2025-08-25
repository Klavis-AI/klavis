import os
import logging
import ssl
from typing import Any, Dict, Optional
from contextvars import ContextVar
import aiohttp

logger = logging.getLogger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search"

serpapi_token_context: ContextVar[str] = ContextVar('serpapi_token')


def get_serpapi_access_token() -> str:
    """Get the SerpApi access token from context or environment."""
    try:
        return serpapi_token_context.get()
    except LookupError:
        token = os.getenv("SERPAPI_API_KEY")
        if not token:
            raise RuntimeError("SerpApi API key not found in request context or environment")
        return token

def _get_serpapi_headers() -> Dict[str, str]:
    """Create standard headers for SerpApi calls."""
    return {
        "User-Agent": "MCP Google Jobs Server",
        "Accept": "application/json"
    }

def _get_ssl_context():
    """Create secure SSL context."""
    return ssl.create_default_context()

async def make_serpapi_request(
    params: Dict[str, Any],
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the SerpApi.
    
    Args:
        params: Query parameters for the API request
        expect_empty_response: Whether to expect an empty response
    
    Returns:
        Response data as dict, or None for empty responses
    """
    api_key = get_serpapi_access_token()
    params["api_key"] = api_key
    params["engine"] = params.get("engine", "google_jobs")
    
    url = SERPAPI_BASE_URL
    headers = _get_serpapi_headers()
    
    connector = aiohttp.TCPConnector(ssl=_get_ssl_context())
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                
                if expect_empty_response:
                    if response.status in [200, 201, 204]:
                        return None
                    else:
                        logger.warning(f"Expected empty response for SerpApi request, but got status {response.status}")
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()
                else:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        data = await response.json()
                        
                        if "error" in data:
                            raise RuntimeError(f"SerpApi error: {data['error']}")
                        
                        return data
                    else:
                        text_content = await response.text()
                        logger.warning(f"Received non-JSON response from SerpApi: {text_content[:100]}...")
                        return {"raw_content": text_content}
                        
        except aiohttp.ClientResponseError as e:
            logger.error(f"SerpApi request failed: {e.status} {e.message} for {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"SerpApi Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during SerpApi request: {e}")
            raise RuntimeError(f"Unexpected error during API call to SerpApi") from e
