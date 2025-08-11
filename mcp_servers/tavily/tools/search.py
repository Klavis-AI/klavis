"""General search tools for Tavily MCP Server."""
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from ..client import tavily_client
from ..models import TavilySearchResponse
from ..utils import prepare_search_params
from ..config import Config

# This will be injected by main.py
mcp = None

def register_search_tools(mcp_instance: FastMCP):
    """Register search tools with MCP server."""
    global mcp
    mcp = mcp_instance
    
    @mcp.tool()
    def tavily_search(
        query: str,
        search_depth: str = Config.DEFAULT_SEARCH_DEPTH,
        topic: str = Config.DEFAULT_TOPIC, 
        max_results: int = Config.DEFAULT_MAX_RESULTS,
        include_images: bool = False,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> TavilySearchResponse:
        """
        Perform an AI-optimized web search using Tavily's search engine.
        
        Tavily is specifically designed for LLM use cases, providing high-quality, 
        relevant results with built-in content filtering and extraction.
        
        Args:
            query: The search query to execute
            search_depth: Search depth level - "basic" for quick results, "advanced" for comprehensive search
            topic: Search topic category - "general", "news", or other specific domains
            max_results: Maximum number of results to return (default: 5, max: 20)
            include_images: Whether to include image URLs in results  
            include_answer: Whether to include a direct answer to the query
            include_raw_content: Whether to include full raw content for each result
            include_domains: List of domains to specifically include in search
            exclude_domains: List of domains to exclude from search
            
        Returns:
            Structured search results optimized for AI consumption
        """
        params = prepare_search_params(
            query=query,
            search_depth=search_depth,
            topic=topic,
            max_results=max_results,
            include_images=include_images,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        
        return tavily_client.search(**params)

    @mcp.tool()
    def tavily_qna(
        query: str,
        search_depth: str = "advanced",
        max_results: int = Config.DEFAULT_MAX_RESULTS,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> TavilySearchResponse:
        """
        Perform a question-answering search optimized for direct answers.
        
        This tool focuses on providing direct, factual answers to specific questions
        by leveraging Tavily's QnA-optimized search algorithms.
        
        Args:
            query: The question to answer
            search_depth: Search depth - "basic" or "advanced" (advanced recommended for QnA)
            max_results: Maximum supporting results to include
            include_domains: List of domains to specifically search within
            exclude_domains: List of domains to exclude from search
            
        Returns:
            Search results with emphasis on direct answers and supporting sources
        """
        params = prepare_search_params(
            query=query,
            search_depth=search_depth,
            topic="general",
            max_results=max_results,
            include_answer=True,
            include_images=False,
            include_raw_content=False,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        
        return tavily_client.search(**params)