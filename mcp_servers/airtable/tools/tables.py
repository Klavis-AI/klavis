import logging
from typing import Any, Dict

from .base import make_airtable_request

# Configure logging
logger = logging.getLogger(__name__)


async def get_tables_info(base_id: str) -> Dict[str, Any]:
    """Get information about all tables in a base."""
    endpoint = f"meta/bases/{base_id}/tables"
    try:
        logger.info(f"Executing tool: get_tables_info for base_id: {base_id}")
        return await make_airtable_request("GET", endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_tables_info: {e}")
        raise e
