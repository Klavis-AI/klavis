"""
Discord Server Management Tools

Handles Discord server (guild) related operations.
"""

from typing import Any, Dict, List

from .base import DiscordBaseTool


class ServerTool(DiscordBaseTool):
    """Tool for Discord server management operations."""
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get server management tool definitions."""
        return [
            {
                "name": "get_server_info",
                "description": "Retrieve detailed information about a Discord server (guild)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild) to retrieve information for"
                        }
                    },
                    "required": ["server_id"]
                }
            },
            {
                "name": "list_members", 
                "description": "Get a list of members in a server with customizable result limits",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_id": {
                            "type": "string",
                            "description": "The ID of the Discord server (guild)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of members to return (1-1000)",
                            "minimum": 1,
                            "maximum": 1000,
                            "default": 100
                        }
                    },
                    "required": ["server_id"]
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle server management tool calls."""
        if tool_name == "get_server_info":
            return await self.get_server_info(arguments["server_id"])
        elif tool_name == "list_members":
            return await self.list_members(
                arguments["server_id"], 
                arguments.get("limit", 100)
            )
        else:
            raise NotImplementedError(f"Tool {tool_name} not implemented")
    
    async def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Get information about a Discord server (guild)."""
        self.log_tool_execution("get_server_info", server_id=server_id)
        
        try:
            endpoint = f"/guilds/{server_id}?with_counts=true"
            guild_data = await self.auth.make_request("GET", endpoint)
            
            return {
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
        except Exception as e:
            self.log_tool_error("get_server_info", e)
            raise
    
    async def list_members(self, server_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get a list of members in a server."""
        self.log_tool_execution("list_members", server_id=server_id, limit=limit)
        
        try:
            clamped_limit = max(1, min(limit, 1000))
            endpoint = f"/guilds/{server_id}/members?limit={clamped_limit}"
            members_data = await self.auth.make_request("GET", endpoint)
            
            members = []
            for member in members_data:
                user = member.get("user", {})
                member_info = {
                    "id": user.get("id"),
                    "username": user.get("username"),
                    "discriminator": user.get("discriminator"),
                    "global_name": user.get("global_name"),
                    "nick": member.get("nick"),
                    "joined_at": member.get("joined_at"),
                    "roles": member.get("roles", [])
                }
                members.append(member_info)
            
            return members
        except Exception as e:
            self.log_tool_error("list_members", e)
            raise
