"""MCP resources for Tavily server."""
from mcp.server.fastmcp import FastMCP

def register_resources(mcp: FastMCP):
    """Register MCP resources."""
    
    @mcp.resource("tavily://info")
    def tavily_info() -> str:
        """
        Get information about the Tavily AI search engine and this MCP server.
        """
        return """# Tavily AI Search Engine

Tavily is a search engine optimized specifically for AI agents and LLMs. Unlike traditional search APIs, Tavily:

## Key Features
- **AI-Optimized Results**: Search results are filtered and ranked for relevance to AI use cases
- **Content Extraction**: Built-in content extraction and summarization  
- **Answer Generation**: Provides direct answers to queries when possible
- **Domain Control**: Ability to include/exclude specific domains
- **News Focus**: Specialized news search capabilities
- **Speed**: Fast response times optimized for real-time AI applications

## This MCP Server Provides
- `tavily_search`: General web search optimized for AI
- `tavily_extract`: Content extraction from URLs
- `tavily_qna`: Question-answering focused search
- `tavily_news_search`: Recent news article search  
- `tavily_search_context`: Contextual search with additional background

## Getting Started
1. Get a free API key from https://app.tavily.com
2. Set the TAVILY_API_KEY environment variable
3. Use the tools to search the web with AI-optimized results

## Rate Limits
- Free tier: 1,000 requests/month
- Paid tiers available for higher usage
"""