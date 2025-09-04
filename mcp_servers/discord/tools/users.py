"""
Discord User Management Tools

Handles Discord user-related operations.
"""

from typing import Any, Dict, List

from .base import DiscordBaseTool


class UserTool(DiscordBaseTool):
    """Tool for Discord user management operations."""
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get user management tool definitions."""
        return [
            {
                "name": "get_user_info",
                "description": "Retrieve information about a specific Discord user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the Discord user to retrieve information for"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle user management tool calls."""
        if tool_name == "get_user_info":
            return await self.get_user_info(arguments["user_id"])
        else:
            raise NotImplementedError(f"Tool {tool_name} not implemented")
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about a Discord user."""
        self.log_tool_execution("get_user_info", user_id=user_id)
        
        try:
            endpoint = f"/users/{user_id}"
            user_data = await self.auth.make_request("GET", endpoint)
            
            return {
                "id": user_data.get("id"),
                "username": user_data.get("username"),
                "discriminator": user_data.get("discriminator"),
                "global_name": user_data.get("global_name"),
                "is_bot": user_data.get("bot", False),
                "avatar_hash": user_data.get("avatar")
            }
        except Exception as e:
            self.log_tool_error("get_user_info", e)
            raise
