import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

AFFINITY_API_ENDPOINT = "https://api.affinity.co"

# Context variable to store the API key for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

async def make_http_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Affinity API."""
    api_key = get_auth_token()
    
    if not api_key:
        raise RuntimeError("No API key provided. Please set the x-auth-token header.")
    
    # Affinity uses HTTP Basic Auth with API key
    auth = httpx.BasicAuth("", api_key)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"{AFFINITY_API_ENDPOINT}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, auth=auth, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, auth=auth, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await client.put(url, auth=auth, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, auth=auth, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # Handle empty responses for DELETE operations
        if response.status_code == 204 or not response.content:
            return {"success": True}
        
        return response.json() 