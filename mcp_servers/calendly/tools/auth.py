import logging
from typing import Any, Dict
from .base import make_calendly_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_user_info() -> Dict[str, Any]:
    """Get current user's Calendly profile information."""
    logger.info("Executing tool: get_user_info")
    try:
        # Get current user information
        endpoint = "/users/me"
        
        # Get user data
        user_data = await make_calendly_request("GET", endpoint)
        
        # Extract essential user information from the response
        if 'resource' in user_data:
            resource = user_data['resource']
            user_info = {
                "uri": resource.get("uri"),
                "name": resource.get("name"),
                "slug": resource.get("slug"),
                "email": resource.get("email"),
                "scheduling_url": resource.get("scheduling_url"),
                "timezone": resource.get("timezone"),
            }
        else:
            user_info = user_data
        
        return user_info
    except Exception as e:
        logger.exception(f"Error executing tool get_user_info: {e}")
        raise e