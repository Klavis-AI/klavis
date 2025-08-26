import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

# Calendly API constants
CALENDLY_API_BASE = "https://api.calendly.com"

# Context variable to store the authentication token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

class CalendlyClient:
    """Client for Calendly API using Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expect_empty_response: bool = False
    ) -> Dict[str, Any]:
        """Make an HTTP request to Calendly API."""
        access_token = get_auth_token()
        
        if not access_token:
            raise RuntimeError("No access token provided. Please set the x-auth-token header.")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{CALENDLY_API_BASE}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=json_data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                # Handle empty responses
                if expect_empty_response or response.status_code == 204 or not response.content:
                    return {"success": True}
                
                try:
                    json_response = response.json()
                    # Handle null/undefined responses
                    if json_response is None:
                        return {"data": None, "message": "API returned null response"}
                    return json_response
                except ValueError as e:
                    # Handle cases where response content exists but isn't valid JSON
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content: {response.content}")
                    return {"error": "Invalid JSON response", "content": response.text}
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"Calendly API request failed: {e.response.status_code} {e.response.reason_phrase} for {method} {url}")
                error_details = e.response.reason_phrase
                try:
                    error_body = e.response.json()
                    error_details = f"{e.response.reason_phrase} - {error_body}"
                except Exception:
                    pass
                raise RuntimeError(f"Calendly API Error ({e.response.status_code}): {error_details}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred during Calendly API request: {e}")
                raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e

async def make_calendly_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict] = None, 
    params: Optional[Dict] = None,
    expect_empty_response: bool = False
) -> Any:
    """
    Makes an HTTP request to the Calendly API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (should start with /)
        json_data: JSON payload for POST/PUT requests
        params: Query parameters
        expect_empty_response: Whether to expect an empty response (for some operations)
    
    Returns:
        Response data as dict, or None for empty responses
    """
    return await CalendlyClient.make_request(method, endpoint, json_data, params, expect_empty_response)