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


async def create_table(
    base_id: str,
    name: str,
    description: str | None = None,
    fields: list[dict] = None,
) -> Dict[str, Any]:
    """Create a new table in a base.

    Args:
        base_id: ID of the base to create the table in
        name: Name of the new table
        description: Optional description of the table
        fields: List of field configurations. Each field should have at least 'name' and 'type'.
               Can include additional properties like 'description' and 'options'.
    """
    endpoint = f"meta/bases/{base_id}/tables"

    payload = {
        "name": name,
    }
    if description:
        payload["description"] = description
    if fields:
        payload["fields"] = fields

    try:
        logger.info(f"Executing tool: create_table for base_id: {base_id}")
        return await make_airtable_request("POST", endpoint, json_data=payload)
    except Exception as e:
        logger.exception(f"Error executing tool create_table: {e}")
        raise e
