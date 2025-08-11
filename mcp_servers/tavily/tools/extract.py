"""Content extraction tool for Tavily MCP Server."""
from mcp.server.fastmcp import FastMCP

from ..client import tavily_client
from ..models import ExtractedContent

# This will be injected by main.py
mcp = None

def register_extract_tools(mcp_instance: FastMCP):
    """Register extract tools with MCP server."""
    global mcp
    mcp = mcp_instance
    
    @mcp.tool()  
    def tavily_extract(url: str) -> ExtractedContent:
        """
        Extract clean, readable content from a specific URL using Tavily's extraction engine.
        
        This tool is optimized for extracting main content while filtering out navigation,
        ads, and other non-essential elements.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Extracted content from the specified URL
        """
        return tavily_client.extract(url)