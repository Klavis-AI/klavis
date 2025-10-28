import contextlib
import base64
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import click
import mcp.types as types
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    auth_token_context,
    extract_access_token,
    get_transcripts_by_user,
    get_call_transcripts,
    get_extensive_data,
    list_calls,
    add_new_call,
)

logger = logging.getLogger(__name__)

load_dotenv()

GONG_MCP_SERVER_PORT = int(os.getenv("GONG_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=GONG_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level")
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("gong-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="gong_get_transcripts_by_user",
                description=(
                    "Get call transcripts associated with a user by email address "
                    "including all participants on the call and their companies."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["user_email"],
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "description": "Email address of the user.",
                        },
                        "from_date": {
                            "type": "string",
                            "description": "ISO start datetime to filter calls (optional).",
                        },
                        "to_date": {
                            "type": "string",
                            "description": "ISO end datetime to filter calls (optional).",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of calls to return (default 10).",
                            "default": 10,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_TRANSCRIPT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_get_extensive_data",
                description="Lists detailed call data for specific call IDs (Gong /v2/calls/extensive).",
                inputSchema={
                    "type": "object",
                    "required": ["call_ids"],
                    "properties": {
                        "call_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of Gong call IDs (max 100).",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor returned by previous request (optional).",
                        },
                        "include_parties": {
                            "type": "boolean",
                            "description": "Include parties section (default true).",
                            "default": True,
                        },
                        "include_transcript": {
                            "type": "boolean",
                            "description": "Include transcript in response (default false).",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_get_call_transcripts",
                description="Retrieve transcripts of specific calls (Gong /v2/calls/transcript).",
                inputSchema={
                    "type": "object",
                    "required": ["call_ids"],
                    "properties": {
                        "call_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of Gong call IDs (max 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_TRANSCRIPT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_list_calls",
                description="List calls within a date range (Gong /v2/calls).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_date": {"type": "string", "description": "ISO start datetime (optional)."},
                        "to_date": {"type": "string", "description": "ISO end datetime (optional)."},
                        "limit": {"type": "integer", "description": "Maximum calls to return (default 50).", "default": 50},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="gong_add_new_call",
                description="Add a new call record to Gong (POST /v2/calls).",
                inputSchema={
                    "type": "object",
                    "required": ["call"],
                    "properties": {
                        "call": {
                            "type": "object",
                            "description": "Object containing Gong call payload as per API docs.",
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GONG_CALL"}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "gong_get_transcripts_by_user":
            user_email = arguments.get("user_email")
            if not user_email:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'user_email' argument is required.",
                    )
                ]

            limit = arguments.get("limit", 10)
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            try:
                result = await get_transcripts_by_user(
                    user_email=user_email,
                    from_date=from_date,
                    to_date=to_date,
                    limit=limit,
                )
                return [
                    types.TextContent(type="text", text=json.dumps(result, indent=2))
                ]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_get_extensive_data":
            call_ids = arguments.get("call_ids")
            cursor = arguments.get("cursor")
            include_parties = arguments.get("include_parties", True)
            include_transcript = arguments.get("include_transcript", False)
            try:
                result = await get_extensive_data(call_ids, cursor, include_parties, include_transcript)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_get_call_transcripts":
            call_ids = arguments.get("call_ids")
            try:
                result = await get_call_transcripts(call_ids)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_list_calls":
            limit = arguments.get("limit", 50)
            from_date = arguments.get("from_date")
            to_date = arguments.get("to_date")
            try:
                result = await list_calls(from_date, to_date, limit)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        elif name == "gong_add_new_call":
            call_body = arguments.get("call")
            try:
                result = await add_new_call(call_body)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception("Error executing Gong tool %s: %s", name, e)
                return [types.TextContent(type="text", text=f"Error: {e}")]

        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        auth_token = extract_access_token(request)
        token = auth_token_context.set(auth_token)
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            auth_token_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        auth_token = extract_access_token(scope)
        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Gong MCP Server started")
            try:
                yield
            finally:
                logger.info("Gong MCP Server shutting down")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info("Server listening on port %s", port)
    logger.info("SSE endpoint: http://localhost:%s/sse", port)
    logger.info("StreamableHTTP endpoint: http://localhost:%s/mcp", port)

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    main() 