""" Monitor-related tools for the Datadog agent. """
import logging
from typing import Any

# DataDog API client imports
from datadog_api_client import AsyncApiClient
from datadog_api_client.model_utils import (
    UnsetType,
    unset,
)
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client import Configuration


logger = logging.getLogger("datadog-mcp-server-monitors")


async def _list_monitors(
    configuration: Configuration,
    group_states: list[str] | UnsetType = unset, 
    name: str | UnsetType = unset, 
    monitor_tags: list[str] | UnsetType = unset
) -> dict[str, Any]:
    """Retrieves monitors and their configurations."""
    logger.info("Executing tool: list_monitors")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            response = await api_instance.list_monitors(
                group_states=",".join(group_states) if group_states is not unset else unset,
                name=name,
                # tags=",".join(tags) if tags is not unset else unset,
                monitor_tags=",".join(monitor_tags) if monitor_tags is not unset else unset,
            )
            
            return {
                "monitors": [monitor.to_dict() for monitor in response] if response else []
            }
    except Exception as e:
        logger.exception(f"Error executing tool list_monitors: {e}")
        return {"error": str(e), "monitors": []}


async def _get_monitor(
        configuration: Configuration,
        monitor_id: int) -> dict[str, Any]:
    """Retrieves details for a specific monitor by the id."""
    logger.info(f"Executing tool: get_monitor with monitor_id: {monitor_id}")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = MonitorsApi(api_client)
            response = await api_instance.get_monitor(monitor_id=monitor_id)
            
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool get_monitor: {e}")
        return {"error": str(e), "monitor": None}