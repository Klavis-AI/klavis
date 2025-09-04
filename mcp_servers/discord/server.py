import os
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Annotated

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field

# Import modular tools and auth/registry
from tools.auth import DiscordAuth
from tools.base import DiscordToolRegistry
from tools.servers import ServerTool
from tools.messages import MessageTool
from tools.channels import ChannelTool
from tools.users import UserTool

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Discord MCP Server configuration
DISCORD_MCP_SERVER_PORT = int(os.getenv("DISCORD_MCP_SERVER_PORT", "5000"))

# Create an MCP Server instance
mcp_server = Server("discord-mcp-server")

# Initialize auth and tool registry
auth = DiscordAuth()
tool_registry = DiscordToolRegistry(auth)

# Instantiate and register tools
server_tool = ServerTool(auth)
message_tool = MessageTool(auth)
channel_tool = ChannelTool(auth)
user_tool = UserTool(auth)

tool_registry.register_tool("server", server_tool)
tool_registry.register_tool("messages", message_tool)
tool_registry.register_tool("channels", channel_tool)
tool_registry.register_tool("users", user_tool)

# MCP Tool Definitions exposed via list_tools() and call_tool() dispatcher


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available Discord MCP tools from the tool registry."""
    tools = []
    
    # Get tool definitions from the tool registry
    tool_definitions = tool_registry.get_all_tool_definitions()
    
    for tool_def in tool_definitions:
        # Convert tool definition to MCP Tool type
        mcp_tool = types.Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def.get("inputSchema")
        )
        tools.append(mcp_tool)
    
    return tools


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls using the tool registry."""
    ctx = mcp_server.request_context

    try:
        # Use the tool registry to handle the tool call
        result = await tool_registry.handle_tool_call(name, arguments)
        
        # Format the result as text content
        if isinstance(result, dict):
            import json
            result_text = json.dumps(result, indent=2, ensure_ascii=False)
        elif isinstance(result, list):
            import json
            result_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            result_text = str(result)
        
        return [types.TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.exception(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# HTTP transport setup
def create_app() -> Starlette:
    """Create the Starlette ASGI application."""
    transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )
        return Response()

    # Also expose a StreamableHTTP endpoint for /mcp
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
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

    routes = [
        # SSE routes
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
        
        # StreamableHTTP route
        Mount("/mcp", app=handle_streamable_http),
    ]

    return Starlette(routes=routes, lifespan=lifespan)

@contextlib.asynccontextmanager
async def run_server() -> AsyncIterator[None]:
    """Context manager to run the MCP server."""
    async with mcp_server:
        yield

@click.command()
@click.option("--port", default=DISCORD_MCP_SERVER_PORT, help="Server port")
@click.option("--host", default="0.0.0.0", help="Server host")
def main(port: int, host: str) -> None:
    """Run the Discord MCP Server."""
    import uvicorn
    
    app = create_app()
    
    logger.info(f"Starting Discord MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
