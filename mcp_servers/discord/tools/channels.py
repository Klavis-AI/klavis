"""
Discord Channel Management Tools

Handles Discord channel operations.
"""

from typing import Any, Dict, List, Optional

from .base import DiscordBaseTool


class ChannelTool(DiscordBaseTool):
    """Tool for Discord channel management operations."""
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get channel management tool definitions."""
        return [
            {
                "name": "create_text_channel",
                "description": "Create a new text channel",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild) where the channel will be created"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name for the new text channel"
                        },
                        "topic": {
                            "type": "string",
                            "description": "The topic for the new channel"
                        },
                        "category_id": {
                            "type": "string",
                            "description": "The ID of the category (parent channel) to place the new channel under"
                        }
                    },
                    "required": ["server_id", "name"]
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle channel management tool calls."""
        if tool_name == "create_text_channel":
            return await self.create_text_channel(
                arguments["server_id"],
                arguments["name"],
                arguments.get("topic"),
                arguments.get("category_id")
            )
        else:
            raise NotImplementedError(f"Tool {tool_name} not implemented")
    
    async def create_text_channel(
        self, 
        server_id: str, 
        name: str, 
        topic: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new text channel in a Discord server."""
        self.log_tool_execution(
            "create_text_channel", 
            server_id=server_id, 
            name=name, 
            topic=topic,
            category_id=category_id
        )
        
        try:
            endpoint = f"/guilds/{server_id}/channels"
            channel_data = {
                "name": name,
                "type": 0  # Text channel type
            }
            
            if topic:
                channel_data["topic"] = topic
            if category_id:
                channel_data["parent_id"] = category_id
            
            response = await self.auth.make_request("POST", endpoint, channel_data)
            
            return {
                "id": response.get("id"),
                "name": response.get("name"),
                "topic": response.get("topic"),
                "parent_id": response.get("parent_id")
            }
        except Exception as e:
            self.log_tool_error("create_text_channel", e)
            raise
