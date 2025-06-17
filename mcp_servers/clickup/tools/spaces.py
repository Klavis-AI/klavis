import logging
from typing import Any, Dict, Optional
from .base import make_clickup_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_spaces(team_id: str) -> Dict[str, Any]:
    """Get all spaces in a team."""
    logger.info(f"Executing tool: get_spaces with team_id: {team_id}")
    try:
        result = await make_clickup_request(f"team/{team_id}/space")
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_spaces: {e}")
        raise e

async def create_space(team_id: str, name: str, color: Optional[str] = None, private: bool = False) -> Dict[str, Any]:
    """Create a new space in a team."""
    logger.info(f"Executing tool: create_space with name: {name}")
    try:
        data = {
            "name": name,
            "private": private
        }
        if color:
            data["color"] = color
            
        result = await make_clickup_request(f"team/{team_id}/space", "POST", data)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool create_space: {e}")
        raise e

async def update_space(space_id: str, name: Optional[str] = None, color: Optional[str] = None, private: Optional[bool] = None) -> Dict[str, Any]:
    """Update an existing space."""
    logger.info(f"Executing tool: update_space with space_id: {space_id}")
    try:
        data = {}
        if name:
            data["name"] = name
        if color:
            data["color"] = color
        if private is not None:
            data["private"] = private
            
        result = await make_clickup_request(f"space/{space_id}", "PUT", data)
        return result
    except Exception as e:
        logger.exception(f"Error executing tool update_space: {e}")
        raise e 