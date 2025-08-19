import logging
from typing import Any, Dict, Optional
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

SLACK_API_ENDPOINT = "https://slack.com/api"

# Context variables to store the API tokens for each request
user_token_context: ContextVar[str] = ContextVar('user_token')
bot_token_context: ContextVar[str] = ContextVar('bot_token')

def get_user_token() -> str:
    """Get the user authentication token from context."""
    try:
        return user_token_context.get()
    except LookupError:
        raise RuntimeError("User authentication token not found in request context")

def get_bot_token() -> str:
    """Get the bot authentication token from context."""
    try:
        return bot_token_context.get()
    except LookupError:
        raise RuntimeError("Bot authentication token not found in request context")

class SlackClient:
    """Client for Slack API using Bearer Authentication."""
    
    @staticmethod
    async def make_request(
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_user_token: bool = True
    ) -> Dict[str, Any]:
        """Make an HTTP request to Slack API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            use_user_token: If True, use user token; if False, use bot token
        """
        api_token = get_user_token() if use_user_token else get_bot_token()
        
        if not api_token:
            token_type = "user" if use_user_token else "bot"
            raise RuntimeError(f"No {token_type} API token provided. Please set the authentication header.")
        
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

async def make_user_slack_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Slack API using user token."""
    return await SlackClient.make_request(method, endpoint, data, params, use_user_token=True)

async def make_bot_slack_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to Slack API using bot token."""
    return await SlackClient.make_request(method, endpoint, data, params, use_user_token=False)

class SlackAPIError(Exception):
    """Custom exception for Slack API errors."""
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.response = response
