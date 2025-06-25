import logging
from typing import Any, Dict, Optional
from .base import make_http_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_field_values(
    person_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    list_entry_id: Optional[int] = None,
    page_size: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """Get field values for a specific entity."""
    logger.info("Executing tool: get_field_values")
    try:
        params = {
            "page_size": page_size
        }
        if person_id:
            params["person_id"] = person_id
        if organization_id:
            params["organization_id"] = organization_id
        if opportunity_id:
            params["opportunity_id"] = opportunity_id
        if list_entry_id:
            params["list_entry_id"] = list_entry_id
        if page_token:
            params["page_token"] = page_token
        
        return await make_http_request("GET", "/field-values", params=params)
    except Exception as e:
        logger.exception(f"Error executing tool get_field_values: {e}")
        raise e

async def create_field_value(
    field_id: int,
    entity_id: int,
    value: Any,
    list_entry_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new field value."""
    logger.info(f"Executing tool: create_field_value with field_id: {field_id}, entity_id: {entity_id}")
    try:
        data = {
            "field_id": field_id,
            "entity_id": entity_id,
            "value": value
        }
        if list_entry_id:
            data["list_entry_id"] = list_entry_id
        
        return await make_http_request("POST", "/field-values", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool create_field_value: {e}")
        raise e

async def update_field_value(
    field_value_id: int,
    value: Any
) -> Dict[str, Any]:
    """Update an existing field value."""
    logger.info(f"Executing tool: update_field_value with field_value_id: {field_value_id}")
    try:
        data = {
            "value": value
        }
        return await make_http_request("PUT", f"/field-values/{field_value_id}", data=data)
    except Exception as e:
        logger.exception(f"Error executing tool update_field_value: {e}")
        raise e

async def delete_field_value(field_value_id: int) -> Dict[str, Any]:
    """Delete a field value."""
    logger.info(f"Executing tool: delete_field_value with field_value_id: {field_value_id}")
    try:
        return await make_http_request("DELETE", f"/field-values/{field_value_id}")
    except Exception as e:
        logger.exception(f"Error executing tool delete_field_value: {e}")
        raise e 