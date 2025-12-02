""" mcp for hosts """
import logging
from typing import Any

# DataDog API client imports
from datadog_api_client import AsyncApiClient
from datadog_api_client.model_utils import (
    UnsetType,
    unset,
)
from datadog_api_client.v1.api.hosts_api import HostsApi
from datadog_api_client import Configuration

from .utilities import parse_human_readable_date

logger = logging.getLogger("datadog-mcp-server-hosts")


# Infrastructure Management Functions
async def _list_hosts(
    configuration: Configuration,
    filter: str | UnsetType = unset,
    sort_field: str | UnsetType = unset,
    sort_dir: str | UnsetType = unset,
    start: int | UnsetType = unset,
    count: int | UnsetType = unset,
    from_time: str | UnsetType = unset,  # human-readable date string
    include_muted_hosts_data: bool | UnsetType = unset,
    include_hosts_metadata: bool | UnsetType = unset,
) -> dict[str, Any]:
    """Provides detailed host information.
    Args:
        filter: String to filter search results.
        sort_field: Sort hosts by this field.
        sort_dir: Direction of sort. Options include ``asc`` and ``desc``.
        start: 
            Specify the starting point for the host search results. 
            For example, if you set ``count`` to 100
            and the first 100 results have already been returned,
            you can set ``start`` to ``101`` to get the next 100 results.
        count: The number of hosts to return.
        from_time: Human-readable utc time zone date string from which you want to search your hosts.
               Examples: "2024-01-15 14:30:00", "1 hour ago", "2 days ago"
        include_muted_hosts_data: 
            Include information on the muted status of hosts and when the mute expires.
        include_hosts_metadata:
            Include additional metadata about the hosts (agent_version, machine, platform, processor, etc.).
    """
    logger.info("Executing tool: list_hosts")
    try:
        # Convert human-readable date to Unix timestamp if provided
        from_timestamp = unset
        if from_time is not unset:
            from_timestamp = parse_human_readable_date(from_time)
            
        async with AsyncApiClient(configuration) as api_client:
            api_instance = HostsApi(api_client)
            response = await api_instance.list_hosts(
                filter=filter,
                sort_field=sort_field,
                sort_dir=sort_dir,
                start=start,
                count=count,
                _from=from_timestamp,
                include_muted_hosts_data=include_muted_hosts_data,
                include_hosts_metadata=include_hosts_metadata,
            )
            
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool list_hosts: {e}")
        return {"error": str(e), "host_list": []}