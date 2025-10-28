import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

CLICKUP_API_BASE_URL = "https://api.clickup.com/api/v2"

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

async def make_clickup_request(
    endpoint: str, 
    method: str = "GET", 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a REST API request to ClickUp API."""
    access_token = get_auth_token()
    
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json"
    }
    
    url = f"{CLICKUP_API_BASE_URL}/{endpoint.lstrip('/')}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data, params=params)
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data, params=params)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() 