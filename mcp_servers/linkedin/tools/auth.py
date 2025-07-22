import logging
from typing import Any, Dict, Optional
from .base import make_linkedin_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_profile_info(person_id: Optional[str] = None) -> Dict[str, Any]:
    """Get LinkedIn profile information. If person_id is None, gets current user's profile."""
    logger.info(f"Executing tool: get_profile_info with person_id: {person_id}")
    try:
        if person_id:
            # Note: Getting other users' profile info requires additional permissions
            return {"error": "Getting other users' profile information requires elevated LinkedIn API permissions"}
        else:
            # Use the working userinfo endpoint for current user
            endpoint = "/userinfo"
        
        # Get basic profile info
        profile_data = await make_linkedin_request("GET", endpoint)
        
        profile_info = {
            "id": profile_data.get("sub"),
            "firstName": profile_data.get("given_name"),
            "lastName": profile_data.get("family_name"),
            "name": profile_data.get("name"),
            "email": profile_data.get("email"),
            "email_verified": profile_data.get("email_verified"),
            "locale": profile_data.get("locale")
        }
        
        return profile_info
    except Exception as e:
        logger.exception(f"Error executing tool get_profile_info: {e}")
        raise e