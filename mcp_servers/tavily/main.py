"""
Tavily MCP Server - Main entry point

A Model Context Protocol server that provides access to Tavily's AI-powered search engine.
Tavily is specifically optimized for LLM use cases, providing high-quality, relevant search 
results with built-in content extraction and filtering.

Usage:
    # Set your Tavily API key as an environment variable
    export TAVILY_API_KEY="tvly-YOUR_API_KEY"
    
    # Run with MCP
    uv run mcp dev main.py
"""


from mcp.server.fastmcp import FastMCP

# Import tool registration functions
from tools.search import register_search_tools
from tools.extract import register_extract_tools
from tools.news import register_news_tools
from tools.context import register_context_tools
from resources import register_resources

# Create FastMCP server
mcp = FastMCP("Tavily Search")

# Register all tools
register_search_tools(mcp)
register_extract_tools(mcp)
register_news_tools(mcp)
register_context_tools(mcp)

# Register resources
register_resources(mcp)

# Main execution
if __name__ == "__main__":
    # Run the server
    mcp.run()