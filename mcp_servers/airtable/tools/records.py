import logging
from typing import Any, Dict

from .base import make_airtable_request

# Configure logging
logger = logging.getLogger(__name__)


async def list_records(base_id: str, table_id: str) -> Dict[str, Any]:
    """Get all records from a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table to get records from
    """
    endpoint = f"{base_id}/{table_id}"

    try:
        logger.info(
            f"Executing tool: list_records for table {table_id} in base {base_id}"
        )
        return await make_airtable_request("GET", endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool list_records: {e}")
        raise e


async def get_record(base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
    """Get a single record from a table.

    Args:
        base_id: ID of the base containing the table
        table_id: ID or name of the table containing the record
        record_id: ID of the record to retrieve
    """
    endpoint = f"{base_id}/{table_id}/{record_id}"

    try:
        logger.info(
            f"Executing tool: get_record for record {record_id} in table {table_id}, base {base_id}"
        )
        return await make_airtable_request("GET", endpoint)
    except Exception as e:
        logger.exception(f"Error executing tool get_record: {e}")
        raise e
