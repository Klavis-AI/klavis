import logging
from typing import Any, Dict

from .base import make_airtable_request

# Configure logging
logger = logging.getLogger("airtable_tools")


async def create_field(
    base_id: str,
    table_id: str,
    name: str,
    type: str,
    description: str | None = None,
    options: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Create a new field in a table."""
    endpoint = f"meta/bases/{base_id}/tables/{table_id}/fields"

    payload = {
        "name": name,
        "type": type,
    }

    if description:
        payload["description"] = description

    if options:
        payload["options"] = options

    logger.info(
        f"Executing tool: create_field '{name}' of type '{type}' in table {table_id}, base {base_id}"
    )
    return await make_airtable_request("POST", endpoint, json_data=payload)


async def update_field(
    base_id: str,
    table_id: str,
    field_id: str,
    name: str | None = None,
    description: str | None = None,
) -> Dict[str, Any]:
    """Update an existing field in a table."""
    endpoint = f"meta/bases/{base_id}/tables/{table_id}/fields/{field_id}"

    payload = {}

    if name is not None:
        payload["name"] = name

    if description is not None:
        payload["description"] = description

    logger.info(
        f"Executing tool: update_field '{field_id}' in table {table_id}, base {base_id}"
    )
    return await make_airtable_request("PATCH", endpoint, json_data=payload)
