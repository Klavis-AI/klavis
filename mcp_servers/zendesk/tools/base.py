import os
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv
import base64

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Authentication context
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")
auth_email_context: ContextVar[str] = ContextVar("auth_email", default="")

class ZendeskToolExecutionError(Exception):
    """Custom exception for Zendesk tool execution errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for Zendesk API."""
    try:
        auth_token = auth_token_context.get()
        auth_email = auth_email_context.get()
        
        if not auth_token or not auth_email:
            raise ZendeskToolExecutionError("Authentication credentials not provided")
        
        # Zendesk uses Basic Auth with email/token:token format
        credentials = f"{auth_email}/token:{auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
    except LookupError:
        raise ZendeskToolExecutionError("Authentication credentials not found in request context")

def get_zendesk_base_url() -> str:
    """Get the Zendesk base URL from environment or default."""
    subdomain = os.getenv("ZENDESK_SUBDOMAIN", "your-subdomain")
    return f"https://{subdomain}.zendesk.com"

async def make_zendesk_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to the Zendesk API with basic error handling."""
    base_url = get_zendesk_base_url()
    url = f"{base_url}/api/v2{endpoint}"
    headers = get_auth_headers()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                params=params
            )
            
            # Handle rate limiting (HTTP 429)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after else 60
                raise ZendeskToolExecutionError(
                    f"Rate limit exceeded. Please try again in {wait_time} seconds.",
                    status_code=429
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise ZendeskToolExecutionError(
                    "Authentication failed. Please check your API token and email.",
                    status_code=401
                )
            
            # Handle other HTTP errors
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data["error"]
                except:
                    pass
                raise ZendeskToolExecutionError(error_msg, status_code=response.status_code)
            
            # Return JSON response
            if response.content:
                return response.json()
            return {}
            
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise ZendeskToolExecutionError(f"Network error: {str(e)}")
    except ZendeskToolExecutionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ZendeskToolExecutionError(f"Unexpected error: {str(e)}")

def validate_pagination_params(page: Optional[int] = None, per_page: Optional[int] = None) -> Dict[str, Any]:
    """Validate and format pagination parameters for Zendesk API."""
    params = {}
    
    if page is not None:
        if page < 1:
            raise ZendeskToolExecutionError("Page number must be 1 or greater")
        params["page"] = page
    
    if per_page is not None:
        if per_page < 1 or per_page > 100:
            raise ZendeskToolExecutionError("Per page must be between 1 and 100")
        params["per_page"] = per_page
    
    return params
