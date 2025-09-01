""" Incident Management Functions """
import logging
from typing import Any

# DataDog API client imports
from datadog_api_client import AsyncApiClient
from datadog_api_client.model_utils import (
    UnsetType,
    unset,
)
from datadog_api_client import Configuration
from datadog_api_client.v2.api.incidents_api import IncidentsApi


logger = logging.getLogger("datadog-mcp-server-incidents")


async def _list_incidents(
    configuration: Configuration,
    page_size: int = 10, 
    page_offset: int = 0, 
    include: list[str] | UnsetType = unset, 
) -> dict[str, Any]:
    """Retrieves a list of ongoing incidents."""
    logger.info("Executing tool: list_incidents")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = IncidentsApi(api_client)
            response = await api_instance.list_incidents(
                page_size=min(page_size, 100),
                page_offset=page_offset,
                include=include,
            )
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool list_incidents: {e}")
        return {"error": str(e), "data": []}


async def _get_incident(
    configuration: Configuration,
    incident_id: str,
    include: list[str] | UnsetType = unset
) -> dict[str, Any]:
    """Retrieves details for a specific incident."""
    logger.info(f"Executing tool: get_incident with incident_id: {incident_id}")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = IncidentsApi(api_client)
            response = await api_instance.get_incident(
                incident_id=incident_id,
                include=include
            )
            
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool get_incident: {e}")
        return {"error": str(e), "data": None}