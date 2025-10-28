import logging
from typing import Any, Dict
from .base import make_v2_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_current_user() -> Dict[str, Any]:
    """Get current user information from Affinity V2 API."""
    logger.info("Executing tool: get_current_user")
    try:
        return await make_v2_request("GET", "/auth/whoami")
    except Exception as e:
        logger.exception(f"Error executing tool get_current_user: {e}")
        raise e 