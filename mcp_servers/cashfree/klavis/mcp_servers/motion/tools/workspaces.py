import logging
from typing import Any, Dict
from .base import make_api_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_workspaces() -> Dict[str, Any]:
    """Get all workspaces."""
    logger.info("Executing tool: get_workspaces")
    try:
        endpoint = "/workspaces"
        return await make_api_request(endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_workspaces: {e}")
        raise e 