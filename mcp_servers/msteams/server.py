
import contextlib
import logging
import os
import json
import asyncio
import sys
import base64
from collections.abc import AsyncIterator
from typing import Any, Dict

import click
import msal
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import (
    ms_graph_token_context,
    list_all_teams,
    get_team,
    list_channels,
    create_channel,
    send_channel_message,
    list_joined_teams,
    list_chats,
    send_chat_message,
    list_users,
    get_user,
    create_online_meeting,
    list_online_meetings,
)

# Configure logging
logger = logging.getLogger(__name__)

MS_TEAMS_MCP_SERVER_PORT = int(os.getenv("MS_TEAMS_MCP_SERVER_PORT", "8791"))

def acquire_and_set_token():
    """Acquires a token using MSAL and sets it in the context variable for the current request."""
    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Missing Azure credentials. Please set MS_CLIENT_ID, MS_CLIENT_SECRET, and MS_TENANT_ID.")

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)

    result = app.acquire_token_silent(scopes=scope, account=None)
    if not result:
        logger.info("No token in cache, acquiring a new one...")
        result = app.acquire_token_for_client(scopes=scope)

    if "access_token" in result:
        ms_graph_token_context.set(result["access_token"])
        return result["access_token"]
    else:
        raise Exception(f"Authentication failed: {result.get('error_description')}")

def get_all_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="msteams_list_all_teams",
            description="Lists all Microsoft Teams in the organization.",
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(title="List All Teams", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_list_joined_teams",
            description="Lists all Microsoft Teams the current user has joined.",
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(title="List Joined Teams", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_get_team",
            description="Gets the details of a specific team by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "The ID of the team to retrieve."},
                },
                "required": ["team_id"],
            },
            annotations=types.ToolAnnotations(title="Get Team", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_list_channels",
            description="Lists the channels within a specific team.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "The ID of the team to list channels from."},
                },
                "required": ["team_id"],
            },
            annotations=types.ToolAnnotations(title="List Team Channels", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_create_channel",
            description="Creates a new channel within a specific team.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "The ID of the team where the channel will be created."},
                    "display_name": {"type": "string", "description": "The name of the new channel."},
                    "description": {"type": "string", "description": "An optional description for the new channel."},
                },
                "required": ["team_id", "display_name"],
            },
            annotations=types.ToolAnnotations(title="Create Team Channel", destructiveHint=True),
        ),
        types.Tool(
            name="msteams_send_channel_message",
            description="Sends a message to a specific channel in a Team.",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_id": {"type": "string", "description": "The ID of the team that the channel belongs to."},
                    "channel_id": {"type": "string", "description": "The ID of the channel to send the message to."},
                    "message": {"type": "string", "description": "The content of the message to be sent."},
                },
                "required": ["team_id", "channel_id", "message"],
            },
            annotations=types.ToolAnnotations(title="Send Channel Message", destructiveHint=True),
        ),
        types.Tool(
            name="msteams_list_chats",
            description="Lists all 1-on-1 and group chats the application has access to.",
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(title="List Chats", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_send_chat_message",
            description="Sends a message to a specific chat.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "The ID of the chat to send the message to."},
                    "message": {"type": "string", "description": "The content of the message to be sent."},
                },
                "required": ["chat_id", "message"],
            },
            annotations=types.ToolAnnotations(title="Send Chat Message", destructiveHint=True),
        ),
        types.Tool(
            name="msteams_list_users",
            description="Lists all users in the organization.",
            inputSchema={"type": "object", "properties": {}},
            annotations=types.ToolAnnotations(title="List Users", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_get_user",
            description="Gets a specific user by their ID or userPrincipalName.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The ID or userPrincipalName of the user."},
                },
                "required": ["user_id"],
            },
            annotations=types.ToolAnnotations(title="Get User", readOnlyHint=True),
        ),
        types.Tool(
            name="msteams_create_online_meeting",
            description="Schedules a new online Teams meeting for a given user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The ID or userPrincipalName of the user to create the meeting for."},
                    "subject": {"type": "string", "description": "The subject or title of the meeting."},
                    "start_datetime": {"type": "string", "description": "The meeting start time in ISO 8601 format."},
                    "end_datetime": {"type": "string", "description": "The meeting end time in ISO 8601 format."},
                },
                "required": ["user_id", "subject", "start_datetime", "end_datetime"],
            },
            annotations=types.ToolAnnotations(title="Create Online Meeting", destructiveHint=True),
        ),
        types.Tool(
            name="msteams_list_online_meetings",
            description="Lists all online meetings for a specific user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The ID or userPrincipalName of the user."},
                },
                "required": ["user_id"],
            },
            annotations=types.ToolAnnotations(title="List Online Meetings", readOnlyHint=True),
        ),
    ]

async def call_tool_router(name: str, arguments: dict) -> dict:
    if name == "msteams_list_all_teams":
        return await list_all_teams()
    elif name == "msteams_get_team":
        return await get_team(**arguments)
    elif name == "msteams_list_channels":
        return await list_channels(**arguments)
    elif name == "msteams_create_channel":
        return await create_channel(**arguments)
    elif name == "msteams_send_channel_message":
        return await send_channel_message(**arguments)
    elif name == "msteams_list_joined_teams":
        return await list_joined_teams()
    elif name == "msteams_list_chats":
        return await list_chats()
    elif name == "msteams_send_chat_message":
        return await send_chat_message(**arguments)
    elif name == "msteams_list_users":
        return await list_users()
    elif name == "msteams_get_user":
        return await get_user(**arguments)
    elif name == "msteams_create_online_meeting":
        return await create_online_meeting(**arguments)
    elif name == "msteams_list_online_meetings":
        return await list_online_meetings(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

@click.command()
@click.option("--port", default=MS_TEAMS_MCP_SERVER_PORT, help="Port for HTTP mode.")
@click.option("--log-level", default="INFO", help="Logging level.")
@click.option("--stdio", is_flag=True, default=False, help="Run in stdio mode for Claude Desktop.")
def main(port: int, log_level: str, stdio: bool):
    load_dotenv()
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    if stdio:
        run_stdio_mode()
    else:
        run_http_mode(port)

def run_stdio_mode():
    logger.info("msteams-mcp-server starting in stdio mode...")
    app = Server("msteams-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return get_all_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            acquire_and_set_token()
            result = await call_tool_router(name, arguments)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}", exc_info=True)
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
    
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(run_server())

def extract_access_token(request_or_scope) -> str:
    """Extracts access token from x-auth-data header or environment for local dev."""
    auth_data = os.getenv("AUTH_DATA") # For local testing convenience
    if not auth_data:
        if hasattr(request_or_scope, 'headers'):
            header_value = request_or_scope.headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            headers = dict(request_or_scope.get("headers", []))
            header_value = headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')
    
    if not auth_data:
        return ""
    
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError):
        return ""

def run_http_mode(port: int):
    logger.info(f"msteams-mcp-server starting in HTTP mode on port {port}...")
    app = Server("msteams-mcp-server")

    @app.list_tools()
    async def list_tools_http() -> list[types.Tool]:
        return get_all_tools()

    @app.call_tool()
    async def call_tool_http(name: str, arguments: dict) -> list[types.TextContent]:
        # In HTTP mode, the token is set in the context by the request handler
        try:
            result = await call_tool_router(name, arguments)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    session_manager = StreamableHTTPSessionManager(app=app, stateless=True)

    async def handle_http_request(scope: Scope, receive: Receive, send: Send) -> None:
        auth_token = ""
        if scope["type"] == "http":
            auth_token = extract_access_token(scope)
        
        # If no token from header, fall back to acquiring one for local dev
        if not auth_token:
            logger.warning("No x-auth-data header found, falling back to local credential acquisition.")
            auth_token = acquire_and_set_token()

        token = ms_graph_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            ms_graph_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    starlette_app = Starlette(
        debug=True,
        routes=[Mount("/mcp", app=handle_http_request)],
        lifespan=lifespan,
    )

    import uvicorn
    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()
