#!/usr/bin/env python3
"""
Exa AI MCP Server for Klavis AI - Minimal Working Version
"""

import asyncio
import logging
import os
from typing import Any, Dict, List
from datetime import datetime, timedelta

from exa_py import Exa
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exa-mcp-server")

# Server instance
app = Server("exa-mcp-server")

def get_exa_client():
    """Initialize Exa client with API key from environment."""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY environment variable is required. Get your key from https://exa.ai/")
    return Exa(api_key)

def safe_format_score(score) -> str:
    """Safely format a score value that might be None."""
    if score is None:
        return "N/A"
    try:
        return f"{float(score):.3f}"
    except (ValueError, TypeError):
        return str(score)

def safe_get_attr(obj, attr_name: str, default: str = "N/A") -> str:
    """Safely get an attribute that might be None."""
    value = getattr(obj, attr_name, None)
    return str(value) if value is not None else default

@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List all available tools."""
    return [
        types.Tool(
            name="search_web_semantic",
            description="Search the web using Exa AI's semantic search. Use this when you need to find web pages about a specific topic using natural language understanding rather than keyword matching. Returns ranked results with titles, URLs, and relevance scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Natural language search query describing what you're looking for"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="extract_page_content",
            description="Extract clean, readable text content from a specific web page URL. Use this when you need to read or analyze the actual content of a webpage, removing HTML formatting and ads to get just the main text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The complete URL of the webpage to extract content from"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="find_similar_pages",
            description="Find web pages that are similar in content to a given URL. Use this for discovering related articles, finding competing content, or exploring content in the same domain space.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to find similar content for"
                    },
                    "num_results": {
                        "type": "integer", 
                        "description": "Number of similar pages to find",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="search_recent_content",
            description="Search for recent web content published within a specific time period. Use this when you need current information, recent news, or recently published articles on a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for recent content"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days back to search (e.g., 7 for last week, 30 for last month)",
                        "default": 7,
                        "minimum": 1,
                        "maximum": 365
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return", 
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_by_example_text",
            description="Find web content similar to a provided text sample. Use this when you have a piece of text and want to find web pages with similar content, style, or topics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The example text to find similar content for"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of similar results to find",
                        "default": 5,
                        "minimum": 1, 
                        "maximum": 20
                    }
                },
                "required": ["text"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution requests."""
    
    try:
        exa = get_exa_client()
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if name == "search_web_semantic":
            return await _search_web_semantic(exa, arguments)
        elif name == "extract_page_content":
            return await _extract_page_content(exa, arguments)
        elif name == "find_similar_pages":
            return await _find_similar_pages(exa, arguments)
        elif name == "search_recent_content":
            return await _search_recent_content(exa, arguments)
        elif name == "search_by_example_text":
            return await _search_by_example_text(exa, arguments)
        else:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            return [types.TextContent(type="text", text=error_msg)]
            
    except ValueError as e:
        error_msg = f"Configuration Error: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"Error in {name}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def _search_web_semantic(exa: Exa, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Execute semantic web search."""
    query = arguments["query"]
    num_results = arguments.get("num_results", 5)
    
    logger.info(f"Searching web for: '{query}' with {num_results} results")
    
    try:
        results = exa.search(query=query, num_results=num_results, use_autoprompt=True)
        
        if not results.results:
            return [types.TextContent(
                type="text", 
                text=f"No results found for query: '{query}'. Try a different search term or broader query."
            )]
        
        response = f"🔍 **Semantic Search Results for: '{query}'**\n\n"
        response += f"Found {len(results.results)} relevant results:\n\n"
        
        for i, result in enumerate(results.results, 1):
            response += f"**{i}. {safe_get_attr(result, 'title', 'No title')}**\n"
            response += f"📎 URL: {safe_get_attr(result, 'url', 'No URL')}\n"
            response += f"⭐ Relevance Score: {safe_format_score(getattr(result, 'score', None))}\n"
            
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                response += f"📅 Published: {pub_date}\n"
            response += "\n"
        
        logger.info(f"Successfully returned {len(results.results)} search results")
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        error_msg = f"Web search failed: {str(e)}. Please check your query and try again."
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def _extract_page_content(exa: Exa, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Extract content from a web page."""
    url = arguments["url"]
    
    logger.info(f"Extracting content from: {url}")
    
    try:
        results = exa.get_contents([url], text=True)
        
        if not results.results:
            return [types.TextContent(
                type="text",
                text=f"Could not extract content from URL: {url}. The page might be inaccessible or require authentication."
            )]
        
        content = results.results[0]
        response = f"📄 **Content Extracted from: {safe_get_attr(content, 'url', url)}**\n\n"
        
        title = safe_get_attr(content, 'title', 'No title available')
        if title != "No title available":
            response += f"**Title:** {title}\n\n"
        
        text_content = getattr(content, 'text', None)
        if text_content:
            text = text_content.strip()
            if len(text) > 3000:
                response += f"**Content (first 3000 characters):**\n{text[:3000]}...\n\n"
                response += f"*[Content truncated - total length: {len(text)} characters]*"
            else:
                response += f"**Content:**\n{text}"
        else:
            response += "**Content:** Unable to extract readable text from this page."
        
        logger.info(f"Successfully extracted content from {url}")
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        error_msg = f"Content extraction failed for {url}: {str(e)}. The page might be blocked or require special access."
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def _find_similar_pages(exa: Exa, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Find pages similar to a given URL."""
    url = arguments["url"]
    num_results = arguments.get("num_results", 5)
    
    logger.info(f"Finding similar pages to: {url}")
    
    try:
        results = exa.find_similar(url=url, num_results=num_results)
        
        if not results.results:
            return [types.TextContent(
                type="text",
                text=f"No similar pages found for: {url}. Try a different URL or check if the URL is accessible."
            )]
        
        response = f"🔗 **Pages Similar to: {url}**\n\n"
        response += f"Found {len(results.results)} similar pages:\n\n"
        
        for i, result in enumerate(results.results, 1):
            response += f"**{i}. {safe_get_attr(result, 'title', 'No title')}**\n"
            response += f"📎 URL: {safe_get_attr(result, 'url', 'No URL')}\n"
            response += f"⭐ Similarity Score: {safe_format_score(getattr(result, 'score', None))}\n"
            
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                response += f"📅 Published: {pub_date}\n"
            response += "\n"
        
        logger.info(f"Successfully found {len(results.results)} similar pages")
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        error_msg = f"Similar pages search failed for {url}: {str(e)}. Please verify the URL is valid and accessible."
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def _search_recent_content(exa: Exa, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Search for recent content."""
    query = arguments["query"]
    days_back = arguments.get("days_back", 7)
    num_results = arguments.get("num_results", 5)
    
    logger.info(f"Searching recent content for: '{query}' ({days_back} days back)")
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime("%Y-%m-%d")
        
        results = exa.search(
            query=query,
            num_results=num_results,
            start_published_date=start_date_str,
            use_autoprompt=True
        )
        
        if not results.results:
            return [types.TextContent(
                type="text",
                text=f"No recent content found for '{query}' in the last {days_back} days. Try a broader query or increase the time range."
            )]
        
        response = f"🕒 **Recent Content for: '{query}'** (Last {days_back} days)\n\n"
        response += f"Found {len(results.results)} recent results:\n\n"
        
        for i, result in enumerate(results.results, 1):
            response += f"**{i}. {safe_get_attr(result, 'title', 'No title')}**\n"
            response += f"📎 URL: {safe_get_attr(result, 'url', 'No URL')}\n"
            response += f"⭐ Relevance Score: {safe_format_score(getattr(result, 'score', None))}\n"
            
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                response += f"📅 Published: {pub_date}\n"
            response += "\n"
        
        logger.info(f"Successfully found {len(results.results)} recent results")
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        error_msg = f"Recent content search failed: {str(e)}. Please try a different query."
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def _search_by_example_text(exa: Exa, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Search for content similar to example text."""
    text = arguments["text"]
    num_results = arguments.get("num_results", 5)
    
    logger.info(f"Searching by example text (length: {len(text)} chars)")
    
    try:
        results = exa.search(
            query=text,
            num_results=num_results,
            type="neural",
            use_autoprompt=False
        )
        
        if not results.results:
            return [types.TextContent(
                type="text",
                text=f"No similar content found for the provided text sample. Try a longer or more specific text example."
            )]
        
        example_preview = text[:200] + "..." if len(text) > 200 else text
        
        response = f"📝 **Content Similar to Example Text:**\n\n"
        response += f"**Example:** {example_preview}\n\n"
        response += f"Found {len(results.results)} similar results:\n\n"
        
        for i, result in enumerate(results.results, 1):
            response += f"**{i}. {safe_get_attr(result, 'title', 'No title')}**\n"
            response += f"📎 URL: {safe_get_attr(result, 'url', 'No URL')}\n"
            response += f"⭐ Similarity Score: {safe_format_score(getattr(result, 'score', None))}\n"
            
            pub_date = getattr(result, 'published_date', None)
            if pub_date:
                response += f"📅 Published: {pub_date}\n"
            response += "\n"
        
        logger.info(f"Successfully found {len(results.results)} similar text results")
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        error_msg = f"Example text search failed: {str(e)}. Please try a different text sample."
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Exa AI MCP Server...")
    
    # Verify Exa API key is available
    try:
        get_exa_client()
        logger.info("Exa API key validated successfully")
    except ValueError as e:
        logger.error(f"Startup failed: {e}")
        return
    
    # Use stdin/stdout for MCP communication
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="exa-mcp-server",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=False)
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())