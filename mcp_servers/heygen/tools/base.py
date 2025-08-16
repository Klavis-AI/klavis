"""
Base HTTP client for HeyGen API with authentication and error handling.
"""

import os
import httpx
from typing import Dict, Any, Optional
from contextvars import ContextVar

auth_token_context: ContextVar[Optional[str]] = ContextVar('auth_token', default=None)

HEYGEN_API_ENDPOINT = "https://api.heygen.com"

def get_auth_token() -> str:
    """Get the HeyGen API token from context or environment variable."""
    try:
        token = auth_token_context.get()
        if not token:
            token = os.getenv("HEYGEN_API_KEY")
            if not token:
                raise RuntimeError("No HeyGen API key found in context or environment")
        return token
    except LookupError:
        token = os.getenv("HEYGEN_API_KEY")
        if not token:
            raise RuntimeError("No HeyGen API key found in context or environment")
        return token

def get_headers() -> Dict[str, str]:
    """Get standard headers for HeyGen API requests."""
    return {
        "X-Api-Key": get_auth_token(),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make an HTTP request to the HeyGen API.
    
    Args:
        method: HTTP method (GET, POST, DELETE, etc.)
        endpoint: API endpoint (without base URL)
        data: Request body data for POST/PUT requests
        params: Query parameters
        
    Returns:
        Dict containing the API response
        
    Raises:
        RuntimeError: If the API request fails
    """
    url = f"{HEYGEN_API_ENDPOINT}{endpoint}"
    headers = get_headers()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Some endpoints may return empty response (like delete)
            if response.status_code == 204 or not response.content:
                return {"success": True}
                
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_response = e.response.json()
                if isinstance(error_response, dict):
                    error_detail = error_response.get("message", error_response.get("error", str(error_response)))
                else:
                    error_detail = str(error_response)
            except:
                error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            
            raise RuntimeError(f"HeyGen API error ({e.response.status_code}): {error_detail}")
        except Exception as e:
            raise RuntimeError(f"HeyGen API request failed: {str(e)}")