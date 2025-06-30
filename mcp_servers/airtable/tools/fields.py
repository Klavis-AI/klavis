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
    """Create a new field in a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to create the field in
        name: Name of the new field
        type: Type of the field (e.g., 'singleLineText', 'multipleSelectionValues', 'number', etc.)
        description: Optional description of the field
        options: Optional field configuration options specific to the field type

    Returns:
        Dict containing the created field information

    Field Types:
        - singleLineText: Single line text
        - multilineText: Long text
        - richText: Rich text with formatting
        - email: Email address
        - url: URL/Link
        - number: Number
        - currency: Currency
        - percent: Percentage
        - date: Date
        - dateTime: Date and time
        - phoneNumber: Phone number
        - singleSelect: Single select dropdown
        - multipleSelectionValues: Multiple select
        - checkbox: Checkbox
        - rating: Rating (stars)
        - formula: Formula field
        - rollup: Rollup field
        - count: Count field
        - lookup: Lookup field
        - createdTime: Created time
        - lastModifiedTime: Last modified time
        - createdBy: Created by
        - lastModifiedBy: Last modified by
        - multipleLookupValues: Multiple lookup values
        - autoNumber: Auto number
        - barcode: Barcode
        - duration: Duration
    """
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
    """Update an existing field in a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table containing the field
        field_id: ID of the field to update
        name: Optional new name for the field
        description: Optional new description for the field

    Returns:
        Dict containing the updated field information
    """
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
