import logging
from typing import Any, Dict
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_user() -> Dict[str, Any]:
    """Get the current user's information."""
    logger.info("Executing tool: get_user")
    try:
        result = await make_clickup_request("user")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_user: {e}")
        raise e

async def get_team_members(team_id: str) -> Dict[str, Any]:
    """Get all team members."""
    logger.info(f"Executing tool: get_team_members with team_id: {team_id}")
    try:
        result = await make_clickup_request(f"team/{team_id}/member")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_team_members: {e}")
        raise e 