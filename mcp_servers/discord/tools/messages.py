"""
Discord Message Management Tools

Handles Discord message operations including sending, reading, and reactions.
"""

from typing import Any, Dict, List, Union

from .base import DiscordBaseTool


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
        self.log_tool_execution("send_message", channel_id=channel_id, content=content[:50] + "...")
        
        try:
            endpoint = f"/channels/{channel_id}/messages"
            message_data = {"content": content}
            
            response = await self.auth.make_request("POST", endpoint, message_data)
            
            return {
                "message_id": response.get("id"),
                "channel_id": channel_id,
                "content_preview": content[:50] + ("..." if len(content) > 50 else "")
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
    
    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> str:
        """Add a reaction to a message."""
        self.log_tool_execution("add_reaction", channel_id=channel_id, message_id=message_id, emoji=emoji)
        
        try:
            # URL encode the emoji
            import urllib.parse
            encoded_emoji = urllib.parse.quote(emoji, safe='')
            endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
            
            await self.auth.make_request("PUT", endpoint, expect_empty_response=True)
            return f"Successfully added reaction {emoji} to message {message_id}"
        except Exception as e:
            self.log_tool_error("add_reaction", e)
            return f"Error adding reaction {emoji} to message {message_id}: {str(e)}"
    
    async def add_multiple_reactions(self, channel_id: str, message_id: str, emojis: List[str]) -> str:
        """Add multiple reactions to a message."""
        self.log_tool_execution("add_multiple_reactions", channel_id=channel_id, message_id=message_id, emojis=emojis)
        
        results = []
        errors = []
        
        for emoji in emojis:
            try:
                result = await self.add_reaction(channel_id, message_id, emoji)
                if "Error" not in result:
                    results.append(f"{emoji}: Success")
                else:
                    errors.append(f"{emoji}: {result}")
            except Exception as e:
                errors.append(f"{emoji}: {str(e)}")
        
        if errors:
            error_summary = "; ".join(errors)
            return f"Finished adding multiple reactions to message {message_id}. Errors encountered: {error_summary}."
        else:
            return f"Successfully added all reactions to message {message_id}"
    
    async def remove_reaction(self, channel_id: str, message_id: str, emoji: str) -> str:
        """Remove a reaction from a message."""
        self.log_tool_execution("remove_reaction", channel_id=channel_id, message_id=message_id, emoji=emoji)
        
        try:
            import urllib.parse
            encoded_emoji = urllib.parse.quote(emoji, safe='')
            endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me"
            
            await self.auth.make_request("DELETE", endpoint, expect_empty_response=True)
            return f"Successfully removed reaction {emoji} from message {message_id}"
        except Exception as e:
            self.log_tool_error("remove_reaction", e)
            return f"Error removing reaction {emoji} from message {message_id}: {str(e)}"
