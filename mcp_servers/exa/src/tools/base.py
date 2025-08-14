"""
Base tool class for Exa MCP Server
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..client.exa_client import ExaClient
from ..utils.logging import get_logger
from ..utils.formatters import ResponseFormatter

logger = get_logger("tools")


class BaseTool(ABC):
    """Base class for all MCP tools"""
    
    def __init__(self, client: ExaClient):
        self.client = client
        self.formatter = ResponseFormatter()
        self.logger = get_logger(f"tools.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for AI agents"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool inputs"""
        pass
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition"""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute the tool with given arguments
        
        Args:
            arguments: Tool arguments from AI agent
            
        Returns:
            List of text content responses
        """
        pass
    
    def _create_error_response(self, error_message: str) -> List[TextContent]:
        """Create a standardized error response"""
        formatted_error = self.formatter.format_error(self.name, error_message)
        return [TextContent(type="text", text=formatted_error)]
    
    def _create_success_response(self, text: str) -> List[TextContent]:
        """Create a standardized success response"""
        return [TextContent(type="text", text=text)]