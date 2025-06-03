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