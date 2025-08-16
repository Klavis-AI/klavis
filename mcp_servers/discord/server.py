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

# MCP Tool Definitions
@mcp_server.tool(
    name="get_server_info",
    description="Retrieve detailed information about a Discord server (guild)",
)
async def get_server_info_tool(server_id: str) -> str:
    """Get information about a Discord server (guild)."""
    try:
    result = await tool_registry.handle_tool_call("get_server_info", {"server_id": server_id})
        return f"Server Info: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="list_members",
    description="List members of a server with customizable result limits",
)
async def list_members_tool(server_id: str, limit: int = 100) -> str:
    """Get a list of members in a server (Default 100, Max 1000)."""
    try:
    result = await tool_registry.handle_tool_call("list_members", {"server_id": server_id, "limit": limit})
        return f"Members: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="create_text_channel",
    description="Create a new text channel with optional category and topic",
)
async def create_text_channel_tool(
    server_id: str,
    name: str,
    topic: Optional[str] = None,
    category_id: Optional[str] = None
) -> str:
    """Create a new text channel."""
    try:
    result = await tool_registry.handle_tool_call("create_text_channel", {"server_id": server_id, "name": name, "topic": topic, "category_id": category_id})
        return f"Channel Created: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="send_message",
    description="Send a message to a specified channel",
)
async def send_message_tool(channel_id: str, content: str) -> str:
    """Send a message to a specified channel."""
    try:
    result = await tool_registry.handle_tool_call("send_message", {"channel_id": channel_id, "content": content})
        return f"Message Sent: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="read_messages",
    description="Retrieve recent messages from a channel",
)
async def read_messages_tool(channel_id: str, limit: int = 50) -> str:
    """Read recent messages from a channel (Default 50, Max 100)."""
    try:
    result = await tool_registry.handle_tool_call("read_messages", {"channel_id": channel_id, "limit": limit})
        return f"Messages: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="add_reaction",
    description="Add a single emoji reaction to a message",
)
async def add_reaction_tool(channel_id: str, message_id: str, emoji: str) -> str:
    """Add a reaction to a message."""
    try:
    result = await tool_registry.handle_tool_call("add_reaction", {"channel_id": channel_id, "message_id": message_id, "emoji": emoji})
        return f"Reaction Added: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="add_multiple_reactions",
    description="Add multiple emoji reactions to a message",
)
async def add_multiple_reactions_tool(channel_id: str, message_id: str, emojis: List[str]) -> str:
    """Add multiple reactions to a message (makes individual API calls)."""
    try:
    result = await tool_registry.handle_tool_call("add_multiple_reactions", {"channel_id": channel_id, "message_id": message_id, "emojis": emojis})
        return f"Multiple Reactions Added: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="remove_reaction",
    description="Remove a specific reaction from a message",
)
async def remove_reaction_tool(channel_id: str, message_id: str, emoji: str) -> str:
    """Remove the bot's own reaction from a message."""
    try:
    result = await tool_registry.handle_tool_call("remove_reaction", {"channel_id": channel_id, "message_id": message_id, "emoji": emoji})
        return f"Reaction Removed: {result}"
    except Exception as e:
        return str(e)

@mcp_server.tool(
    name="get_user_info",
    description="Retrieve information about a specific Discord user",
)
async def get_user_info_tool(user_id: str) -> str:
    """Get information about a Discord user."""
    try:
    result = await tool_registry.handle_tool_call("get_user_info", {"user_id": user_id})
        return f"User Info: {result}"
    except Exception as e:
        return str(e)

# HTTP transport setup
def create_app() -> Starlette:
    """Create the Starlette ASGI application."""
    transport = SseServerTransport("/mcp")

    async def handle_sse(scope: Scope, receive: Receive, send: Send) -> None:
        await transport.handle_request(
            scope,
            receive,
            send,
            StreamableHTTPSessionManager.create_session,
            mcp_server.call_tool,
            mcp_server.call_resource,
            mcp_server.call_prompt,
        )

    routes = [
        Route("/mcp", endpoint=handle_sse),
    ]

    return Starlette(routes=routes)

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
    uvicorn.run(
        app,
        host=host,
        port=port,
        lifespan=run_server,
        log_level="info"
    )

if __name__ == "__main__":
    main()
