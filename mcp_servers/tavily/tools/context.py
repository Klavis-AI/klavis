"""Context search tool for Tavily MCP Server."""
from mcp.server.fastmcp import FastMCP

from ..client import tavily_client
from ..models import TavilySearchResponse
from ..utils import prepare_search_params
from ..config import Config

# This will be injected by main.py
mcp = None

def register_context_tools(mcp_instance: FastMCP):
    """Register context tools with MCP server."""
    global mcp
    mcp = mcp_instance
    
    @mcp.tool()
    def tavily_search_context(
        query: str,
        context: str,
        search_depth: str = Config.DEFAULT_SEARCH_DEPTH,
        max_results: int = Config.DEFAULT_MAX_RESULTS,
        include_answer: bool = True
    ) -> TavilySearchResponse:
        """
        Perform a contextual search where additional context helps refine the search query.
        
        This tool allows you to provide background context that will help Tavily
        understand the search intent better and return more relevant results.
        
        Args:
            query: The main search query
            context: Additional context to help refine the search
            search_depth: Search depth level 
            max_results: Maximum number of results to return
            include_answer: Whether to include a synthesized answer
            
        Returns:
            Contextually-refined search results
        """
        # Combine query and context for better search
        enhanced_query = f"{query} {context}"
        
        params = prepare_search_params(
            query=enhanced_query,
            search_depth=search_depth,
            topic="general",
            max_results=max_results,
            include_answer=include_answer,
            include_images=False,
            include_raw_content=False
        )
        
        return tavily_client.search(**params)