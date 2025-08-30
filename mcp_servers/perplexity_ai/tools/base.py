import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

PERPLEXITY_API_BASE_URL = "https://api.perplexity.ai"

# Context variable to store the API key for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_api_key() -> str:
    """Get the API key from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("API key not found in request context")

async def make_perplexity_request(
    endpoint: str, 
    method: str = "POST", 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a REST API request to Perplexity AI API."""
    api_key = get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{PERPLEXITY_API_BASE_URL}/{endpoint.lstrip('/')}"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
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
