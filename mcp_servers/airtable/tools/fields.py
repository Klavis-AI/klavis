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
