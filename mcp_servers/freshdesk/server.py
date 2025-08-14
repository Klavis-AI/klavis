import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import create_ticket, get_ticket, update_ticket, delete_ticket, list_tickets
from tools.base import auth_token_context, FreshdeskToolExecutionError


logger = logging.getLogger(__name__)

load_dotenv()

FRESHDESK_MCP_SERVER_PORT = int(os.getenv("FRESHDESK_MCP_SERVER_PORT", "5000"))


async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "freshdesk-mcp-server",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
    )


@click.command()
@click.option("--port", default=FRESHDESK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    app = Server("freshdesk-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="freshdesk_create_ticket",
                description="Create a new Freshdesk ticket",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "Ticket subject"},
                        "description": {"type": "string", "description": "Ticket description (HTML or text)"},
                        "email": {"type": "string", "description": "Requester email"},
                        "priority": {"type": "integer", "description": "Priority 1-4"},
                        "status": {"type": "integer", "description": "Status 2=Open,3=Pending,4=Resolved,5=Closed"},
                        "cc_emails": {"type": "array", "items": {"type": "string"}},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["subject", "email"],
                },
            ),
            types.Tool(
                name="freshdesk_get_ticket",
                description="Get a Freshdesk ticket by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "integer", "description": "Ticket ID"},
                    },
                    "required": ["ticket_id"],
                },
            ),
            types.Tool(
                name="freshdesk_update_ticket",
                description="Update a Freshdesk ticket",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "integer"},
                        "subject": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "integer"},
                        "status": {"type": "integer"},
                        "cc_emails": {"type": "array", "items": {"type": "string"}},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["ticket_id"],
                },
            ),
            types.Tool(
                name="freshdesk_delete_ticket",
                description="Delete a Freshdesk ticket",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ticket_id": {"type": "integer"},
                    },
                    "required": ["ticket_id"],
                },
            ),
            types.Tool(
                name="freshdesk_list_tickets",
                description="List Freshdesk tickets with optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "description": "Filter by requester email"},
                        "updated_since": {"type": "string", "description": "ISO timestamp to filter by last updated"},
                        "per_page": {"type": "integer", "description": "Results per page (default 30, max 100)"},
                        "page": {"type": "integer", "description": "Page number"},
                        "order_type": {"type": "string", "enum": ["asc", "desc"], "description": "Sort order"},
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # Auth
        try:
            if name == "freshdesk_create_ticket":
                result = await create_ticket.create_ticket(**arguments)
            elif name == "freshdesk_get_ticket":
                result = await get_ticket.get_ticket(**arguments)
            elif name == "freshdesk_update_ticket":
                result = await update_ticket.update_ticket(**arguments)
            elif name == "freshdesk_delete_ticket":
                result = await delete_ticket.delete_ticket(**arguments)
            elif name == "freshdesk_list_tickets":
                result = await list_tickets.list_tickets(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except FreshdeskToolExecutionError as e:
            error_response = {
                "error": str(e),
                "developer_message": getattr(e, "developer_message", ""),
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        except Exception as e:
            error_response = {
                "error": f"Unexpected error: {str(e)}",
                "developer_message": f"{type(e).__name__}: {str(e)}",
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        auth_token = request.headers.get("x-auth-token")
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b"x-auth-token")
        if auth_token:
            auth_token = auth_token.decode("utf-8")
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            try:
                yield
            finally:
                pass

    starlette_app = Starlette(
        debug=False,  # Disable debug mode for production
        routes=[
            Route("/health", endpoint=health_check, methods=["GET"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level=log_level.lower())
    return 0


if __name__ == "__main__":
    exit(main())
