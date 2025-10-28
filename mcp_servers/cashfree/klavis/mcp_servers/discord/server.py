import os
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Annotated

import click
import aiohttp
import urllib.parse
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

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

# Discord API constants and configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_MCP_SERVER_PORT = int(os.getenv("DISCORD_MCP_SERVER_PORT", "5000"))

# Helper function to create standard headers for Discord API calls
def _get_discord_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

# Helper to make API requests and handle errors
async def _make_discord_request(method: str, endpoint: str, json_data: Optional[Dict] = None, expect_empty_response: bool = False) -> Any:
    """
    Makes an HTTP request to the Discord API.
    """
    url = f"{DISCORD_API_BASE}{endpoint}"
    headers = _get_discord_headers()
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
                response.raise_for_status()  # Raise exception for non-2xx status codes
                if expect_empty_response:
                    # For requests like DELETE or PUT roles/reactions where success is 204 No Content
                    if response.status == 204: 
                        return None
                    else:
                         # If we expected empty but got something else (and it wasn't an error raised above)
                         logger.warning(f"Expected empty response for {method} {endpoint}, but got status {response.status}")
                         # Try to parse JSON anyway, might be useful error info
                         try:
                             return await response.json()
                         except aiohttp.ContentTypeError:
                             return await response.text() # Return text if not json
                else:
                    # Check if response is JSON before parsing
                    if 'application/json' in response.headers.get('Content-Type', ''):
                         return await response.json()
                    else:
                         # Handle non-JSON responses if necessary, e.g., log or return text
                         text_content = await response.text()
                         logger.warning(f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}...")
                         return {"raw_content": text_content}
        except aiohttp.ClientResponseError as e:
            logger.error(f"Discord API request failed: {e.status} {e.message} for {method} {url}")
            error_details = e.message
            try:
                # Discord often returns JSON errors
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                 # If response body isn't JSON or can't be read
                 pass
            raise RuntimeError(f"Discord API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Discord API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {method} {url}") from e

async def get_server_info(server_id: str) -> Dict[str, Any]:
    """Get information about a Discord server (guild)."""
    logger.info(f"Executing tool: get_server_info with server_id: {server_id}")
    try:
        # API: GET /guilds/{guild.id}
        endpoint = f"/guilds/{server_id}?with_counts=true"
        guild_data = await _make_discord_request("GET", endpoint)
        info = {
            "name": guild_data.get("name"),
            "id": guild_data.get("id"),
            "owner_id": guild_data.get("owner_id"),
            "member_count": guild_data.get("approximate_member_count", "N/A"),
            "presence_count": guild_data.get("approximate_presence_count", "N/A"),
            "icon_hash": guild_data.get("icon"),
            "description": guild_data.get("description"),
            "premium_tier": guild_data.get("premium_tier"),
            "explicit_content_filter": guild_data.get("explicit_content_filter")
        }
        return info
    except Exception as e:
        logger.exception(f"Error executing tool get_server_info: {e}")
        raise e

async def list_members(server_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get a list of members in a server (Default 100, Max 1000)."""
    logger.info(f"Executing tool: list_members with server_id: {server_id}, limit: {limit}")
    try:
        clamped_limit = max(1, min(limit, 1000))
        # API: GET /guilds/{guild.id}/members
        endpoint = f"/guilds/{server_id}/members?limit={clamped_limit}"
        members_data = await _make_discord_request("GET", endpoint)

        if not isinstance(members_data, list):
             logger.error(f"Unexpected response type for list_members: {type(members_data)}")
             return [{"error": "Received unexpected data format for members."}]

        members_list = []
        for member in members_data:
            user = member.get('user', {})
            members_list.append({
                "id": user.get("id"),
                "username": user.get('username', 'UnknownUser'),
                "discriminator": user.get('discriminator', '0000'),
                "global_name": user.get("global_name"),
                "nick": member.get("nick"),
                "joined_at": member.get("joined_at"),
                "roles": member.get("roles", [])
            })
        return members_list
    except Exception as e:
        logger.exception(f"Error executing tool list_members: {e}")
        raise e

async def create_text_channel(server_id: str, name: str, category_id: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    """Create a new text channel."""
    logger.info(f"Executing tool: create_text_channel '{name}' in server {server_id}")
    try:
        # API: POST /guilds/{guild.id}/channels
        endpoint = f"/guilds/{server_id}/channels"
        payload = {
            "name": name,
            "type": 0, # 0 indicates a text channel
            "topic": topic,
            "parent_id": category_id # API uses parent_id
        }
        # Filter out None values from payload
        payload = {k: v for k, v in payload.items() if v is not None}
        channel_data = await _make_discord_request("POST", endpoint, json_data=payload)
        return {
             "id": channel_data.get("id"),
             "name": channel_data.get("name"),
             "topic": channel_data.get("topic"),
             "parent_id": channel_data.get("parent_id")
        }
    except Exception as e:
        logger.exception(f"Error executing tool create_text_channel: {e}")
        raise e

async def add_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Add a reaction to a message."""
    logger.info(f"Executing tool: add_reaction '{emoji}' to message {message_id} in channel {channel_id}")
    try:
        # URL Encode the emoji: Handles unicode and custom format name:id
        encoded_emoji = urllib.parse.quote(emoji)
        # API: PUT /channels/{channel.id}/messages/{message.id}/reactions/{emoji}/@me
        endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
        await _make_discord_request("PUT", endpoint, expect_empty_response=True) # Expects 204 No Content
        return f"Added reaction {emoji} to message {message_id}"
    except Exception as e:
        logger.exception(f"Error executing tool add_reaction: {e}")
        return f"Error adding reaction {emoji} to message {message_id}: {str(e)}"

async def add_multiple_reactions(channel_id: str, message_id: str, emojis: List[str]) -> str:
     """Add multiple reactions to a message (makes individual API calls)."""
     logger.info(f"Executing tool: add_multiple_reactions {emojis} to message {message_id} in channel {channel_id}")
     added_emojis = []
     errors = []
     # Make individual requests for each emoji
     for emoji in emojis:
         try:
             encoded_emoji = urllib.parse.quote(emoji)
             endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
             await _make_discord_request("PUT", endpoint, expect_empty_response=True)
             added_emojis.append(emoji)
             # Optional: Add slight delay if rate limits become an issue
             # await asyncio.sleep(0.3)
         except Exception as e:
             logger.error(f"Failed to add reaction {emoji}: {e}")
             errors.append(f"{emoji}: {str(e)}")

     result_text = f"Finished adding multiple reactions to message {message_id}. "
     if added_emojis:
         result_text += f"Successfully added: {', '.join(added_emojis)}. "
     if errors:
         result_text += f"Errors encountered: {'; '.join(errors)}."

     return result_text.strip()

async def remove_reaction(channel_id: str, message_id: str, emoji: str) -> str:
    """Remove the bot's own reaction from a message."""
    logger.info(f"Executing tool: remove_reaction '{emoji}' from message {message_id} in channel {channel_id}")
    try:
        # URL Encode the emoji
        encoded_emoji = urllib.parse.quote(emoji)
        # API: DELETE /channels/{channel.id}/messages/{message.id}/reactions/{emoji}/@me
        # This removes the bot's *own* reaction. Modify endpoint to remove others if needed (requires permissions).
        endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
        await _make_discord_request("DELETE", endpoint, expect_empty_response=True) # Expects 204 No Content
        return f"Removed bot's reaction {emoji} from message {message_id}"
    except Exception as e:
        logger.exception(f"Error executing tool remove_reaction: {e}")
        return f"Error removing reaction {emoji} from message {message_id}: {str(e)}"

async def send_message(channel_id: str, content: str) -> Dict[str, Any]:
    """Send a message to a specific channel."""
    logger.info(f"Executing tool: send_message to channel {channel_id}")
    try:
        # API: POST /channels/{channel.id}/messages
        endpoint = f"/channels/{channel_id}/messages"
        payload = {"content": content}
        message_data = await _make_discord_request("POST", endpoint, json_data=payload)
        return {
            "message_id": message_data.get("id"),
            "channel_id": message_data.get("channel_id"),
            "content_preview": content[:100] + ("..." if len(content) > 100 else "")
        }
    except Exception as e:
        logger.exception(f"Error executing tool send_message: {e}")
        raise e

async def read_messages(channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Read recent messages from a channel (Default 50, Max 100)."""
    logger.info(f"Executing tool: read_messages from channel {channel_id}, limit: {limit}")
    try:
        clamped_limit = max(1, min(limit, 100))
        # API: GET /channels/{channel.id}/messages
        endpoint = f"/channels/{channel_id}/messages?limit={clamped_limit}"
        messages_data = await _make_discord_request("GET", endpoint)

        if not isinstance(messages_data, list):
             logger.error(f"Unexpected response type for read_messages: {type(messages_data)}")
             return [{"error": "Received unexpected data format for messages."}]

        messages_list = []
        for msg in messages_data:
            author = msg.get('author', {})
            reactions_list = []
            if 'reactions' in msg and msg['reactions']:
                 for r in msg['reactions']:
                     emoji = r.get('emoji', {})
                     reactions_list.append({
                         "name": emoji.get('name', '<?>'),
                         "id": emoji.get('id'),
                         "count": r.get('count', 0)
                     })

            messages_list.append({
                "id": msg.get("id"),
                "content": msg.get('content', ''),
                "timestamp": msg.get('timestamp', 'No Timestamp'),
                "author": {
                    "id": author.get("id"),
                    "username": author.get('username', 'UnknownUser'),
                    "discriminator": author.get('discriminator', '0000'),
                    "global_name": author.get('global_name'),
                     "is_bot": author.get('bot', False)
                },
                "reactions": reactions_list
            })
        return messages_list
    except Exception as e:
        logger.exception(f"Error executing tool read_messages: {e}")
        raise e

async def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get information about a Discord user."""
    logger.info(f"Executing tool: get_user_info for user {user_id}")
    try:
        # API: GET /users/{user.id}
        endpoint = f"/users/{user_id}"
        user_data = await _make_discord_request("GET", endpoint)
        user_info = {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "discriminator": user_data.get("discriminator"),
            "global_name": user_data.get("global_name"),
            "is_bot": user_data.get("bot", False),
            "avatar_hash": user_data.get("avatar"),
        }
        return user_info
    except Exception as e:
         logger.exception(f"Error executing tool get_user_info: {e}")
         raise e


@click.command()
@click.option("--port", default=DISCORD_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("discord-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="discord_get_server_info",
                description="Get information about a Discord server (guild).",
                inputSchema={
                    "type": "object",
                    "required": ["server_id"],
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild) to retrieve information for."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_SERVER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="discord_list_members",
                description="Get a list of members in a server (Default 100, Max 1000).",
                inputSchema={
                    "type": "object",
                    "required": ["server_id"],
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild)."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of members to return (1-1000).",
                            "default": 100
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_SERVER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="discord_create_text_channel",
                description="Create a new text channel.",
                inputSchema={
                    "type": "object",
                    "required": ["server_id", "name"],
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild) where the channel will be created."
                        },
                        "name": {
                            "type": "string",
                            "description": "The name for the new text channel."
                        },
                        "category_id": {
                            "type": "string",
                            "description": "The ID of the category (parent channel) to place the new channel under."
                        },
                        "topic": {
                            "type": "string",
                            "description": "The topic for the new channel."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_SERVER"}
                ),
            ),
            types.Tool(
                name="discord_add_reaction",
                description="Add a reaction to a message.",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id", "message_id", "emoji"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message."
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to add the reaction to."
                        },
                        "emoji": {
                            "type": "string",
                            "description": "The emoji to add as a reaction. Can be a standard Unicode emoji or a custom emoji in the format `name:id`."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_MESSAGE"}
                ),
            ),
            types.Tool(
                name="discord_add_multiple_reactions",
                description="Add multiple reactions to a message (makes individual API calls).",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id", "message_id", "emojis"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message."
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to add reactions to."
                        },
                        "emojis": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "A list of emojis to add. Each can be Unicode or custom format `name:id`."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_REACTION"}
                ),
            ),
            types.Tool(
                name="discord_remove_reaction",
                description="Remove the bot's own reaction from a message.",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id", "message_id", "emoji"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message."
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to remove the reaction from."
                        },
                        "emoji": {
                            "type": "string",
                            "description": "The emoji reaction to remove. Can be Unicode or custom format `name:id`."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_REACTION"}
                ),
            ),
            types.Tool(
                name="discord_send_message",
                description="Send a message to a specific channel.",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id", "content"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel to send the message to."
                        },
                        "content": {
                            "type": "string",
                            "description": "The text content of the message."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_MESSAGE"}
                ),
            ),
            types.Tool(
                name="discord_read_messages",
                description="Read recent messages from a channel (Default 50, Max 100).",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel to read messages from."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of messages to retrieve (1-100).",
                            "default": 50
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_MESSAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="discord_get_user_info",
                description="Get information about a Discord user.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the Discord user to retrieve information for."
                        }
                    }
                },
                annotations=types.ToolAnnotations(
                    **{"category": "DISCORD_USER", "readOnlyHint": True}
                ),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "discord_get_server_info":
            server_id = arguments.get("server_id")
            result = await get_server_info(server_id)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_list_members":
            server_id = arguments.get("server_id")
            limit = arguments.get("limit", 100)
            result = await list_members(server_id, limit)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_create_text_channel":
            server_id = arguments.get("server_id")
            name = arguments.get("name")
            category_id = arguments.get("category_id")
            topic = arguments.get("topic")
            result = await create_text_channel(server_id, name, category_id, topic)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_add_reaction":
            channel_id = arguments.get("channel_id")
            message_id = arguments.get("message_id")
            emoji = arguments.get("emoji")
            result = await add_reaction(channel_id, message_id, emoji)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_add_multiple_reactions":
            channel_id = arguments.get("channel_id")
            message_id = arguments.get("message_id")
            emojis = arguments.get("emojis")
            result = await add_multiple_reactions(channel_id, message_id, emojis)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_remove_reaction":
            channel_id = arguments.get("channel_id")
            message_id = arguments.get("message_id")
            emoji = arguments.get("emoji")
            result = await remove_reaction(channel_id, message_id, emoji)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_send_message":
            channel_id = arguments.get("channel_id")
            content = arguments.get("content")
            result = await send_message(channel_id, content)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_read_messages":
            channel_id = arguments.get("channel_id")
            limit = arguments.get("limit", 50)
            result = await read_messages(channel_id, limit)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
        elif name == "discord_get_user_info":
            user_id = arguments.get("user_id")
            result = await get_user_info(user_id)
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]
        
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
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )
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

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main() 
