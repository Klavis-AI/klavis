""" Dashboard Functions """
import logging
from typing import Any

from datadog_api_client.model_utils import UnsetType, unset
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client import AsyncApiClient, Configuration


logger = logging.getLogger("datadog-mcp-server-dashboards")


async def _list_dashboards(
    configuration: Configuration,
    filter_shared: bool | UnsetType = unset, 
    filter_deleted: bool | UnsetType = unset,
    count: int | UnsetType = unset,
    start: int | UnsetType = unset,
) -> dict[str, Any]:
    """ Discovers available dashboards and their context.
    Args:
        filter_shared: When ``true`` , this query only returns shared custom created
                or cloned dashboards.
        filter_deleted: When ``true`` , this query only returns deleted dashboards.
        count: The number of dashboards to return (default: 10).
        start: The starting index for the returned dashboards (default: 0).
    """
    logger.info("Executing tool: list_dashboards")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = DashboardsApi(api_client)
            response = await api_instance.list_dashboards(
                filter_shared=filter_shared,
                filter_deleted=filter_deleted
            )
            
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool list_dashboards: {e}")
        return {"error": str(e), "dashboards": []}


async def _get_dashboard(configuration:Configuration, dashboard_id: str) -> dict[str, Any]:
    """Retrieves details for a specific dashboard.
        Args:
            dashboard_id : The ID of the dashboard. we can get it from list_dashboards()
    """
    logger.info(f"Executing tool: get_dashboard with dashboard_id: {dashboard_id}")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = DashboardsApi(api_client)
            response = await api_instance.get_dashboard(dashboard_id=dashboard_id)
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool get_dashboard: {e}")
        return {"error": str(e), "data": None}