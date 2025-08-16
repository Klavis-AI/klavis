"""
Discord Base Tool Module

Provides base class and common functionality for Discord MCP tools.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .auth import DiscordAuth

logger = logging.getLogger("discord-mcp-server")


class DiscordBaseTool(ABC):
    """Base class for Discord MCP tools."""
    
    def __init__(self, auth: DiscordAuth):
        """
        Initialize base tool.
        
        Args:
            auth: Discord authentication instance
        """
        self.auth = auth
    
    @abstractmethod
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get MCP tool definitions for this tool.
        
        Returns:
            List of tool definitions
        """
        pass
    
    @abstractmethod
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Handle MCP tool call.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    def log_tool_execution(self, tool_name: str, **kwargs):
        """Log tool execution for debugging."""
        args_str = ", ".join(f"{k}: {v}" for k, v in kwargs.items())
        logger.info(f"Executing tool: {tool_name} with {args_str}")
    
    def log_tool_error(self, tool_name: str, error: Exception):
        """Log tool execution error."""
        logger.exception(f"Error executing tool {tool_name}: {error}")


class DiscordToolRegistry:
    """Registry for managing Discord MCP tools."""
    
    def __init__(self, auth: DiscordAuth):
        """Initialize tool registry."""
        self.auth = auth
        self.tools: Dict[str, DiscordBaseTool] = {}
    
    def register_tool(self, name: str, tool: DiscordBaseTool):
        """Register a tool."""
        self.tools[name] = tool
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions from registered tools."""
        definitions = []
        for tool in self.tools.values():
            definitions.extend(tool.get_tool_definitions())
        return definitions
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool call by routing to appropriate tool."""
        for tool in self.tools.values():
            try:
                return await tool.handle_tool_call(tool_name, arguments)
            except NotImplementedError:
                continue
        
        raise ValueError(f"Unknown tool: {tool_name}")
