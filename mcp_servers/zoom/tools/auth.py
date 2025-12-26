import json
import contextvars
from typing import Optional, Dict, Any
import httpx
import asyncio
import time

# Context variable for storing OAuth access token per request
zoom_access_token_context = contextvars.ContextVar("zoom_access_token", default=None)

# Device flow OAuth configuration
ZOOM_OAUTH_CONFIG = {
    "client_id": "your_zoom_client_id",  # Replace with your Zoom App Client ID
    "device_authorization_url": "https://zoom.us/oauth/device",
    "token_url": "https://zoom.us/oauth/token",
    "user_verification_url": "https://zoom.us/activate",
    "scopes": "meeting:write meeting:read user:read webinar:write webinar:read"
}

class DeviceFlowOAuth:
    """Handle Zoom OAuth device flow authentication."""
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id or ZOOM_OAUTH_CONFIG["client_id"]
        self.device_code = None
        self.user_code = None
        self.verification_url = None
        self.interval = 5
        self.expires_in = 600
        
    async def start_device_flow(self) -> Dict[str, Any]:
        """Start the device authorization flow."""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "scope": ZOOM_OAUTH_CONFIG["scopes"]
            }
            
            response = await client.post(
                ZOOM_OAUTH_CONFIG["device_authorization_url"],
                data=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Device authorization failed: {response.text}")
            
            result = response.json()
            self.device_code = result["device_code"]
            self.user_code = result["user_code"]
            self.verification_url = result["verification_url"]
            self.interval = result.get("interval", 5)
            self.expires_in = result.get("expires_in", 600)
            
            return {
                "user_code": self.user_code,
                "verification_url": self.verification_url,
                "expires_in": self.expires_in,
                "interval": self.interval
            }
    
    async def poll_for_token(self, device_code: str = None) -> Optional[str]:
        """Poll for the access token."""
        device_code = device_code or self.device_code
        
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "device_code",
                "client_id": self.client_id,
                "device_code": device_code
            }
            
            response = await client.post(
                ZOOM_OAUTH_CONFIG["token_url"],
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["access_token"]
            elif response.status_code == 400:
                error = response.json()
                if error.get("error") == "authorization_pending":
                    return None  # Still waiting for user authorization
                elif error.get("error") == "authorization_declined":
                    raise Exception("User declined authorization")
                elif error.get("error") == "expired_token":
                    raise Exception("Device code expired")
                else:
                    raise Exception(f"Token request failed: {error}")
            else:
                raise Exception(f"Token request failed: {response.text}")
    
    async def authenticate_user(self) -> str:
        """Complete the device flow authentication and return access token."""
        print("🔐 Starting Zoom OAuth Device Flow...")
        
        # Step 1: Start device flow
        flow_info = await self.start_device_flow()
        
        print(f"\n📱 Please visit: {flow_info['verification_url']}")
        print(f"🔢 Enter code: {flow_info['user_code']}")
        print(f"⏰ Code expires in: {flow_info['expires_in']} seconds")
        print("\n⏳ Waiting for authorization...")
        
        # Step 2: Poll for token
        start_time = time.time()
        while time.time() - start_time < flow_info['expires_in']:
            try:
                token = await self.poll_for_token()
                if token:
                    print("✅ Authorization successful!")
                    return token
                
                # Wait before next poll
                await asyncio.sleep(flow_info['interval'])
                print(".", end="", flush=True)
                
            except Exception as e:
                if "expired" in str(e).lower():
                    raise Exception("Device code expired. Please try again.")
                elif "declined" in str(e).lower():
                    raise Exception("Authorization was declined.")
                else:
                    raise e
        
        raise Exception("Authentication timed out. Please try again.")

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

async def authenticate_with_device_flow(client_id: str = None) -> str:
    """Authenticate user using device flow and return access token."""
    oauth = DeviceFlowOAuth(client_id)
    return await oauth.authenticate_user()
