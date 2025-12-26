import json
from typing import Dict, Any
from .auth import get_zoom_client

async def zoom_get_user(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get user information."""
    try:
        client = get_zoom_client()
        user_id = arguments.get("user_id", "me")
        
        endpoint = f"/users/{user_id}"
        result = await client.get(endpoint)
        
        return {
            "success": True,
            "user": result,
            "message": "User information retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get user information"
        }

async def zoom_list_users(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List all users in the account."""
    try:
        client = get_zoom_client()
        
        # Build query parameters
        params = {}
        for key in ["status", "role_id", "page_size", "page_number", "next_page_token"]:
            if key in arguments:
                params[key] = arguments[key]
        
        endpoint = "/users"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        result = await client.get(endpoint)
        
        return {
            "success": True,
            "users": result.get("users", []),
            "total_records": result.get("total_records", 0),
            "page_count": result.get("page_count", 0),
            "message": "Users retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list users"
        }
