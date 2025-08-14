"""
Discovery and analysis tools for Exa MCP Server
"""

from typing import Any, Dict, List
from mcp.types import TextContent

from .base import BaseTool
from ..models.schemas import ExaSimilarParams


class FindSimilarContentTool(BaseTool):
    """Tool for finding similar content based on a URL"""
    
    @property
    def name(self) -> str:
        return "find_similar_content"
    
    @property
    def description(self) -> str:
        return (
            "Find web pages similar to a given URL using Exa's AI similarity detection. "
            "This tool analyzes the content, topic, and context of the provided URL to find "
            "semantically similar pages. Great for content discovery, competitive analysis, "
            "or finding alternative sources on the same topic."
        )
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to find similar content for (must include http:// or https://)"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of similar results to return (1-100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to include in similar results"
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to exclude from similar results"
                },
                "category": {
                    "type": "string",
                    "description": "Filter similar content by category"
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute similarity search"""
        try:
            params = ExaSimilarParams(**arguments)
            result = await self.client.find_similar(params)
            
            if not result.success:
                return self._create_error_response(result.error)
            
            # Format the response
            results = result.data.get("results", [])
            formatted_response = self.formatter.format_similar_results(
                results, params.url
            )
            
            return self._create_success_response(formatted_response)
            
        except Exception as e:
            self.logger.error(f"Similarity search execution error: {str(e)}")
            return self._create_error_response(str(e))