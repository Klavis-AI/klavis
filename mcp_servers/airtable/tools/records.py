import logging
from typing import Any, Dict

from .base import make_airtable_request

# Configure logging
logger = logging.getLogger("airtable_tools")


async def list_records(base_id: str, table_id: str) -> Dict[str, Any]:
    """Get all records from a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to get records from
    """
    endpoint = f"{base_id}/{table_id}"
    logger.info(f"Executing tool: list_records for table {table_id} in base {base_id}")
    return await make_airtable_request("GET", endpoint)


async def get_record(base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
    """Get a single record from a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table containing the record
        record_id: ID of the record to retrieve
    """
    endpoint = f"{base_id}/{table_id}/{record_id}"
    logger.info(
        f"Executing tool: get_record for record {record_id} in table {table_id}, base {base_id}"
    )
    return await make_airtable_request("GET", endpoint)


async def create_records(
    base_id: str,
    table_id: str,
    records: list[Dict[str, Any]],
    typecast: bool | None = None,
    return_fields_by_field_id: bool | None = None,
) -> Dict[str, Any]:
    """Create one or multiple records in a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to create records in
        records: List of record objects containing fields to create multiple records
        typecast: Whether to automatically convert string values to appropriate types
        return_fields_by_field_id: Whether to return fields keyed by field ID instead of name

    Note:
        Either fields or records must be provided, but not both.
    """
    endpoint = f"{base_id}/{table_id}"

    payload = {
        "typecast": typecast,
        "returnFieldsByFieldId": return_fields_by_field_id,
        "records": records,
    }

    logger.info(
        f"Executing tool: create_records for table {table_id} in base {base_id}"
    )
    return await make_airtable_request("POST", endpoint, json_data=payload)


async def update_records(
    base_id: str,
    table_id: str,
    records: list[Dict[str, Any]],
    typecast: bool | None = None,
    return_fields_by_field_id: bool | None = None,
    perform_upsert: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Update one or multiple records in a table, with optional upsert functionality.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to update records in
        records: List of record objects. For regular updates, each record must include an "id" field.
                For upserts, records should contain fields to match against.
        typecast: Whether to automatically convert string values to appropriate types
        return_fields_by_field_id: Whether to return fields keyed by field ID instead of name
        perform_upsert: Optional upsert configuration with "fieldsToMergeOn" array
    """
    endpoint = f"{base_id}/{table_id}"

    payload = {
        "records": records,
    }

    if typecast is not None:
        payload["typecast"] = typecast

    if return_fields_by_field_id is not None:
        payload["returnFieldsByFieldId"] = return_fields_by_field_id

    if perform_upsert is not None:
        payload["performUpsert"] = perform_upsert

    logger.info(
        f"Executing tool: update_records for table {table_id} in base {base_id}"
    )
    return await make_airtable_request("PATCH", endpoint, json_data=payload)


async def delete_records(
    base_id: str,
    table_id: str,
    record_ids: list[str],
) -> Dict[str, Any]:
    """Delete multiple records from a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to delete records from
        record_ids: List of record IDs to delete

    Returns:
        Dict containing the deletion results
    """
    endpoint = f"{base_id}/{table_id}"

    # Build query params string with multiple record IDs
    records_params = "&".join([f"records[]={record_id}" for record_id in record_ids])
    endpoint = f"{endpoint}?{records_params}"

    logger.info(
        f"Executing tool: delete_records for table {table_id} in base {base_id}"
    )
    return await make_airtable_request("DELETE", endpoint)
