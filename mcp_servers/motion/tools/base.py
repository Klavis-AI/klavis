import logging
from typing import Any, Dict
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

MOTION_API_ENDPOINT = "https://api.usemotion.com/v1"

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

async def make_api_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a REST API request to Motion API."""
    access_token = get_auth_token()
    
    headers = {
        "X-API-Key": access_token,
        "Content-Type": "application/json"
    }
    
    url = f"{MOTION_API_ENDPOINT}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, json=data, headers=headers)
        elif method.upper() == "PATCH":
            response = await client.patch(url, json=data, headers=headers)
        elif method.upper() == "DELETE": 
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response.json() 