import contextlib
import logging
import os
import json
from typing import Any, Dict

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
import mcp.types as types
from tools import (
    create_meeting,
    get_meeting_details,
    get_past_meetings,
    get_past_meeting_details,
    get_past_meeting_participants,
)

from tools import auth_token_context
from utils import list_tools, call_tool

logger = logging.getLogger(__name__)

load_dotenv()

SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

async def list_tools() -> list[types.Tool]:
    """Define all the tools available in this server. Each tool has a name, description, and input schema for validation."""
    return [
        types.Tool(
            name="create_meeting",
            description="Create a new meeting",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_meeting_details",
            description="Get details of a meeting",
            inputSchema={
                "type": "object",
                "required": ["space_id"],
                "properties": {
                    "space_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^spaces/[a-zA-Z0-9\\-_]+$",
                        "description": "Meeting space ID (spaces/{space-id})"
                    }
                }
            },
        ),
        types.Tool(
            name="get_past_meetings",
            description="Get details for completed meetings",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of records to return"},
                    "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                    "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                }
            },
        ),
        types.Tool(
            name="get_past_meeting_details",
            description="Get details of a specific meeting",
            inputSchema={
                "type": "object",
                "required": ["conference_record_id"],
                "properties": {
                    "conference_record_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                        "description": "Conference record ID (conferenceRecords/{record-id})"
                    }
                }
            },
        ),
        types.Tool(
            name="get_past_meeting_participants",
            description="Get a list of participants from a past meeting",
            inputSchema={
                "type": "object",
                "required": ["conference_record_id"],
                "properties": {
                    "conference_record_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                        "description": "Conference record ID (conferenceRecords/{record-id})"
                    },
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of participants to return"},
                    "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                    "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                }
            },
        ),
    ]


async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """This is where we route the tool calls. Based on the name, we call the right function and return the result as text."""
    try:
        if name == "create_meeting":
            result = await create_meeting(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_meeting_details":
            result = await get_meeting_details(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meetings":
            result = await get_past_meetings(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meeting_details":
            result = await get_past_meeting_details(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meeting_participants":
            result = await get_past_meeting_participants(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@click.command()
@click.option("--port", default=SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Set up basic logging so we can see what's happening at the level we choose.
    logging.basicConfig(level=getattr(logging, log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # This is the core MCP server object that handles tool listing and calls.
    app = Server("google-meet-mcp-server")

    app.list_tools()(list_tools)
    app.call_tool()(call_tool)

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        # For SSE requests, we grab the token from headers, set it in context, and run the app with SSE transport.
        auth_token = request.headers.get('x-auth-token')
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            auth_token_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        # Similar to SSE, but for HTTP: extract token from headers, set context, and handle the request.
        headers = scope.get("headers", [])
        auth_token = next((v.decode('utf-8') for k, v in headers if k == b'x-auth-token'), None)
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        # This manages the app's lifetime: starts the session manager, logs startup, yields control, then shuts down.
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            yield
            logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
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
