import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
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

# Import bot tools
from bot_tools import (
    bot_token_context
)
from bot_tools.bot_messages import (
    bot_post_message, 
    bot_reply_to_thread, 
    bot_add_reaction
)

# Import user tools
from user_tools import (
    user_token_context,
    list_channels as user_list_channels,
    get_channel_history as user_get_channel_history
)
from user_tools.user_messages import (
    user_post_message,
    user_reply_to_thread,
    user_add_reaction
)
from user_tools.search import user_search_messages
from user_tools.users import list_users, user_get_info

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

SLACK_MCP_SERVER_PORT = int(os.getenv("SLACK_MCP_SERVER_PORT", "5000"))

def extract_access_tokens(request_or_scope) -> tuple[str, str]:
    """Extract both bot and user access tokens from x-auth-data header.
    Returns (bot_token, user_token)
    """
    auth_data = None
    
    ## ---- for Klavis Cloud ---- ##
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
    if hasattr(request_or_scope, 'headers'):
        # SSE request object
        auth_data = request_or_scope.headers.get(b'x-auth-data')
        if auth_data:
            auth_data = base64.b64decode(auth_data).decode('utf-8')
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        auth_data = headers.get(b'x-auth-data')
        if auth_data:
            auth_data = base64.b64decode(auth_data).decode('utf-8')
    
    ## ---- for local development ---- ##
    if not auth_data:
        # Fall back to environment variables
        bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        user_token = os.getenv("SLACK_USER_TOKEN", "")
        return bot_token, user_token
    
    try:
        # Parse the JSON auth data to extract both tokens
        auth_json = json.loads(auth_data)
        bot_token = auth_json.get('access_token', '')  # Bot token at root level
        user_token = auth_json.get('authed_user', {}).get('access_token', '')  # User token in authed_user
        return bot_token, user_token
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return "", ""

@click.command()
@click.option("--port", default=SLACK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("slack-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # ============= USER TOOLS (using user token) =============

            # User Channels
            types.Tool(
                name="slack_user_list_channels",
                description="List all channels the authenticated user has access to. This includes public channels, private channels the user is a member of, direct messages, and multi-party direct messages.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of channels to return (default 100, max 200)",
                            "default": 100,
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for next page of results",
                        },
                        "types": {
                            "type": "string",
                            "description": "Mix and match channel types by providing a comma-separated list of any combination of public_channel, private_channel, mpim, im",
                            "default": "public_channel",
                        },
                    },
                },
            ),
            types.Tool(
                name="slack_get_channel_history",
                description="Get recent messages from a channel",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel",
                        },
                        "limit": {
                            "type": "number",
                            "description": "Number of messages to retrieve (default 10)",
                            "default": 10,
                        },
                    },
                    "required": ["channel_id"],
                },
            ),
            
            # User Info
            types.Tool(
                name="slack_list_users",
                description="Lists all users in a Slack team using user token",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for getting more results",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of users to return (default 100, max 200)",
                        },
                        "team_id": {
                            "type": "string",
                            "description": "Team ID to list users from (for Enterprise Grid)",
                        },
                        "include_locale": {
                            "type": "boolean",
                            "description": "Whether to include locale information for each user",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="slack_user_get_info",
                description="Gets information about a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user to get information for (e.g., 'U1234567890')",
                        },
                        "include_locale": {
                            "type": "boolean",
                            "description": "Whether to include locale information for the user",
                        },
                    },
                    "required": ["user_id"],
                },
            ),
            
            # User Search
            types.Tool(
                name="slack_user_search_messages",
                description="Searches for messages matching a query.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query string. You can use Slack's search operators like 'in:#channel', 'from:@user', 'before:YYYY-MM-DD', 'after:YYYY-MM-DD', etc.",
                        },
                        "channel_ids": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                            "description": "Optional list of channel IDs to search within. If not provided, searches across all accessible channels.",
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["score", "timestamp"],
                            "description": "Sort results by relevance (score) or date (timestamp). Default is score.",
                            "default": "score",
                        },
                        "sort_dir": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "Sort direction. Default is desc (newest/most relevant first).",
                            "default": "desc",
                        },
                        "count": {
                            "type": "number",
                            "description": "Number of results to return per page (default 20, max 100)",
                            "default": 20,
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for next page of results",
                        },
                        "highlight": {
                            "type": "boolean",
                            "description": "Whether to include highlighting of matched terms",
                            "default": True,
                        },
                    },
                    "required": ["query"],
                },
            ),
            
            # User Messages
            types.Tool(
                name="slack_user_post_message",
                description="Post a new message to a Slack channel as a user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the Slack channel (e.g., 'C1234567890')",
                        },
                        "text": {
                            "type": "string",
                            "description": "The message text to post",
                        },
                    },
                    "required": ["channel_id", "text"],
                },
            ),
            types.Tool(
                name="slack_user_reply_to_thread",
                description="Reply to a specific message thread in Slack as a user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the Slack channel (e.g., 'C1234567890')",
                        },
                        "thread_ts": {
                            "type": "string",
                            "description": "The timestamp of the parent message to reply to",
                        },
                        "text": {
                            "type": "string",
                            "description": "The message text to post as a reply",
                        },
                    },
                    "required": ["channel_id", "thread_ts", "text"],
                },
            ),
            types.Tool(
                name="slack_user_add_reaction",
                description="Add a reaction emoji to a message as a user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the Slack channel (e.g., 'C1234567890')",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "The timestamp of the message to react to",
                        },
                        "reaction": {
                            "type": "string",
                            "description": "The name of the emoji reaction (without colons, e.g., 'thumbsup', 'heart')",
                        },
                    },
                    "required": ["channel_id", "timestamp", "reaction"],
                },
            ),
            
            # ============= BOT TOOLS (using bot token) =============
            
            # Bot Messages
            types.Tool(
                name="slack_bot_post_message",
                description="Post a new message to a Slack channel as a bot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel to post to",
                        },
                        "text": {
                            "type": "string",
                            "description": "The message text to post",
                        },
                    },
                    "required": ["channel_id", "text"],
                },
            ),
            types.Tool(
                name="slack_bot_reply_to_thread",
                description="Reply to a specific message thread in Slack as a bot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the thread",
                        },
                        "thread_ts": {
                            "type": "string",
                            "description": "The timestamp of the parent message in the format '1234567890.123456'. Timestamps in the format without the period can be converted by adding the period such that 6 numbers come after it.",
                        },
                        "text": {
                            "type": "string",
                            "description": "The reply text",
                        },
                    },
                    "required": ["channel_id", "thread_ts", "text"],
                },
            ),
            types.Tool(
                name="slack_bot_add_reaction",
                description="Add a reaction emoji to a message as a bot.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "The timestamp of the message to react to",
                        },
                        "reaction": {
                            "type": "string",
                            "description": "The name of the emoji reaction (without ::)",
                        },
                    },
                    "required": ["channel_id", "timestamp", "reaction"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # ============= USER TOOLS (using user token) =============
        
        # User Channels
        if name == "slack_user_list_channels":
            limit = arguments.get("limit")
            cursor = arguments.get("cursor")
            types_param = arguments.get("types")
            
            try:
                result = await user_list_channels(limit, cursor, types_param)
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
        
        elif name == "slack_get_channel_history":
            channel_id = arguments.get("channel_id")
            if not channel_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id parameter is required",
                    )
                ]
            
            limit = arguments.get("limit")
            
            try:
                result = await user_get_channel_history(channel_id, limit)
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
        
        # User Info
        elif name == "slack_list_users":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            team_id = arguments.get("team_id")
            include_locale = arguments.get("include_locale")
            
            try:
                result = await list_users(cursor, limit, team_id, include_locale)
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
        
        elif name == "slack_user_get_info":
            user_id = arguments.get("user_id")
            if not user_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: user_id parameter is required",
                    )
                ]
            
            include_locale = arguments.get("include_locale")
            
            try:
                result = await user_get_info(user_id, include_locale)
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
        
        # User Search
        elif name == "slack_user_search_messages":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            channel_ids = arguments.get("channel_ids")
            sort = arguments.get("sort")
            sort_dir = arguments.get("sort_dir")
            count = arguments.get("count")
            cursor = arguments.get("cursor")
            highlight = arguments.get("highlight")
            
            try:
                result = await user_search_messages(query, channel_ids, sort, sort_dir, count, cursor, highlight)
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
        
        # User Messages
        elif name == "slack_user_post_message":
            channel_id = arguments.get("channel_id")
            text = arguments.get("text")
            if not channel_id or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id and text parameters are required",
                    )
                ]
            
            try:
                result = await user_post_message(channel_id, text)
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
        
        elif name == "slack_user_reply_to_thread":
            channel_id = arguments.get("channel_id")
            thread_ts = arguments.get("thread_ts")
            text = arguments.get("text")
            if not channel_id or not thread_ts or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id, thread_ts, and text parameters are required",
                    )
                ]
            
            try:
                result = await user_reply_to_thread(channel_id, thread_ts, text)
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
        
        elif name == "slack_user_add_reaction":
            channel_id = arguments.get("channel_id")
            timestamp = arguments.get("timestamp")
            reaction = arguments.get("reaction")
            if not channel_id or not timestamp or not reaction:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id, timestamp, and reaction parameters are required",
                    )
                ]
            
            try:
                result = await user_add_reaction(channel_id, timestamp, reaction)
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
        
        # ============= BOT TOOLS (using bot token) =============
        
        # Bot Messages
        elif name == "slack_bot_post_message":
            channel_id = arguments.get("channel_id")
            text = arguments.get("text")
            if not channel_id or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id and text parameters are required",
                    )
                ]
            
            try:
                result = await bot_post_message(channel_id, text)
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
        
        elif name == "slack_bot_reply_to_thread":
            channel_id = arguments.get("channel_id")
            thread_ts = arguments.get("thread_ts")
            text = arguments.get("text")
            if not channel_id or not thread_ts or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id, thread_ts, and text parameters are required",
                    )
                ]
            
            try:
                result = await bot_reply_to_thread(channel_id, thread_ts, text)
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
        
        elif name == "slack_bot_add_reaction":
            channel_id = arguments.get("channel_id")
            timestamp = arguments.get("timestamp")
            reaction = arguments.get("reaction")
            if not channel_id or not timestamp or not reaction:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id, timestamp, and reaction parameters are required",
                    )
                ]
            
            try:
                result = await bot_add_reaction(channel_id, timestamp, reaction)
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
        
        # Extract both bot and user tokens from headers
        bot_token, user_token = extract_access_tokens(request)
        
        # Set both tokens in context for this request
        bot_token_ctx = bot_token_context.set(bot_token)
        user_token_ctx = user_token_context.set(user_token)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            bot_token_context.reset(bot_token_ctx)
            user_token_context.reset(user_token_ctx)
        
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
        
        # Extract both bot and user tokens from headers
        bot_token, user_token = extract_access_tokens(scope)
        
        # Set both tokens in context for this request
        bot_token_ctx = bot_token_context.set(bot_token)
        user_token_ctx = user_token_context.set(user_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            bot_token_context.reset(bot_token_ctx)
            user_token_context.reset(user_token_ctx)

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
