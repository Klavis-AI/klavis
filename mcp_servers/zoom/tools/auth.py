import json
import contextvars
from typing import Optional, Dict, Any
import httpx

# Context variable for storing OAuth access token per request
zoom_access_token_context = contextvars.ContextVar("zoom_access_token", default=None)

def get_zoom_access_token() -> str:
    """Get Zoom OAuth access token from context."""
    access_token = zoom_access_token_context.get()
    
    if not access_token:
        raise ValueError("Missing Zoom OAuth access token. Please provide x-zoom-access-token header.")
    
    return access_token

class ZoomClient:
    """Client for interacting with Zoom API using OAuth access tokens."""
    
    def __init__(self, access_token: str):
        self.base_url = "https://api.zoom.us/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to Zoom API."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request to Zoom API."""
        return await self._make_request("GET", endpoint)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Zoom API."""
        return await self._make_request("POST", endpoint, data)
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request to Zoom API."""
        return await self._make_request("PUT", endpoint, data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request to Zoom API."""
        return await self._make_request("DELETE", endpoint, data)

def get_zoom_client() -> ZoomClient:
    """Get a Zoom client instance using OAuth access token from context."""
    access_token = get_zoom_access_token()
    return ZoomClient(access_token)

async def validate_access_token(access_token: str) -> bool:
    """Validate Zoom OAuth access token by making a test request."""
    try:
        # Create a temporary client to test the token
        test_client = ZoomClient(access_token)
        # Try to get user info to validate the token
        await test_client.get("/users/me")
        return True
    except Exception:
        return False
