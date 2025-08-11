import logging
from typing import Optional, Dict, Any, List
from .base import make_zendesk_request, validate_pagination_params, ZendeskToolExecutionError

logger = logging.getLogger(__name__)

async def list_users(
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    role: Optional[str] = None,
    organization_id: Optional[int] = None
) -> Dict[str, Any]:
    """List users with optional filtering and pagination."""
    try:
        params = validate_pagination_params(page, per_page)
        
        # Add optional filters
        if role:
            params["role"] = role
        if organization_id:
            params["organization_id"] = organization_id
        
        return await make_zendesk_request("GET", "/users.json", params=params)
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise

async def get_user(user_id: int) -> Dict[str, Any]:
    """Get a single user by ID."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        return await make_zendesk_request("GET", f"/users/{user_id}.json")
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise

async def create_user(
    name: str,
    email: str,
    role: str = "end-user",
    organization_id: Optional[int] = None,
    phone: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create a new user."""
    try:
        if not name or not email:
            raise ZendeskToolExecutionError("Name and email are required")
        
        valid_roles = ["end-user", "agent", "admin"]
        if role not in valid_roles:
            raise ZendeskToolExecutionError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        user_data = {
            "user": {
                "name": name,
                "email": email,
                "role": role
            }
        }
        
        # Add optional fields
        if organization_id:
            user_data["user"]["organization_id"] = organization_id
        if phone:
            user_data["user"]["phone"] = phone
        if tags:
            user_data["user"]["tags"] = tags
        if custom_fields:
            user_data["user"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("POST", "/users.json", data=user_data)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

async def update_user(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    organization_id: Optional[int] = None,
    phone: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Update an existing user."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        user_data = {"user": {}}
        
        # Add only provided fields
        if name is not None:
            user_data["user"]["name"] = name
        if email is not None:
            user_data["user"]["email"] = email
        if role is not None:
            valid_roles = ["end-user", "agent", "admin"]
            if role not in valid_roles:
                raise ZendeskToolExecutionError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
            user_data["user"]["role"] = role
        if organization_id is not None:
            user_data["user"]["organization_id"] = organization_id
        if phone is not None:
            user_data["user"]["phone"] = phone
        if tags is not None:
            user_data["user"]["tags"] = tags
        if custom_fields is not None:
            user_data["user"]["custom_fields"] = custom_fields
        
        return await make_zendesk_request("PUT", f"/users/{user_id}.json", data=user_data)
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise

async def delete_user(user_id: int) -> Dict[str, Any]:
    """Delete a user."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        return await make_zendesk_request("DELETE", f"/users/{user_id}.json")
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise

async def search_users(
    query: str,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Search users using Zendesk search syntax."""
    try:
        if not query:
            raise ZendeskToolExecutionError("Search query is required")
        
        params = validate_pagination_params(page, per_page)
        params["query"] = query
        
        return await make_zendesk_request("GET", "/search.json", params=params)
    except Exception as e:
        logger.error(f"Error searching users with query '{query}': {e}")
        raise

async def get_user_tickets(
    user_id: int,
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Dict[str, Any]:
    """Get tickets requested by a specific user."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        params = validate_pagination_params(page, per_page)
        return await make_zendesk_request("GET", f"/users/{user_id}/tickets/requested.json", params=params)
    except Exception as e:
        logger.error(f"Error getting tickets for user {user_id}: {e}")
        raise

async def get_user_organizations(user_id: int) -> Dict[str, Any]:
    """Get organizations associated with a user."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        return await make_zendesk_request("GET", f"/users/{user_id}/organizations.json")
    except Exception as e:
        logger.error(f"Error getting organizations for user {user_id}: {e}")
        raise

async def suspend_user(user_id: int) -> Dict[str, Any]:
    """Suspend a user account."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        user_data = {
            "user": {
                "suspended": True
            }
        }
        
        return await make_zendesk_request("PUT", f"/users/{user_id}.json", data=user_data)
    except Exception as e:
        logger.error(f"Error suspending user {user_id}: {e}")
        raise

async def reactivate_user(user_id: int) -> Dict[str, Any]:
    """Reactivate a suspended user account."""
    try:
        if not user_id or user_id <= 0:
            raise ZendeskToolExecutionError("Valid user ID is required")
        
        user_data = {
            "user": {
                "suspended": False
            }
        }
        
        return await make_zendesk_request("PUT", f"/users/{user_id}.json", data=user_data)
    except Exception as e:
        logger.error(f"Error reactivating user {user_id}: {e}")
        raise

async def get_current_user() -> Dict[str, Any]:
    """Get the current authenticated user's information."""
    try:
        return await make_zendesk_request("GET", "/users/me.json")
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise
