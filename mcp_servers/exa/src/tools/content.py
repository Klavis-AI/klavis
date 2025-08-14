"""
Content extraction tools for Exa MCP Server
"""

from typing import Any, Dict, List
from mcp.types import TextContent

from .base import BaseTool
from ..models.schemas import ExaContentsParams


class GetPageContentsTool(BaseTool):
    """Tool for retrieving full page contents"""
    
    @property
    def name(self) -> str:
        return "get_page_contents"
    
    @property
    def description(self) -> str:
        return (
            "Retrieve the full text content of web pages from Exa search results. "
            "Use this after performing a search to get detailed content from specific pages. "
            "Can include highlights and AI-generated summaries. Requires the result IDs "
            "from a previous search operation."
        )
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Exa result IDs to get contents for (from search results)"
                },
                "text": {
                    "type": "boolean",
                    "description": "Whether to include full text content",
                    "default": True
                },
                "highlights": {
                    "type": "boolean",
                    "description": "Whether to include highlighted relevant passages",
                    "default": False
                },
                "summary": {
                    "type": "boolean",
                    "description": "Whether to include AI-generated summary of the content",
                    "default": False
                }
            },
            "required": ["ids"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute content retrieval"""
        try:
            params = ExaContentsParams(**arguments)
            result = await self.client.get_contents(params)
            
            if not result.success:
                return self._create_error_response(result.error)
            
            # Format the response
            results = result.data.get("results", [])
            formatted_response = self.formatter.format_contents(
                results, arguments
            )
            
            return self._create_success_response(formatted_response)
            
        except Exception as e:
            self.logger.error(f"Content retrieval execution error: {str(e)}")
            return self._create_error_response(str(e))