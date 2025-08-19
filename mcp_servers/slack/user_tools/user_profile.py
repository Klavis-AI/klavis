import logging
from typing import Any, Dict, Optional
from .base import make_slack_user_request

# Configure logging
logger = logging.getLogger(__name__)

async def set_user_status(
    status_text: str,
    status_emoji: Optional[str] = None,
    status_expiration: Optional[int] = None
) -> Dict[str, Any]:
    """Set the user's custom status."""
    logger.info(f"Executing tool: slack_user_set_status")
    
    profile = {
        "status_text": status_text
    }
    
    if status_emoji:
        profile["status_emoji"] = status_emoji
    
    if status_expiration:
        profile["status_expiration"] = status_expiration
    
    data = {
        "profile": profile
    }
    
    try:
        return await make_slack_user_request("POST", "users.profile.set", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_set_status: {e}")
        raise e

async def get_user_profile() -> Dict[str, Any]:
    """Get the authenticated user's profile."""
    logger.info("Executing tool: slack_user_get_profile")
    
    try:
        return await make_slack_user_request("GET", "users.profile.get")
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_get_profile: {e}")
        raise e

async def set_user_presence(
    presence: str  # "auto" or "away"
) -> Dict[str, Any]:
    """Set the user's presence status."""
    logger.info(f"Executing tool: slack_user_set_presence to {presence}")
    
    data = {
        "presence": presence
    }
    
    try:
        return await make_slack_user_request("POST", "users.setPresence", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool slack_user_set_presence: {e}")
        raise e
