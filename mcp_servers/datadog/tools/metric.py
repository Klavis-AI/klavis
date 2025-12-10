""" Metrics related tools """
import logging
from typing import Any

from datadog_api_client.model_utils import UnsetType, unset
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client import AsyncApiClient, Configuration

from .utilities import parse_human_readable_date

logger = logging.getLogger("datadog-mcp-server-metrics")


# Metrics & Monitoring Functions
async def _list_metrics(
    configuration: Configuration,
    query: str = "*",
) -> dict[str, Any]:
    """Retrieves a list of available metrics in your environment."""
    logger.info("Executing tool: list_metrics")
    try:
        async with AsyncApiClient(configuration) as api_client:
            api_instance = MetricsApi(api_client)
            response = await api_instance.list_metrics(q=query)
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool list_metrics: {e}")
        return {"error": str(e), "metrics": []}


async def _get_metrics(
    configuration: Configuration,
    query: str, 
    from_time: str | UnsetType = unset, 
    to_time: str | UnsetType = unset
) -> dict[str, Any]:
    """ Queries timeseries metrics data.
        Args:
            query (str): The query to filter metrics.
                Example: "avg:system.cpu.idle{*}"
            from_time (str | UnsetType): The start time for the query.
            to_time (str | UnsetType): The end time for the query.
    """
    logger.info(f"Executing tool: get_metrics with query: {query}")
    try:
        # Use human-readable date parser for time arguments
        if from_time is unset:
            from_time = "1 hour ago"
            from_time_parsed = parse_human_readable_date(from_time)
        elif isinstance(from_time, str):
            from_time_parsed = parse_human_readable_date(from_time)
        else:
            from_time_parsed = int(from_time)

        if to_time is unset:
            to_time = "now"
            to_time_parsed = parse_human_readable_date(to_time)
        elif isinstance(to_time, str):
            to_time_parsed = parse_human_readable_date(to_time)
        else:
            to_time_parsed = int(to_time)

        async with AsyncApiClient(configuration) as api_client:
            api_instance = MetricsApi(api_client)
            response = await api_instance.query_metrics(
                _from=int(from_time_parsed),
                to=int(to_time_parsed),
                query=query
            )
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool get_metrics: {e}")
        return {"error": str(e), "series": []}