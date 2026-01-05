import logging
from typing import Any, Dict

from .base import make_airtable_request, normalize_table

# Configure logging
logger = logging.getLogger("airtable_tools")


async def get_tables_info(base_id: str) -> Dict[str, Any]:
    """Get information about all tables in a base."""
    endpoint = f"meta/bases/{base_id}/tables"
    logger.info(f"Executing tool: get_tables_info for base_id: {base_id}")
    raw_response = await make_airtable_request("GET", endpoint)
    
    tables = [normalize_table(t) for t in raw_response.get("tables", [])]
    return {
        "count": len(tables),
        "tables": tables,
    }


async def create_table(
    base_id: str,
    name: str,
    fields: list[dict],
    description: str | None = None,
) -> Dict[str, Any]:
    """Create a new table in a base."""
    endpoint = f"meta/bases/{base_id}/tables"

    payload = {
        "name": name,
        "fields": fields,
    }
    if description:
        payload["description"] = description

    logger.info(f"Executing tool: create_table for base_id: {base_id}")
    raw_response = await make_airtable_request("POST", endpoint, json_data=payload)
    return normalize_table(raw_response)


async def update_table(
    base_id: str,
    table_id: str,
    name: str | None = None,
    description: str | None = None,
) -> Dict[str, Any]:
    """Update an existing table in a base."""
    endpoint = f"meta/bases/{base_id}/tables/{table_id}"

    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description

    logger.info(f"Executing tool: update_table for table {table_id} in base {base_id}")
    raw_response = await make_airtable_request("PATCH", endpoint, json_data=payload)
    return normalize_table(raw_response)
