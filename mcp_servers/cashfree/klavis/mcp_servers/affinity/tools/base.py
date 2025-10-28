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

class AffinityV1Client:
    """Client for Affinity API V1 using Basic Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Affinity V1 API."""
        api_key = get_auth_token()
        
        if not api_key:
            raise RuntimeError("No API key provided. Please set the x-auth-token header.")
        
        # V1 uses HTTP Basic Auth with API key
        auth = httpx.BasicAuth("", api_key)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # V1 endpoints don't have /v1 prefix
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

class AffinityV2Client:
    """Client for Affinity API V2 using Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Affinity V2 API."""
        api_key = get_auth_token()
        
        if not api_key:
            raise RuntimeError("No API key provided. Please set the x-auth-token header.")
        
        # note: v2 uses Bearer Authentication
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{AFFINITY_API_ENDPOINT}/v2{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses for DELETE operations
            if response.status_code == 204 or not response.content:
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

async def make_http_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Affinity V1 API."""
    return await AffinityV1Client.make_request(method, endpoint, data, params)

async def make_v2_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Affinity V2 API."""
    return await AffinityV2Client.make_request(method, endpoint, data, params) 