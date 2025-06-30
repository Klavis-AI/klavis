import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator

import click
import mcp.types as types
import uvicorn
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from tools import (
    create_table,
    get_bases_info,
    get_tables_info,
    list_records,
    update_table,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

AIRTABLE_MCP_SERVER_PORT = int(os.getenv("AIRTABLE_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option(
    "--port", default=AIRTABLE_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("airtable-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="airtable_list_bases_info",
                description="Get information about all bases",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            types.Tool(
                name="airtable_list_tables_info",
                description="Get information about all tables in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string"},
                    },
                    "required": ["base_id"],
                },
            ),
            types.Tool(
                name="airtable_create_table",
                description="Create a new table in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "fields": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": ["base_id", "name", "fields"],
                },
            ),
            types.Tool(
                name="airtable_update_table",
                description="Update an existing table in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string"},
                        "table_id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["base_id", "table_id"],
                },
            ),
            types.Tool(
                name="airtable_list_records",
                description="Get all records from a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {"type": "string"},
                        "table_id": {"type": "string"},
                    },
                    "required": ["base_id", "table_id"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "airtable_list_bases_info":
            result = await get_bases_info()
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "airtable_list_tables_info":
            result = await get_tables_info(arguments["base_id"])
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "airtable_create_table":
            result = await create_table(
                arguments["base_id"],
                arguments["name"],
                arguments["description"],
                arguments["fields"],
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "airtable_update_table":
            result = await update_table(
                arguments["base_id"],
                arguments["table_id"],
                arguments["name"],
                arguments["description"],
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "airtable_list_records":
            result = await list_records(arguments["base_id"], arguments["table_id"])
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

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

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    main()
