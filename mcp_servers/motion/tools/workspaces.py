import logging
from typing import Any, Dict
from .base import make_api_request
from .normalize import normalize_workspaces

# Configure logging
logger = logging.getLogger(__name__)

async def get_workspaces() -> Dict[str, Any]:
    """Get all workspaces."""
    logger.info("Executing tool: get_workspaces")
    try:
        endpoint = "/workspaces"
        raw_response = await make_api_request(endpoint)
        workspaces = normalize_workspaces(raw_response.get("workspaces", []))
        return {
            "count": len(workspaces),
            "workspaces": workspaces,
        }
    except Exception as e:
        logger.exception(f"Error executing tool get_workspaces: {e}")
        raise e 