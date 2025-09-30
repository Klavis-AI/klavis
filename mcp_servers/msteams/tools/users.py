
from .base import make_graph_api_request

async def list_users():
    """Lists all users in the organization."""
    return await make_graph_api_request("GET", "/users")

async def get_user(user_id: str):
    """Gets a specific user by their ID or userPrincipalName."""
    return await make_graph_api_request("GET", f"/users/{user_id}")
