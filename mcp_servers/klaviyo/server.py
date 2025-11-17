import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import List

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

# Import your Klaviyo tool modules
from tools import (
    profiles,
    lists,
    metrics,
    campaigns,
    templates,
    flows,
    accounts,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

KLAVIYO_MCP_SERVER_PORT = int(os.getenv("KLAVIYO_MCP_SERVER_PORT", "5001"))


# -------------------------------
# API Key Handling
# -------------------------------
def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("KLAVIYO_API_KEY")

    if not api_key:
        if hasattr(request_or_scope, 'headers'):
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None

        if auth_data:
            try:
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token', '')
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""

    return api_key or ""


# -------------------------------
# CLI entrypoint
# -------------------------------
@click.command()
@click.option("--port", default=KLAVIYO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("klaviyo-mcp-server")

    # -------------------------------
    # Tool listing
    # -------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(name="get_profile", description="Get a profile by email",  inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },),
            types.Tool(name="create_or_update_profile_single", description="Create or update a single profile", inputSchema={
                       "type": "object", "properties": {"email": {"type": "string"}, "attributes": {"type": "object"}}, "required": ["email"]}),
            types.Tool(name="get_lists", description="Get all lists",
                       inputSchema={"type": "object", "properties": {}}),
            types.Tool(name="get_list", description="Get details of a list", inputSchema={
                       "type": "object", "properties": {"list_id": {"type": "string"}}, "required": ["list_id"]}),
            types.Tool(name="create_list", description="Create a new list", inputSchema={
                       "type": "object", "properties": {"list_name": {"type": "string"}}, "required": ["list_name"]}),
            types.Tool(name="get_profiles_for_list", description="Get profiles for a list", inputSchema={
                       "type": "object", "properties": {"list_id": {"type": "string"}}, "required": ["list_id"]}),
            types.Tool(name="get_metrics", description="Get metrics",
                       inputSchema={"type": "object", "properties": {}}),
            types.Tool(name="get_custom_metrics", description="Get custom metrics", inputSchema={
                       "type": "object", "properties": {}}),
            types.Tool(name="get_campaigns", description="Retrieve campaigns", inputSchema={
                       "type": "object", "properties": {"channel": {"type": "string"}}, "required": ["channel"]}),
            types.Tool(name="create_campaign", description="Create a new campaign", inputSchema={"type": "object", "properties": {
                       "name": {"type": "string"}, "channel": {"type": "string"}}, "required": ["name", "channel"]}),
            types.Tool(name="get_campaign", description="Get a specific campaign by ID", inputSchema={
                       "type": "object", "properties": {"campaign_id": {"type": "string"}}, "required": ["campaign_id"]}),
            types.Tool(name="get_templates", description="Get templates",
                       inputSchema={"type": "object", "properties": {}}),
            types.Tool(name="render_template", description="Render a template", inputSchema={"type": "object", "properties": {
                       "template_id": {"type": "string"}, "context": {"type": "object"}}, "required": ["template_id"]}),
            types.Tool(name="get_flows", description="Get flows",
                       inputSchema={"type": "object", "properties": {}}),
            types.Tool(name="get_account_details", description="Get account details", inputSchema={
                       "type": "object", "properties": {}}),
        ]

    # -------------------------------
    # Tool dispatcher
    # -------------------------------
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
        try:
            if name == "get_profile":
                result = await profiles.get_profile(arguments["email"])
            elif name == "create_or_update_profile_single":
                result = await profiles.create_or_update_profile_single(arguments["email"], arguments.get("attributes", {}))
            elif name == "get_lists":
                result = await lists.get_lists()
            elif name == "get_list":
                result = await lists.get_list(arguments["list_id"])
            elif name == "create_list":
                result = await lists.create_list(arguments["list_name"])
            elif name == "get_profiles_for_list":
                result = await lists.get_profiles_for_list(arguments["list_id"])
            elif name == "get_metrics":
                result = await metrics.get_metrics()
            elif name == "get_custom_metrics":
                result = await metrics.get_custom_metrics()
            elif name == "get_campaigns":
                result = await campaigns.get_campaigns(arguments["channel"])
            elif name == "create_campaign":
                result = await campaigns.create_campaign(arguments["name"], arguments["channel"])
            elif name == "get_campaign":
                result = await campaigns.get_campaign(arguments["campaign_id"])
            elif name == "get_templates":
                result = await templates.get_templates()
            elif name == "render_template":
                result = await templates.render_template(arguments["template_id"], arguments.get("context", {}))
            elif name == "get_flows":
                result = await flows.get_flows()
            elif name == "get_account_details":
                result = await accounts.get_account_details()
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error in {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # -------------------------------
    # SSE + Streamable HTTP setup
    # -------------------------------
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        _ = extract_api_key(request)

        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
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
