import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import (
    username_context,
    secret_context,
    send_events,
    get_projects,
    get_events,
    get_event_properties,
    get_event_property_values,
    run_funnels_query,
    run_frequency_query,
    run_retention_query,
    run_segmentation_query,
)

logger = logging.getLogger(__name__)

load_dotenv()

MIXPANEL_MCP_SERVER_PORT = int(os.getenv("MIXPANEL_MCP_SERVER_PORT", "5000"))

def extract_credentials(request_or_scope) -> Dict[str, str]:
    """Extract service account credentials from x-auth-data header."""
    username = os.getenv("MIXPANEL_SERVICE_ACCOUNT_USERNAME")
    secret = os.getenv("MIXPANEL_SERVICE_ACCOUNT_SECRET")
    
    auth_data = None
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
    if hasattr(request_or_scope, 'headers'):
        # SSE request object
        auth_data_header = request_or_scope.headers.get(b'x-auth-data')
        if auth_data_header:
            auth_data = base64.b64decode(auth_data_header).decode('utf-8')
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        auth_data_header = headers.get(b'x-auth-data')
        if auth_data_header:
            auth_data = base64.b64decode(auth_data_header).decode('utf-8')
    
    # If no credentials from environment, try to parse from auth_data (from prod)
    if auth_data and (not username or not secret):
        try:
            # Parse the JSON auth data to extract credentials
            auth_json = json.loads(auth_data)
            username = auth_json.get('serviceaccount_username', '') or username
            secret = auth_json.get('serviceaccount_secret', '') or secret
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse auth data JSON: {e}")
    
    return {
        'username': username or "",
        'secret': secret or "",
    }

@click.command()
@click.option("--port", default=MIXPANEL_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("mixpanel-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="mixpanel_send_events",
                description="Send events to Mixpanel using the /import endpoint with Service Account authentication. Send batches of events with automatic deduplication support. Each event requires time, distinct_id, and $insert_id for proper processing.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "events"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The Mixpanel project ID to import events to. Use get_projects tool to find available project IDs.",
                        },
                        "events": {
                            "type": "array",
                            "description": "Array of event objects to import",
                            "items": {
                                "type": "object",
                                "required": ["event"],
                                "properties": {
                                    "event": {
                                        "type": "string",
                                        "description": "The name of the event (e.g., 'Page View', 'Button Click', 'Purchase')",
                                    },
                                    "properties": {
                                        "type": "object",
                                        "description": "Event properties. Will auto-generate time and $insert_id if not provided.",
                                        "additionalProperties": True,
                                    },
                                    "distinct_id": {
                                        "type": "string",
                                        "description": "Unique identifier for the user performing the event (empty string if anonymous)",
                                    },
                                },
                            },
                            "minItems": 1,
                            "maxItems": 2000,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_EVENT"}),
            ),
            types.Tool(
                name="mixpanel_get_events",
                description="Get event names for the given Mixpanel project. Retrieves all event names that have been tracked in the specified project, useful for discovering what events are available for analysis.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The Mixpanel project ID to get event names for",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_EVENT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_get_event_properties",
                description=(
                    "Get event properties for the given event and Mixpanel project. "
                    "These are the properties available when filtering and aggregating in queries."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "event"],
                    "properties": {
                        "project_id": {
                            "type": ["string", "integer"],
                            "description": "The Mixpanel project ID",
                        },
                        "event": {
                            "type": "string",
                            "description": "Event name (e.g., 'AI Prompt Sent')",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_EVENT_METADATA", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_get_event_property_values",
                description=(
                    "Get event property values for the given event name, Mixpanel project, and property name. "
                    "These are the values that are available for the given event property."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "event", "property"],
                    "properties": {
                        "project_id": {
                            "type": ["string", "integer"],
                            "description": "The Mixpanel project ID",
                        },
                        "event": {
                            "type": "string",
                            "description": "Event name (e.g., 'AI Prompt Sent')",
                        },
                        "property": {
                            "type": "string",
                            "description": "Property name (e.g., 'utm_source')",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_EVENT_METADATA", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_run_funnels_query",
                description=(
                    "Run a funnel query. This measures the conversion rate of a user journey."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["events", "from_date", "to_date", "count_type", "project_id"],
                    "properties": {
                        "events": {
                            "type": ["array", "string"],
                            "description": "Ordered steps of the funnel. Either an array of step objects or a JSON-encoded string.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string"},
                                    "step_label": {"type": "string"}
                                },
                                "required": ["event"],
                                "additionalProperties": True
                            }
                        },
                        "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "to_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "count_type": {"type": "string", "enum": ["unique", "general"], "default": "unique"},
                        "project_id": {"type": ["string", "integer"]}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_run_segmentation_query",
                description=(
                    "The segmentation tool (run_segmentation_query) is a flexible way to slice and dice your event stream for deeper insights. "
                    "At a high level, it lets you: "
                    "• Select which events to analyze (e.g. a single event name or all events via \"$any_event\"). "
                    "• Specify a time window, defaulting to the last 30 days unless you override from_date/to_date. "
                    "• Bucket your results into time intervals (day, hour, or month) so you can see trends over time. "
                    "• Choose your metric: "
                    "general: raw event counts, i.e. how many times the event fired. "
                    "unique: unique user counts, i.e. how many distinct users triggered the event. "
                    "• Filter the data with arbitrary boolean expressions (where)—for example, only count purchases above $100 or sessions where plan == \"Pro\". "
                    "• Segment (group) the results by any property or computed key (on), from simple string or numeric properties to math‐ or typecast‐based buckets. "
                    "• Apply numerical aggregations when grouping on a numeric field: "
                    "sum: total up the values in each segment (e.g. total revenue per day). "
                    "average: compute the mean value in each segment (e.g. average session length by plan). "
                    "buckets: build a histogram of value ranges (e.g. count of purchases falling into each revenue bracket)."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "event"],
                    "properties": {
                        "project_id": {
                            "type": ["string", "integer"],
                            "description": "The Mixpanel project ID",
                        },
                        "event": {
                            "type": "string",
                            "description": "Event name to analyze.",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD. Defaults to 30 days ago.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD. Defaults to today.",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["hour", "day", "month"],
                            "default": "day",
                            "description": "Granularity of time buckets.",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["general", "unique"],
                            "default": "general",
                            "description": "Metric for counts (raw vs distinct users).",
                        },
                        "where": {
                            "type": "string",
                            "description": "Optional boolean expression filter",
                        },
                        "on": {
                            "type": "string",
                            "description": "Optional segmentation property or computed key",
                        },
                        "numerical_aggregation": {
                            "type": "string",
                            "enum": ["sum", "average", "buckets"],
                            "description": "Optional numeric aggregation when grouping by a numeric field.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_run_retention_query",
                description=(
                    "The retention tool tracks user engagement over time and supports cohort analysis. "
                    "It lets you select a born event ('born_event') and a retention event ('event'), specify a time window, "
                    "choose retention type (birth or compounded), bucket by day/week/month, choose a metric (general or unique), "
                    "filter the data with boolean expressions ('where'), and segment results by any property ('on')."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "event"],
                    "properties": {
                        "project_id": {
                            "type": ["string", "integer"],
                            "description": "The Mixpanel project ID",
                        },
                        "event": {
                            "type": "string",
                            "description": "The retention event to analyze",
                        },
                        "born_event": {
                            "type": "string",
                            "description": "The born/cohort event. Defaults to event if not provided",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD. Defaults to 30 days ago.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD. Defaults to today.",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["day", "week", "month"],
                            "default": "day",
                            "description": "Granularity of cohorts/time buckets.",
                        },
                        "retention_type": {
                            "type": "string",
                            "enum": ["birth", "compounded"],
                            "default": "birth",
                            "description": "Retention analysis type.",
                        },
                        "interval_count": {
                            "type": "integer",
                            "description": "Number of intervals to include.",
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["general", "unique"],
                            "default": "unique",
                            "description": "Metric for counts (raw vs distinct users).",
                        },
                        "where": {
                            "type": "string",
                            "description": "Optional boolean expression filter",
                        },
                        "on": {
                            "type": "string",
                            "description": "Optional segmentation property or computed key",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_run_frequency_query",
                description=(
                    "The frequency tool (run_frequency_query) is a powerful way to track user engagement over time and do cohort analysis. "
                    "It lets you:\n"
                    "• Select which events to analyze both for born event \"born_event\" param and retention event \"event\" param.\n"
                    "• Specify a time window, defaulting to the last 30 days unless user specifies otherwise.\n"
                    "• Choose your unit:\n"
                    "  - day\n"
                    "  - week\n"
                    "  - month\n"
                    "• Choose your addiction_unit:\n"
                    "  - hour\n"
                    "  - day\n"
                    "  - week\n"
                    "• Choose your metric:\n"
                    "  - general: raw event counts, i.e. how many times the event fired.\n"
                    "  - unique: unique user counts, i.e. how many distinct users triggered the event.\n"
                    "• Filter the data with arbitrary boolean expressions (where)—for example, only count purchases above $100 or sessions where properties[\"plan\"] == \"Pro\".\n"
                    "• Segment (group) the results by any property or computed key (on), from simple string or numeric properties to math‐ or typecast‐based buckets."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["project_id", "event"],
                    "properties": {
                        "project_id": {
                            "type": ["string", "integer"],
                            "description": "The Mixpanel project ID",
                        },
                        "event": {
                            "type": "string",
                            "description": "The retention event to analyze",
                        },
                        "born_event": {
                            "type": "string",
                            "description": "The born/cohort event. Defaults to event if not provided",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD. Defaults to 30 days ago.",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD. Defaults to today.",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["day", "week", "month"],
                            "default": "day",
                            "description": "Granularity of cohorts/time buckets.",
                        },
                        "addiction_unit": {
                            "type": "string",
                            "enum": ["hour", "day", "week"],
                            "default": "hour",
                            "description": "Sub-interval used for frequency bins.",
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["general", "unique"],
                            "default": "unique",
                            "description": "Metric for counts (raw vs distinct users).",
                        },
                        "where": {
                            "type": "string",
                            "description": "Optional boolean expression filter",
                        },
                        "on": {
                            "type": "string",
                            "description": "Optional segmentation property or computed key",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="mixpanel_get_projects",
                description="Get all projects that are accessible to the current service account user. Use this tool to discover available projects and their IDs, which are required for event tracking and user profile operations.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "MIXPANEL_PROJECT", "readOnlyHint": True}),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "mixpanel_send_events":
            project_id = arguments.get("project_id")
            events = arguments.get("events")
            
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
                
            if not events:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: events parameter is required",
                    )
                ]
            
            try:
                result = await send_events(project_id, events)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mixpanel_get_projects":
            try:
                result = await get_projects()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        

        elif name == "mixpanel_get_event_properties":
            project_id = arguments.get("project_id")
            event = arguments.get("event")

            if not project_id:
                return [types.TextContent(type="text", text="Error: project_id parameter is required")]
            if not event:
                return [types.TextContent(type="text", text="Error: event parameter is required")]

            try:
                result = await get_event_properties(str(project_id), event)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mixpanel_get_event_property_values":
            project_id = arguments.get("project_id")
            event = arguments.get("event")
            property_name = arguments.get("property")

            if not project_id:
                return [types.TextContent(type="text", text="Error: project_id parameter is required")]
            if not event:
                return [types.TextContent(type="text", text="Error: event parameter is required")]
            if not property_name:
                return [types.TextContent(type="text", text="Error: property parameter is required")]

            try:
                result = await get_event_property_values(str(project_id), event, property_name)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mixpanel_run_funnels_query":
            project_id = arguments.get("project_id")
            events = arguments.get("events")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            count_type = arguments.get("count_type", "unique")

            if not project_id:
                return [types.TextContent(type="text", text="Error: project_id parameter is required")]
            if not events:
                return [types.TextContent(type="text", text="Error: events parameter is required")]
            if not from_date or not to_date:
                return [types.TextContent(type="text", text="Error: from_date and to_date are required")]

            try:
                result = await run_funnels_query(
                    project_id=str(project_id),
                    events=events,
                    from_date=from_date,
                    to_date=to_date,
                    count_type=count_type,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        
        elif name == "mixpanel_get_events":
            project_id = arguments.get("project_id")
            
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
            
            try:
                result = await get_events(project_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mixpanel_run_frequency_query":
            project_id = arguments.get("project_id")
            event = arguments.get("event")
            born_event = arguments.get("born_event")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            unit = arguments.get("unit", "day")
            addiction_unit = arguments.get("addiction_unit", "hour")
            metric = arguments.get("metric", "unique")
            where = arguments.get("where")
            on = arguments.get("on")

            if not project_id:
                return [
                    types.TextContent(type="text", text="Error: project_id parameter is required")
                ]
            if not event:
                return [
                    types.TextContent(type="text", text="Error: event parameter is required")
                ]

            try:
                result = await run_frequency_query(
                    project_id=project_id,
                    event=event,
                    born_event=born_event,
                    from_date=from_date,
                    to_date=to_date,
                    unit=unit,
                    addiction_unit=addiction_unit,
                    metric=metric,
                    where=where,
                    on=on,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mixpanel_run_retention_query":
            project_id = arguments.get("project_id")
            event = arguments.get("event")
            born_event = arguments.get("born_event")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            unit = arguments.get("unit", "day")
            retention_type = arguments.get("retention_type", "birth")
            interval_count = arguments.get("interval_count")
            metric = arguments.get("metric", "unique")
            where = arguments.get("where")
            on = arguments.get("on")

            if not project_id:
                return [
                    types.TextContent(type="text", text="Error: project_id parameter is required")
                ]
            if not event:
                return [
                    types.TextContent(type="text", text="Error: event parameter is required")
                ]

            try:
                result = await run_retention_query(
                    project_id=str(project_id),
                    event=event,
                    born_event=born_event,
                    from_date=from_date,
                    to_date=to_date,
                    unit=unit,
                    retention_type=retention_type,
                    interval_count=interval_count,
                    metric=metric,
                    where=where,
                    on=on,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "mixpanel_run_segmentation_query":
            project_id = arguments.get("project_id")
            event = arguments.get("event")
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            unit = arguments.get("unit", "day")
            metric_type = arguments.get("type", "general")
            where = arguments.get("where")
            on = arguments.get("on")
            numerical_aggregation = arguments.get("numerical_aggregation")

            if not project_id:
                return [
                    types.TextContent(type="text", text="Error: project_id parameter is required")
                ]
            if not event:
                return [
                    types.TextContent(type="text", text="Error: event parameter is required")
                ]

            try:
                result = await run_segmentation_query(
                    project_id=str(project_id),
                    event=event,
                    from_date=from_date,
                    to_date=to_date,
                    unit=unit,
                    type=metric_type,
                    where=where,
                    on=on,
                    numerical_aggregation=numerical_aggregation,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract credentials from headers
        credentials = extract_credentials(request)
        
        # Set the credentials in context for this request
        username_token = username_context.set(credentials['username'])
        secret_token = secret_context.set(credentials['secret'])
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            username_context.reset(username_token)
            secret_context.reset(secret_token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract credentials from headers
        credentials = extract_credentials(scope)
        
        # Set the credentials in context for this request
        username_token = username_context.set(credentials['username'])
        secret_token = secret_context.set(credentials['secret'])
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            username_context.reset(username_token)
            secret_context.reset(secret_token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()