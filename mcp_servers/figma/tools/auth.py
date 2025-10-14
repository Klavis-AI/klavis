import logging
from typing import Any, Dict
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_current_user() -> Dict[str, Any]:
    """Get information about the current user (me endpoint)."""
    logger.info("Executing tool: get_current_user")
    try:
        endpoint = "/v1/me"
        
        user_data = await make_figma_request("GET", endpoint)
        
        result = {
            "id": user_data.get("id"),
            "email": user_data.get("email"),
            "handle": user_data.get("handle"),
            "img_url": user_data.get("img_url"),
            "location": user_data.get("location"),
            "company": user_data.get("company"),
            "bio": user_data.get("bio"),
            "website": user_data.get("website"),
            "public_profile": user_data.get("public_profile"),
            "created_at": user_data.get("created_at"),
            "updated_at": user_data.get("updated_at")
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_current_user: {e}")
        return {
            "error": "Failed to retrieve current user information",
            "exception": str(e)
        }

async def test_figma_connection() -> Dict[str, Any]:
    """Test the connection to Figma API and verify authentication."""
    logger.info("Executing tool: test_figma_connection")
    try:
        # Use the /v1/me endpoint to test authentication
        user_data = await get_current_user()
        
        if "error" in user_data:
            return {
                "status": "error",
                "message": "Failed to connect to Figma API",
                "error": user_data["error"]
            }
        
        result = {
            "status": "success",
            "message": "Figma API connection successful",
            "authenticated_user": {
                "id": user_data.get("id"),
                "handle": user_data.get("handle"),
                "email": user_data.get("email")
            }
        }
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool test_figma_connection: {e}")
        return {
            "status": "error",
            "message": "Failed to connect to Figma API",
            "error": str(e)
        }