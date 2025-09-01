""" Logs & Traces Functions """
import logging
from typing import Any

from datadog_api_client.model_utils import UnsetType, unset
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.model.logs_list_request import LogsListRequest
from datadog_api_client.v2.model.logs_list_request_page import LogsListRequestPage
from datadog_api_client.v2.model.logs_query_filter import LogsQueryFilter
from datadog_api_client.v2.model.logs_sort import LogsSort
from datadog_api_client import AsyncApiClient, Configuration
from datetime import datetime, timezone

from .utilities import parse_human_readable_date

logger = logging.getLogger("datadog-mcp-server-logs")


async def _list_logs(
    configuration: Configuration,
    query: str = "*", 
    from_time: str | UnsetType = unset, 
    to_time: str | UnsetType = unset, 
    limit: int = 100, 
    sort: str = "desc"
) -> dict[str, Any]:
    """Retrieves a list of logs based on query filters."""
    logger.info(f"Executing tool: list_logs with\
                query: {query},\
                from_time: {from_time},\
                to_time: {to_time},\
                limit: {limit}")
    try:
        # Build the filter with proper time formatting
        filter_kwargs = {"query": query}
        
        # Add time filters if provided (expects ISO format or relative time)
        if from_time is not unset:
            if isinstance(from_time, str):
                # If it looks like a relative time, convert to ISO
                if "ago" in from_time.lower() or from_time.lower() in ["now", "today", "yesterday"]:
                    from_timestamp = parse_human_readable_date(from_time)
                    from_dt = datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                    filter_kwargs["_from"] = from_dt.isoformat()
                else:
                    # Assume it's already in ISO format
                    filter_kwargs["_from"] = from_time
        
        if to_time is not unset:
            if isinstance(to_time, str):
                # If it looks like a relative time, convert to ISO
                if "ago" in to_time.lower() or to_time.lower() in ["now", "today", "yesterday"]:
                    to_timestamp = parse_human_readable_date(to_time)
                    to_dt = datetime.fromtimestamp(to_timestamp, tz=timezone.utc)
                    filter_kwargs["to"] = to_dt.isoformat()
                else:
                    # Assume it's already in ISO format
                    filter_kwargs["to"] = to_time

        simple_body = LogsListRequest(
            filter=LogsQueryFilter(**filter_kwargs),
            sort=LogsSort("desc" if sort.lower() == "desc" else "asc"),
            page=LogsListRequestPage(limit=min(limit, 1000))
        )
        
        async with AsyncApiClient(configuration) as api_client:
            api_instance = LogsApi(api_client)
            response = await api_instance.list_logs(body=simple_body)
            return response.to_dict()
    except Exception as e:
        logger.exception(f"Error executing tool list_logs: {e}")
        return {"error": str(e), "data": [], "meta": {}, "links": {}}
