"""News search tool for Tavily MCP Server."""
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from ..client import tavily_client
from ..models import TavilySearchResponse
from ..utils import prepare_search_params

# This will be injected by main.py
mcp = None

def register_news_tools(mcp_instance: FastMCP):
    """Register news tools with MCP server."""
    global mcp
    mcp = mcp_instance
    
    @mcp.tool()
    def tavily_news_search(
        query: str,
        search_depth: str = "basic",
        max_results: int = 10,
        include_images: bool = True,
        days: Optional[int] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> TavilySearchResponse:
        """
        Search for recent news articles using Tavily's news-optimized search.
        
        This tool is specifically tuned for finding recent, relevant news content
        with proper source attribution and recency filtering.
        
        Args:
            query: News search query
            search_depth: Search depth level ("basic" recommended for news)
            max_results: Maximum number of news articles to return (default: 10)
            include_images: Whether to include images from news articles
            days: Limit results to articles from the last N days (optional)
            include_domains: List of news domains to specifically search
            exclude_domains: List of domains to exclude from news search
            
        Returns:
            Recent news articles matching the search query
        """
        params = prepare_search_params(
            query=query,
            search_depth=search_depth,
            topic="news",
            max_results=max_results,
            include_images=include_images,
            include_answer=True,
            include_raw_content=False,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        
        # Add days filter if specified
        if days:
            params["days"] = days
        
        return tavily_client.search(**params)