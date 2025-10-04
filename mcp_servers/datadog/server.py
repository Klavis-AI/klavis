""" DataDog MCP Server with dual transport: SSE and StreamableHTTP """
import os
import logging
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Dict
from functools import partial
import click
from dotenv import load_dotenv

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn

# DataDog API client imports
from datadog_api_client import Configuration
from datadog_api_client.model_utils import unset

# load all mcp funcitons
from tools import setup_logging
from tools import (
    _get_dashboard, _list_dashboards,
    _list_hosts,
    _list_incidents, _get_incident,
    _list_logs,
    _list_metrics, _get_metrics,
    _list_monitors, _get_monitor,
    _list_spans)

# Add ASGI types without starlette dependency
Scope = Dict[str, Any]
Receive = Callable[[], Awaitable[Dict[str, Any]]]
Send = Callable[[Dict[str, Any]], Awaitable[None]]


load_dotenv()


# Global logging configuration
LOG_TO_FILE = os.getenv("DATADOG_MCP_LOG_TO_FILE", "false").lower() == "true"
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "datadog_mcp_server.log")

# Initial logging setup
setup_logging(
    level = "INFO",
    log_to_file = True,
    log_file_path = "datadog_mcp_server.log")
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

# Public wrappers for internal functions with configuration pre-set
list_dashboards = partial(_list_dashboards, configuration)
get_dashboard = partial(_get_dashboard, configuration)
list_hosts = partial(_list_hosts, configuration)
list_incidents = partial(_list_incidents, configuration)
get_incident = partial(_get_incident, configuration)
list_logs = partial(_list_logs, configuration)
list_metrics = partial(_list_metrics, configuration)
get_metrics = partial(_get_metrics, configuration)
list_monitors = partial(_list_monitors, configuration)
get_monitor = partial(_get_monitor, configuration)
list_spans = partial(_list_spans, configuration)

# dashboard functions
get_dashboard = partial(_get_dashboard, configuration)
list_dashboards = partial(_list_dashboards, configuration)


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
