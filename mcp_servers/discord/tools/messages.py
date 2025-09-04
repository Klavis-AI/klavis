"""
Discord Message Management Tools

Handles Discord message operations including sending, reading, and reactions.
"""

import re
import urllib.parse
from typing import Any, Dict, List, Union

from .base import DiscordBaseTool


def normalize_emoji(emoji: str) -> str:
    """
    Normalize emoji for Discord API usage.
    
    Args:
        emoji: Unicode emoji or custom emoji in various formats
        
    Returns:
        Properly formatted emoji string for API calls
    """
    # If it's a custom emoji with angle brackets, remove them
    if emoji.startswith('<') and emoji.endswith('>'):
        # Extract the name:id part from <:name:id> or <a:name:id>
        match = re.match(r'<a?:([^:]+):(\d+)>', emoji)
        if match:
            name, emoji_id = match.groups()
            return f"{name}:{emoji_id}"
    
    # Return as-is for Unicode emoji or already normalized custom emoji
    return emoji


class MessageTool(DiscordBaseTool):
    """Tool for Discord message operations."""
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get message management tool definitions."""
        return [
            {
                "name": "send_message",
                "description": "Send a message to a specified channel",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel to send the message to"
                        },
                        "content": {
                            "type": "string",
                            "description": "The text content of the message"
                        }
                    },
                    "required": ["channel_id", "content"]
                }
            },
            {
                "name": "read_messages",
                "description": "Retrieve recent messages from a channel",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel to read messages from"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of messages to retrieve (1-100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 50
                        }
                    },
                    "required": ["channel_id"]
                }
            },
            {
                "name": "add_reaction",
                "description": "Add a single emoji reaction to a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message"
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to add the reaction to"
                        },
                        "emoji": {
                            "type": "string",
                            "description": "The emoji to add as a reaction. Can be a standard Unicode emoji or a custom emoji in the format `name:id`"
                        }
                    },
                    "required": ["channel_id", "message_id", "emoji"]
                }
            },
            {
                "name": "add_multiple_reactions",
                "description": "Add multiple reactions to a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message"
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to add reactions to"
                        },
                        "emojis": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of emojis to add. Each can be Unicode or custom format `name:id`"
                        }
                    },
                    "required": ["channel_id", "message_id", "emojis"]
                }
            },
            {
                "name": "remove_reaction",
                "description": "Remove the bot's own reaction from a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The ID of the channel containing the message"
                        },
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to remove the reaction from"
                        },
                        "emoji": {
                            "type": "string",
                            "description": "The emoji reaction to remove. Can be Unicode or custom format `name:id`"
                        }
                    },
                    "required": ["channel_id", "message_id", "emoji"]
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle message management tool calls."""
        if tool_name == "send_message":
            return await self.send_message(
                arguments["channel_id"], 
                arguments["content"]
            )
        elif tool_name == "read_messages":
            return await self.read_messages(
                arguments["channel_id"],
                arguments.get("limit", 50)
            )
        elif tool_name == "add_reaction":
            return await self.add_reaction(
                arguments["channel_id"],
                arguments["message_id"], 
                arguments["emoji"]
            )
        elif tool_name == "add_multiple_reactions":
            return await self.add_multiple_reactions(
                arguments["channel_id"],
                arguments["message_id"],
                arguments["emojis"]
            )
        elif tool_name == "remove_reaction":
            return await self.remove_reaction(
                arguments["channel_id"],
                arguments["message_id"],
                arguments["emoji"]
            )
        else:
            raise NotImplementedError(f"Tool {tool_name} not implemented")
    
    async def send_message(self, channel_id: str, content: str) -> Dict[str, Any]:
        """Send a message to a Discord channel."""
        content_preview = content[:50] + ("..." if len(content) > 50 else "")
        self.log_tool_execution("send_message", channel_id=channel_id, content=content_preview)
        
        try:
            endpoint = f"/channels/{channel_id}/messages"
            message_data = {"content": content}
            
            response = await self.auth.make_request("POST", endpoint, message_data)
            
            return {
                "message_id": response.get("id"),
                "channel_id": channel_id,
                "content_preview": content_preview
            }
        except Exception as e:
            self.log_tool_error("send_message", e)
            raise
    
    async def read_messages(self, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Read recent messages from a Discord channel."""
        self.log_tool_execution("read_messages", channel_id=channel_id, limit=limit)
        
        try:
            clamped_limit = max(1, min(limit, 100))
            endpoint = f"/channels/{channel_id}/messages?limit={clamped_limit}"
            
            messages_data = await self.auth.make_request("GET", endpoint)
            
            messages = []
            for msg in messages_data:
                author = msg.get("author", {})
                message_info = {
                    "id": msg.get("id"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp"),
                    "author": {
                        "id": author.get("id"),
                        "username": author.get("username"),
                        "discriminator": author.get("discriminator"),
                        "global_name": author.get("global_name"),
                        "is_bot": author.get("bot", False)
                    },
                    "reactions": msg.get("reactions", [])
                }
                messages.append(message_info)
            
            return messages
        except Exception as e:
            self.log_tool_error("read_messages", e)
            raise
    
    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> Dict[str, Any]:
        """Add a reaction to a message."""
        self.log_tool_execution("add_reaction", channel_id=channel_id, message_id=message_id, emoji=emoji)
        
        try:
            # Normalize and URL encode the emoji
            normalized_emoji = normalize_emoji(emoji)
            # If this looks like a custom emoji (name:id), validate it exists in the guild
            is_custom = False
            custom_id = None
            if ":" in normalized_emoji:
                parts = normalized_emoji.rsplit(":", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    is_custom = True
                    custom_id = parts[1]

            if is_custom:
                try:
                    # Get channel info to determine guild id
                    channel_info = await self.auth.make_request("GET", f"/channels/{channel_id}")
                    guild_id = channel_info.get("guild_id")
                    if not guild_id:
                        raise RuntimeError("Custom emoji requires a guild channel (no guild_id found for channel)")

                    # Fetch guild emojis and ensure the custom emoji belongs to the guild
                    guild_emojis = await self.auth.make_request("GET", f"/guilds/{guild_id}/emojis")
                    emoji_ids = {e.get("id") for e in guild_emojis}
                    if custom_id not in emoji_ids:
                        raise RuntimeError(f"Custom emoji id {custom_id} not found in guild {guild_id} or bot lacks access to it")
                except Exception as e:
                    # Bubble up a clear error about custom emoji availability
                    self.log_tool_error("add_reaction", e)
                    return {
                        "success": False,
                        "error": str(e),
                        "emoji": emoji,
                        "message_id": message_id,
                        "channel_id": channel_id
                    }
            encoded_emoji = urllib.parse.quote(normalized_emoji, safe='')
            endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
            
            await self.auth.make_request("PUT", endpoint, expect_empty_response=True)
            return {
                "success": True,
                "message": f"Successfully added reaction {emoji} to message {message_id}",
                "emoji": emoji,
                "message_id": message_id,
                "channel_id": channel_id
            }
        except Exception as e:
            self.log_tool_error("add_reaction", e)
            return {
                "success": False,
                "error": str(e),
                "emoji": emoji,
                "message_id": message_id,
                "channel_id": channel_id
            }
    
    async def add_multiple_reactions(self, channel_id: str, message_id: str, emojis: List[str]) -> Dict[str, Any]:
        """Add multiple reactions to a message."""
        self.log_tool_execution("add_multiple_reactions", channel_id=channel_id, message_id=message_id, emojis=emojis)
        
        results = []
        errors = []
        # Attempt each emoji sequentially and record successes/failures with clear messages
        for emoji in emojis:
            try:
                # Call add_reaction which now returns clear failure if custom emoji invalid
                result = await self.add_reaction(channel_id, message_id, emoji)
                if result.get("success"):
                    results.append({"emoji": emoji, "success": True})
                else:
                    errors.append({"emoji": emoji, "error": result.get("error", "Unknown error")})
            except Exception as e:
                # Unexpected exceptions should be captured and included in failed_reactions
                self.log_tool_error("add_multiple_reactions", e)
                errors.append({"emoji": emoji, "error": str(e)})
        
        return {
            "success": len(errors) == 0,
            "message_id": message_id,
            "channel_id": channel_id,
            "successful_reactions": results,
            "failed_reactions": errors,
            "summary": f"Added {len(results)} reactions successfully, {len(errors)} failed"
        }
    
    async def remove_reaction(self, channel_id: str, message_id: str, emoji: str) -> Dict[str, Any]:
        """Remove a reaction from a message."""
        self.log_tool_execution("remove_reaction", channel_id=channel_id, message_id=message_id, emoji=emoji)
        
        try:
            normalized_emoji = normalize_emoji(emoji)
            encoded_emoji = urllib.parse.quote(normalized_emoji, safe='')
            endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
            
            await self.auth.make_request("DELETE", endpoint, expect_empty_response=True)
            return {
                "success": True,
                "message": f"Successfully removed reaction {emoji} from message {message_id}",
                "emoji": emoji,
                "message_id": message_id,
                "channel_id": channel_id
            }
        except Exception as e:
            self.log_tool_error("remove_reaction", e)
            return {
                "success": False,
                "error": str(e),
                "emoji": emoji,
                "message_id": message_id,
                "channel_id": channel_id
            }
