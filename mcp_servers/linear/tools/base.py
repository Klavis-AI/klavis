import logging
from typing import Any, Dict
from contextvars import ContextVar
import httpx

# Configure logging
logger = logging.getLogger(__name__)

LINEAR_API_ENDPOINT = "https://api.linear.app/graphql"

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def clean_filter_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Remove empty string values and empty nested objects from a filter object.
    
    This is necessary because the Linear API returns 400 Bad Request when
    filter objects contain empty strings (e.g., {'lte': '', 'gte': ''}).
    """
    if not isinstance(obj, dict):
        return obj
    
    cleaned = {}
    for key, value in obj.items():
        if isinstance(value, dict):
            nested_cleaned = clean_filter_object(value)
            if nested_cleaned:  # Only add if not empty after cleaning
                cleaned[key] = nested_cleaned
        elif value != "" and value is not None:  # Exclude empty strings and None
            cleaned[key] = value
    return cleaned

async def make_graphql_request(query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a GraphQL request to Linear API."""
    access_token = get_auth_token()
    
    headers = {
        "Authorization": access_token,
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    async with httpx.AsyncClient() as client:
        response = await client.post(LINEAR_API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        return response.json() 