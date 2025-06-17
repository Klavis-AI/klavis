import logging
from typing import Any, Dict
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_teams() -> Dict[str, Any]:
    """Get all teams/workspaces the user has access to."""
    logger.info("Executing tool: get_teams")
    try:
        result = await make_clickup_request("team")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_teams: {e}")
        raise e

async def get_workspaces() -> Dict[str, Any]:
    """Get all workspaces (alias for get_teams for consistency)."""
    logger.info("Executing tool: get_workspaces")
    try:
        return await get_teams()
    except Exception as e:
        logger.exception(f"Error executing tool get_workspaces: {e}")
        raise e 