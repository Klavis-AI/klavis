"""
Google Hotels MCP Server
A Model Context Protocol server for hotel search and booking assistance
"""
import asyncio
import logging
import os
from typing import Any, Sequence
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from .api_client import GoogleHotelsApiClient, SerpApiError
from .tools import GoogleHotelsTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("google-hotels-mcp")

# Initialize MCP Server
app = Server("google-hotels-mcp")

# Global tools instance (initialized in main)
hotel_tools: GoogleHotelsTools = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools for the Google Hotels MCP server
    """
    return [
        Tool(
            name="search_hotels",
            description=(
                "Search for hotels in a specific location with check-in and check-out dates. "
                "Returns a list of available hotels with basic information like name, price, and rating. "
                "Perfect for finding accommodation options for travel planning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Location or hotel name to search (e.g., 'New York', 'Paris hotels', 'Tokyo')"
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format (e.g., '2024-12-15')"
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format (e.g., '2024-12-20')"
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults (default: 2)",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "children": {
                        "type": "integer",
                        "description": "Number of children (default: 0)",
                        "default": 0,
                        "minimum": 0,
                        "maximum": 10
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code for prices (default: 'USD')",
                        "default": "USD"
                    }
                },
                "required": ["query", "check_in_date", "check_out_date"]
            }
        ),
        
        Tool(
            name="get_supported_amenities",
            description=(
                "Get a list of all supported amenities with their IDs for use in advanced hotel searches. "
                "Use these amenity IDs with the search_hotels_with_filters tool to find hotels "
                "with specific amenities like pools, gyms, free WiFi, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        
        Tool(
            name="compare_hotel_prices",
            description=(
                "Compare prices, ratings, and value across hotels in a location. "
                "Identifies the cheapest, highest-rated, and best value options with "
                "price statistics and recommendations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Location to compare hotels in"
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults",
                        "default": 2
                    },
                    "children": {
                        "type": "integer",
                        "description": "Number of children",
                        "default": 0
                    }
                },
                "required": ["query", "check_in_date", "check_out_date"]
            }
        ),
        Tool(
            name="get_booking_links",
            description=(
                "Get booking links and pricing options for a specific hotel. "
                "Provides direct links to book the hotel on various platforms including "
                "the hotel's official website and trusted booking sites. Requires a "
                "property_token from previous search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "property_token": {
                        "type": "string",
                        "description": "Unique hotel property token from search results (required)"
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults (default: 2)",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "children": {
                        "type": "integer",
                        "description": "Number of children (default: 0)",
                        "default": 0,
                        "minimum": 0,
                        "maximum": 10
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code for prices (default: 'USD')",
                        "default": "USD"
                    }
                },
                "required": ["property_token", "check_in_date", "check_out_date"]
            }
        ),
        Tool(
            name="search_hotels_with_filters",
            description=(
                "Advanced hotel search with filtering options like price range, minimum rating, "
                "amenities, and hotel brands. Perfect for finding specific types of accommodations "
                "that match detailed preferences and requirements."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Location or hotel name to search (e.g., 'New York', 'Paris hotels')"
                    },
                    "check_in_date": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out_date": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "adults": {
                        "type": "integer",
                        "description": "Number of adults (default: 2)",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 30
                    },
                    "children": {
                        "type": "integer",
                        "description": "Number of children (default: 0)",
                        "default": 0,
                        "minimum": 0,
                        "maximum": 10
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price per night in USD"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price per night in USD"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum hotel rating (3.5, 4.0, or 4.5)",
                        "enum": [3.5, 4.0, 4.5]
                    },
                    "amenities": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of required amenity IDs (use get_supported_amenities to see options)"
                    },
                    "brands": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of preferred hotel brand IDs (use get_supported_brands to see options)"
                    },
                    "sort_by": {
                        "type": "integer",
                        "description": "Sort order: 3 for lowest price, 13 for highest rating",
                        "enum": [3, 13]
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code for prices (default: 'USD')",
                        "default": "USD"
                    }
                },
                "required": ["query", "check_in_date", "check_out_date"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """
    Handle tool calls from the MCP client
    """
    if arguments is None:
        arguments = {}
    
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        # Route to appropriate tool
        if name == "search_hotels":
            result = await hotel_tools.search_hotels(arguments)
        elif name == "get_supported_amenities":
            result = await hotel_tools.get_supported_amenities(arguments)
        elif name == "compare_hotel_prices":
            result = await hotel_tools.compare_hotel_prices(arguments)
        elif name == "get_booking_links":
            result = await hotel_tools.get_booking_links(arguments)
        elif name == "search_hotels_with_filters":
            result = await hotel_tools.search_hotels_with_filters(arguments)
        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}",
                "suggestion": "Use one of the available tools listed in list_tools"
            }
        
        # Format result as JSON string
        result_text = json.dumps(result, indent=2, ensure_ascii=False)
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        error_result = {
            "success": False,
            "error": f"Tool execution failed: {str(e)}",
            "tool": name
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """
    Main entry point for the MCP server
    """
    global hotel_tools
    
    # Check for required environment variables
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.error("SERPAPI_API_KEY environment variable is required")
        logger.info("Please get your API key from https://serpapi.com and set it as an environment variable")
        return
    
    try:
        # Initialize API client and tools
        api_client = GoogleHotelsApiClient(api_key)
        hotel_tools = GoogleHotelsTools(api_client)
        
        logger.info("Google Hotels MCP Server starting...")
        logger.info("Available tools: search_hotels, get_supported_amenities, compare_hotel_prices, get_booking_links, search_hotels_with_filters")
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())