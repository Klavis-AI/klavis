import os
import logging
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Dict, List, Union
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_date
import re

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn

# Add ASGI types without starlette dependency
Scope = Dict[str, Any]
Receive = Callable[[], Awaitable[Dict[str, Any]]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]

# DataDog API client imports
from datadog_api_client import Configuration, AsyncApiClient
from datadog_api_client.model_utils import (
    UnsetType,
    unset,
)
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client.v1.api.hosts_api import HostsApi
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
from datadog_api_client.v2.api.incidents_api import IncidentsApi
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.api.spans_api import SpansApi
from datadog_api_client.v2.model.logs_list_request import LogsListRequest
from datadog_api_client.v2.model.logs_list_request_page import LogsListRequestPage
from datadog_api_client.v2.model.logs_query_filter import LogsQueryFilter
from datadog_api_client.v2.model.logs_sort import LogsSort
from datadog_api_client.v2.model.spans_sort import SpansSort

load_dotenv()

# Global logging configuration
LOG_TO_FILE = os.getenv("DATADOG_MCP_LOG_TO_FILE", "false").lower() == "true"
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "datadog_mcp_server.log")
# Configure logging
def setup_logging(level: str = "INFO"):
    """Setup logging with optional file output."""
    log_level = getattr(logging, level.upper())
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if LOG_TO_FILE:
        try:
            file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            # Log the file path
            logging.getLogger("datadog-mcp-server").info(f"Logging to file: {LOG_FILE_PATH}")
        except Exception as e:
            logging.getLogger("datadog-mcp-server").warning(f"Failed to setup file logging: {e}")

# Initial logging setup
setup_logging()
logger = logging.getLogger("datadog-mcp-server")

# DataDog API constants and configuration
DATADOG_API_KEY = os.getenv("DD_API_KEY")
DATADOG_APP_KEY = os.getenv("DD_APP_KEY")
DATADOG_SITE = os.getenv("DATADOG_SITE", "datadoghq.com")

if not DATADOG_API_KEY:
    raise ValueError("DD_API_KEY environment variable is required")
if not DATADOG_APP_KEY:
    raise ValueError("DD_APP_KEY environment variable is required")

DATADOG_MCP_SERVER_PORT = int(os.getenv("DATADOG_MCP_SERVER_PORT", "8000"))

# Configure DataDog API client
configuration = Configuration()
configuration.api_key["apiKeyAuth"] = DATADOG_API_KEY
configuration.api_key["appKeyAuth"] = DATADOG_APP_KEY
if DATADOG_SITE != "datadoghq.com":
    configuration.server_variables["site"] = DATADOG_SITE
configuration.unstable_operations["list_incidents"] = True
configuration.unstable_operations["get_incident"] = True


def parse_human_readable_date(date_str: str) -> int:
    """Convert human-readable date string to Unix timestamp.
    
    Accepts formats like:
    - "2024-01-15 14:30:00"
    - "2024-01-15T14:30:00Z" 
    - "2024-01-15"
    - "1 hour ago", "2 days ago", "30 minutes ago"
    - "yesterday", "today"
    - Unix timestamps (as strings)
    """
    try:
        # Handle Unix timestamp strings
        if date_str.isdigit():
            return int(date_str)
            
        # Handle relative time expressions
        if "ago" in date_str.lower():
            now = datetime.now(timezone.utc)
            
            # Extract number and unit using regex
            match = re.match(r'(\d+)\s*(minute|hour|day|week|month)s?\s+ago', date_str.lower())
            if match:
                value, unit = match.groups()
                value = int(value)
                
                if unit == 'minute':
                    target_time = now - timedelta(minutes=value)
                elif unit == 'hour':
                    target_time = now - timedelta(hours=value)
                elif unit == 'day':
                    target_time = now - timedelta(days=value)
                elif unit == 'week':
                    target_time = now - timedelta(weeks=value)
                elif unit == 'month':
                    target_time = now - timedelta(days=value * 30)  # Approximate
                else:
                    raise ValueError(f"Unsupported time unit: {unit}")
            else:
                raise ValueError(f"Cannot parse relative time: {date_str}")
                
        # Handle common keywords
        elif date_str.lower() == "now":
            target_time = datetime.now(timezone.utc)
        elif date_str.lower() == "today":
            target_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str.lower() == "yesterday":
            target_time = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Parse standard date formats using dateutil
            target_time = parse_date(date_str)
            
        return int(target_time.timestamp())
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        raise ValueError(f"Unable to parse date: {date_str}. Supported formats: '2024-01-15', '1 hour ago', 'yesterday', Unix timestamp")


# Infrastructure Management Functions
async def list_hosts(
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
    

# Logs & Traces Functions
async def list_logs(
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


async def list_spans(
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


# Metrics & Monitoring Functions
async def list_metrics(
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

async def get_metrics(
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


async def list_monitors(
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


async def get_monitor(monitor_id: int) -> dict[str, Any]:
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


# Incident Management Functions
async def list_incidents(
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

async def get_incident(
    incident_id: str, include: list[str] | UnsetType = unset
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


# Dashboard Functions
async def list_dashboards(
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

async def get_dashboard(dashboard_id: str) -> dict[str, Any]:
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


@click.command()
@click.option(
    "--port", 
    default=DATADOG_MCP_SERVER_PORT, 
    help="Port to listen on for HTTP"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging with the specified level
    setup_logging(log_level)
    
    logger.info(f"Starting DataDog MCP Server")
    logger.info(f"Log level: {log_level}")
    logger.info(f"File logging: {'enabled' if LOG_TO_FILE else 'disabled'}")
    if LOG_TO_FILE:
        logger.info(f"Log file: {LOG_FILE_PATH}")

    # Create the MCP server instance
    app = Server("datadog-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="datadog_list_hosts",
                description="Provides detailed host information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "String to filter search results."
                        },
                        "sort_field": {
                            "type": "string",
                            "description": "Sort hosts by this field."
                        },
                        "sort_dir": {
                            "type": "string",
                            "description": (
                                "Direction of sort. Options include 'asc' and "
                                "'desc'."
                            )
                        },
                        "start": {
                            "type": "integer",
                            "description": (
                                "Specify the starting point for the host search "
                                "results."
                            )
                        },
                        "count": {
                            "type": "integer",
                            "description": "The number of hosts to return."
                        },
                        "from_time": {
                            "type": "string",
                            "description": (
                                "Human-readable utc time zone date string from "
                                "which you want to search your hosts."
                            )
                        },
                        "include_muted_hosts_data": {
                            "type": "boolean",
                            "description": (
                                "Include information on the muted status of "
                                "hosts and when the mute expires."
                            )
                        },
                        "include_hosts_metadata": {
                            "type": "boolean",
                            "description": (
                                "Include additional metadata about the hosts."
                            )
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_get_logs",
                description="Retrieves a list of logs based on query filters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query for logs (default: '*')."
                            ),
                            "default": "*"
                        },
                        "from_time": {
                            "type": "string",
                            "description": (
                                "Start time in ISO format or relative "
                                "(default: 1 hour ago)."
                            )
                        },
                        "to_time": {
                            "type": "string",
                            "description": (
                                "End time in ISO format or relative "
                                "(default: now)."
                            )
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                "Maximum number of logs to return "
                                "(default: 100, max: 1000)."
                            ),
                            "default": 100
                        },
                        "sort": {
                            "type": "string",
                            "description": (
                                "Sort order: 'asc' or 'desc' "
                                "(default: 'desc')."
                            ),
                            "default": "desc"
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_list_spans",
                description=(
                    "Lists spans using the dedicated Spans API GET endpoint."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "env": {
                            "type": "string",
                            "description": "Filter by the environment."
                        },
                        "service": {
                            "type": "string",
                            "description": "Filter spans by service name."
                        },
                        "operation": {
                            "type": "string",
                            "description": "Filter spans by operation name."
                        },
                        "from_time": {
                            "type": "string",
                            "description": (
                                "Start time in ISO format or relative "
                                "(default: 1 hour ago)."
                            )
                        },
                        "to_time": {
                            "type": "string",
                            "description": (
                                "End time in ISO format or relative "
                                "(default: now)."
                            )
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                "Maximum number of spans to return "
                                "(default: 100, max: 1000)."
                            ),
                            "default": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_list_metrics",
                description=(
                    "Retrieves a list of available metrics in your environment."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Query string to filter metrics (default: '*')."
                            ),
                            "default": "*"
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_get_metrics",
                description="Queries timeseries metrics data.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The metric query "
                                "(e.g., 'avg:system.cpu.idle{*}')."
                            )
                        },
                        "from_time": {
                            "type": "string",
                            "description": (
                                "Start time as Unix timestamp or relative "
                                "(default: 1 hour ago)."
                            )
                        },
                        "to_time": {
                            "type": "string",
                            "description": (
                                "End time as Unix timestamp or relative "
                                "(default: now)."
                            )
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_list_monitors",
                description="Retrieves monitors and their configurations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "group_states": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by monitor group states."
                        },
                        "name": {
                            "type": "string",
                            "description": "Filter monitors by name."
                        },
                        "monitor_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter monitors by tags."
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_get_monitor",
                description=(
                    "Retrieves details for a specific monitor by the id."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["monitor_id"],
                    "properties": {
                        "monitor_id": {
                            "type": "integer",
                            "description": (
                                "The ID of the monitor to retrieve."
                            )
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_list_incidents",
                description="Retrieves a list of ongoing incidents.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_size": {
                            "type": "integer",
                            "description": (
                                "Number of incidents per page "
                                "(default: 10, max: 100)."
                            ),
                            "default": 10
                        },
                        "page_offset": {
                            "type": "integer",
                            "description": (
                                "Page offset for pagination (default: 0)."
                            ),
                            "default": 0
                        },
                        "include": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Include related resources."
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_get_incident",
                description="Retrieves details for a specific incident.",
                inputSchema={
                    "type": "object",
                    "required": ["incident_id"],
                    "properties": {
                        "incident_id": {
                            "type": "string",
                            "description": (
                                "The ID of the incident to retrieve."
                            )
                        },
                        "include": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Include related resources."
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_list_dashboards",
                description=(
                    "Discovers available dashboards and their context."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter_shared": {
                            "type": "boolean",
                            "description": "Filter by shared status."
                        },
                        "filter_deleted": {
                            "type": "boolean",
                            "description": "Include deleted dashboards."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of dashboards to return."
                        },
                        "start": {
                            "type": "integer",
                            "description": (
                                "Starting index for returned dashboards."
                            )
                        }
                    }
                }
            ),
            types.Tool(
                name="datadog_get_dashboard",
                description="Retrieves details for a specific dashboard.",
                inputSchema={
                    "type": "object",
                    "required": ["dashboard_id"],
                    "properties": {
                        "dashboard_id": {
                            "type": "string",
                            "description": (
                                "The ID of the dashboard to retrieve."
                            )
                        }
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[
        types.TextContent | types.ImageContent | types.EmbeddedResource
    ]:
        if name == "datadog_list_hosts":
            result = await list_hosts(
                filter=arguments.get("filter", unset),
                sort_field=arguments.get("sort_field", unset),
                sort_dir=arguments.get("sort_dir", unset),
                start=arguments.get("start", unset),
                count=arguments.get("count", unset),
                from_time=arguments.get("from_time", unset),
                include_muted_hosts_data=arguments.get(
                    "include_muted_hosts_data", unset
                ),
                include_hosts_metadata=arguments.get(
                    "include_hosts_metadata", unset
                ),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_get_logs":
            result = await list_logs(
                query=arguments.get("query", "*"),
                from_time=arguments.get("from_time", unset),
                to_time=arguments.get("to_time", unset),
                limit=arguments.get("limit", 100),
                sort=arguments.get("sort", "desc"),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_list_spans":
            result = await list_spans(
                env=arguments.get("env", unset),
                service=arguments.get("service", unset),
                operation=arguments.get("operation", unset),
                from_time=arguments.get("from_time", unset),
                to_time=arguments.get("to_time", unset),
                limit=arguments.get("limit", 100),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_list_metrics":
            result = await list_metrics(
                query=arguments.get("query", "*"),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_get_metrics":
            result = await get_metrics(
                query=arguments["query"],
                from_time=arguments.get("from_time", unset),
                to_time=arguments.get("to_time", unset),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_list_monitors":
            result = await list_monitors(
                group_states=arguments.get("group_states", unset),
                name=arguments.get("name", unset),
                monitor_tags=arguments.get("monitor_tags", unset),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_get_monitor":
            result = await get_monitor(
                monitor_id=arguments["monitor_id"]
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_list_incidents":
            result = await list_incidents(
                page_size=arguments.get("page_size", 10),
                page_offset=arguments.get("page_offset", 0),
                include=arguments.get("include", unset),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_get_incident":
            result = await get_incident(
                incident_id=arguments["incident_id"],
                include=arguments.get("include", unset),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_list_dashboards":
            result = await list_dashboards(
                filter_shared=arguments.get("filter_shared", unset),
                filter_deleted=arguments.get("filter_deleted", unset),
                count=arguments.get("count", unset),
                start=arguments.get("start", unset),
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        elif name == "datadog_get_dashboard":
            result = await get_dashboard(
                dashboard_id=arguments["dashboard_id"]
            )
            return [
                types.TextContent(type="text", text=str(result))
            ]
        # ...existing code...

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            # Takes the incoming HTTP request and upgrades it to an SSE connection
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: dict[str, Any], 
        receive: Callable[[], Awaitable[dict[str, Any]]], 
        send: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create a FastAPI application with routes for both transports
    fastapi_app = FastAPI(
        title="DataDog MCP Server",
        description="MCP Server for DataDog API integration",
        version="1.0.0",
        lifespan=lifespan,
    )

    # SSE endpoint, Establish SSE connection
    @fastapi_app.get("/sse")
    async def sse_endpoint(request: Request):
        return await handle_sse(request)

    # Mount SSE message handling
    fastapi_app.mount("/messages/", sse.handle_post_message)
    
    # Mount StreamableHTTP, for HTTP MCP requests 
    fastapi_app.mount("/mcp", handle_streamable_http)

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    uvicorn.run(fastapi_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
