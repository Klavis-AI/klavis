import contextlib
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
    access_token_context, instance_url_context,
    # Accounts
    get_accounts, create_account, update_account, delete_account,
    # Contacts
    get_contacts, create_contact, update_contact, delete_contact,
    # Opportunities
    get_opportunities, create_opportunity, update_opportunity, delete_opportunity,
    # Leads
    get_leads, create_lead, update_lead, delete_lead, convert_lead,
    # Cases
    get_cases, create_case, update_case, delete_case,
    # Campaigns
    get_campaigns, create_campaign, update_campaign, delete_campaign,
    # Metadata & Queries
    describe_object, execute_soql_query
)

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()
FRESHDESK_MCP_SERVER_PORT = int(os.getenv("FRESHDESK_MCP_SERVER_PORT", "5000"))
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")

@click.command()
@click.option("--port", default=FRESHDESK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("freshdesk-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth credentials from headers
        headers = dict(scope.get("headers", []))
        access_token = headers.get(b'x-auth-token')
        instance_url = headers.get(b'x-instance-url')
        
        if access_token:
            access_token = access_token.decode('utf-8')
        if instance_url:
            instance_url = instance_url.decode('utf-8')
        
        # Set the access token and instance URL in context for this request
        access_token_token = access_token_context.set(access_token or "")
        instance_url_token = instance_url_context.set(instance_url or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            access_token_context.reset(access_token_token)
            instance_url_context.reset(instance_url_token)

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