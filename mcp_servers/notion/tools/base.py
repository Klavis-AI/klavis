import os
from typing import Optional
from contextvars import ContextVar
from notion_client import Client

# Context variable to store auth token for the current request
auth_token_context: ContextVar[str] = ContextVar('auth_token', default="")


def get_notion_client() -> Client:
    """Get Notion client with authentication token from context or environment."""
    # Try to get token from context first (for HTTP requests)
    try:
        token = auth_token_context.get()
        if token:
            return Client(auth=token)
    except LookupError:
        pass
    
    # Fall back to environment variable
    token = os.getenv("NOTION_API_KEY")
    if not token:
        raise ValueError("Notion API key not found. Please set NOTION_API_KEY environment variable or provide x-auth-token header.")
    
    return Client(auth=token)


def handle_notion_error(error: Exception) -> dict:
    """Handle Notion API errors and return formatted error response."""
    error_msg = str(error)
    
    if "Unauthorized" in error_msg:
        return {
            "error": "Authentication failed. Please check your Notion API key.",
            "type": "authentication_error"
        }
    elif "Not found" in error_msg:
        return {
            "error": "The requested resource was not found. Check the ID and permissions.",
            "type": "not_found_error"
        }
    elif "Forbidden" in error_msg:
        return {
            "error": "Access denied. The integration may not have permission to access this resource.",
            "type": "permission_error"
        }
    else:
        return {
            "error": f"Notion API error: {error_msg}",
            "type": "api_error"
        }


def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a valid UUID format."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def format_notion_id(notion_id: str) -> str:
    """Format Notion ID by removing dashes if present."""
    return notion_id.replace('-', '')


def clean_notion_response(response: dict) -> dict:
    """Clean up Notion API response by removing unnecessary fields."""
    if isinstance(response, dict):
        # Remove common unnecessary fields
        cleaned = {k: v for k, v in response.items() 
                  if k not in ['request_id', 'developer_survey']}
        
        # Recursively clean nested dictionaries
        for key, value in cleaned.items():
            if isinstance(value, dict):
                cleaned[key] = clean_notion_response(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_notion_response(item) if isinstance(item, dict) else item 
                              for item in value]
        
        return cleaned
    return response 