""" Trace and Span related tools """
import logging
from typing import Any
from datetime import datetime, timezone

from datadog_api_client import AsyncApiClient
from datadog_api_client.model_utils import (
    UnsetType,
    unset,
)
from datadog_api_client import Configuration
from datadog_api_client.v2.api.spans_api import SpansApi
from datadog_api_client.v2.model.spans_sort import SpansSort


from .utilities import parse_human_readable_date


logger = logging.getLogger("datadog-mcp-server-trace")


async def _list_spans(
    configuration: Configuration,
    env: str | UnsetType = unset, 
    service: str | UnsetType = unset, 
    operation: str | UnsetType = unset, 
    from_time: str | UnsetType = unset, 
    to_time: str | UnsetType = unset, 
    limit: int = 100
) -> dict[str, Any]:
    """Lists spans using the dedicated Spans API GET endpoint."""
    logger.info(f"Executing tool: list_spans with env: {env}, service: {service}")
    try:
        # Build a query for spans
        query_parts = []
        if env is not unset:
            query_parts.append(f"env:{env}")
        if service is not unset:
            query_parts.append(f"service:{service}")
        if operation is not unset:
            query_parts.append(f"operation_name:{operation}")
        
        # If no specific filters, get all spans
        query = " ".join(query_parts) if query_parts else "*"
        
        # Convert time filters to proper format
        filter_from = unset
        filter_to = unset
        
        if from_time is not unset:
            if isinstance(from_time, str):
                if "ago" in from_time.lower() or from_time.lower() in ["now", "today", "yesterday"]:
                    from_timestamp = parse_human_readable_date(from_time)
                    from_dt = datetime.fromtimestamp(from_timestamp, tz=timezone.utc)
                    filter_from = from_dt.isoformat()
                else:
                    filter_from = from_time
        
        if to_time is not unset:
            if isinstance(to_time, str):
                if "ago" in to_time.lower() or to_time.lower() in ["now", "today", "yesterday"]:
                    to_timestamp = parse_human_readable_date(to_time)
                    to_dt = datetime.fromtimestamp(to_timestamp, tz=timezone.utc)
                    filter_to = to_dt.isoformat()
                else:
                    filter_to = to_time

        async with AsyncApiClient(configuration) as api_client:
            api_instance = SpansApi(api_client)
            response = await api_instance.list_spans_get(
                filter_query=query,
                filter_from=filter_from,
                filter_to=filter_to,
                sort=SpansSort("desc"),
                page_limit=min(limit, 1000)
            )
            
            return {
                "spans": [span.to_dict() for span in response.data] if response.data else [],
                "meta": response.meta.to_dict() if response.meta else {},
                "parameters": {
                    "env": env if env is not unset else None,
                    "service": service if service is not unset else None,
                    "operation": operation if operation is not unset else None,
                    "from_time": from_time if from_time is not unset else None,
                    "to_time": to_time if to_time is not unset else None,
                    "limit": limit
                }
            }
    except Exception as e:
        logger.exception(f"Error executing tool list_spans: {e}")
        return {"error": str(e), "spans": [], "meta": {}, "parameters": {}}
