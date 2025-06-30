import logging
from typing import Any, Dict

from .base import make_airtable_request

# Configure logging
logger = logging.getLogger(__name__)


async def get_bases_info() -> Dict[str, Any]:
    """Get information about all bases."""
    endpoint = "meta/bases"
    try:
        logger.info("Executing tool: get_bases_info")
        return await make_airtable_request("GET", endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_bases_info: {e}")
        raise e
