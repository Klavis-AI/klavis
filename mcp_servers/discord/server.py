import os
import logging
from typing import Any, Dict, List, Optional, Annotated
import urllib.parse  # Added for URL encoding emojis
from dotenv import load_dotenv
import aiohttp  # Added for HTTP requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_MCP_SERVER_PORT = int(os.getenv("DISCORD_MCP_SERVER_PORT", "5000"))

mcp = FastMCP("discord-server", port=DISCORD_MCP_SERVER_PORT)

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


@mcp.tool()
async def discord_get_server_info(
    server_id: Annotated[
        str,
        Field(
            description="The ID of the Discord server (guild) to retrieve information for."
        ),
    ]
) -> Dict[str, Any]:
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

@mcp.tool()
async def discord_list_members(
    server_id: Annotated[
        str,
        Field(
            description="The ID of the Discord server (guild)."
        ),
    ],
    limit: Annotated[
        int,
        Field(
            description="The maximum number of members to return (1-1000).",
            default=100
        ),
    ] = 100
) -> List[Dict[str, Any]]:
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

@mcp.tool()
async def discord_create_text_channel(
    server_id: Annotated[
        str,
        Field(
            description="The ID of the Discord server (guild) where the channel will be created."
        ),
    ],
    name: Annotated[
        str,
        Field(
            description="The name for the new text channel."
        ),
    ],
    category_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the category (parent channel) to place the new channel under."
        ),
    ] = None,
    topic: Annotated[
        Optional[str],
        Field(
            description="The topic for the new channel."
        ),
    ] = None
) -> Dict[str, Any]:
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

@mcp.tool()
async def discord_add_reaction(
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the channel containing the message."
        ),
    ],
    message_id: Annotated[
        str,
        Field(
            description="The ID of the message to add the reaction to."
        ),
    ],
    emoji: Annotated[
        str,
        Field(
            description="The emoji to add as a reaction. Can be a standard Unicode emoji or a custom emoji in the format `name:id`."
        ),
    ]
) -> str:
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

@mcp.tool()
async def discord_add_multiple_reactions(
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the channel containing the message."
        ),
    ],
    message_id: Annotated[
        str,
        Field(
            description="The ID of the message to add reactions to."
        ),
    ],
    emojis: Annotated[
        List[str],
        Field(
            description="A list of emojis to add. Each can be Unicode or custom format `name:id`."
        ),
    ]
) -> str:
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


@mcp.tool()
async def discord_remove_reaction(
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the channel containing the message."
        ),
    ],
    message_id: Annotated[
        str,
        Field(
            description="The ID of the message to remove the reaction from."
        ),
    ],
    emoji: Annotated[
        str,
        Field(
            description="The emoji reaction to remove. Can be Unicode or custom format `name:id`."
        ),
    ]
) -> str:
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

@mcp.tool()
async def discord_send_message(
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the channel to send the message to."
        ),
    ],
    content: Annotated[
        str,
        Field(
            description="The text content of the message."
        ),
    ]
) -> Dict[str, Any]:
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

@mcp.tool()
async def discord_read_messages(
    channel_id: Annotated[
        str,
        Field(
            description="The ID of the channel to read messages from."
        ),
    ],
    limit: Annotated[
        int,
        Field(
            description="The maximum number of messages to retrieve (1-100).",
            default=50
        ),
    ] = 50
) -> List[Dict[str, Any]]:
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

@mcp.tool()
async def discord_get_user_info(
    user_id: Annotated[
        str,
        Field(
            description="The ID of the Discord user to retrieve information for."
        ),
    ]
) -> Dict[str, Any]:
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


if __name__ == "__main__":
    mcp.run(transport="sse")
