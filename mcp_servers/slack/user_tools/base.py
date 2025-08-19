import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

SLACK_API_ENDPOINT = "https://slack.com/api"

# Context variable to store user token for each request
user_token_context: ContextVar[str] = ContextVar('user_token')

def get_user_token() -> str:
    """Get the user authentication token from context."""
    try:
        return user_token_context.get()
    except LookupError:
        raise RuntimeError("User authentication token not found in request context")

class SlackUserClient:
    """Client for Slack API using User Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to Slack API using user token."""
        api_token = get_user_token()
        
        if not api_token:
            raise RuntimeError("No user API token provided. Please set the authentication header.")
        
        # Slack uses Bearer Authentication
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        url = f"{SLACK_API_ENDPOINT}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check HTTP status
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {"ok": True}
            
            try:
                json_response = response.json()
                
                # Check for Slack API errors
                if not json_response.get("ok", False):
                    error_msg = json_response.get("error", "Unknown Slack API error")
                    logger.error(f"Slack API error: {error_msg}")
                    raise SlackAPIError(error_msg, json_response)
                
                return json_response
            except ValueError as e:
                # Handle cases where response content exists but isn't valid JSON
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.content}")
                return {"error": "Invalid JSON response", "content": response.text}

async def make_slack_user_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Slack API using user token."""
    return await SlackUserClient.make_request(method, endpoint, data, params)

class SlackAPIError(Exception):
    """Custom exception for Slack API errors."""
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.response = response