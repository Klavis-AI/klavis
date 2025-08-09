"""
Google Hotels MCP Server
A Model Context Protocol server for hotel search and booking assistance
"""
import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from api_client import GoogleHotelsApiClient, SerpApiError
from tools import GoogleHotelsTools

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_HOTELS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_HOTELS_MCP_SERVER_PORT", "5000"))

# Global tools instance
hotel_tools: GoogleHotelsTools = None

@click.command()
@click.option("--port", default=GOOGLE_HOTELS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    global hotel_tools
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check for required environment variables
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.error("SERPAPI_API_KEY environment variable is required")
        logger.info("Please get your API key from https://serpapi.com and set it as an environment variable")
        return 1
    
    try:
        # Initialize API client and tools
        api_client = GoogleHotelsApiClient(api_key)
        hotel_tools = GoogleHotelsTools(api_client)
        logger.info("Google Hotels API client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Hotels API client: {e}")
        return 1

    # Create the MCP server instance
    app = Server("google-hotels-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_hotels_search_hotels",
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
            
            types.Tool(
                name="google_hotels_search_hotels_with_filters",
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
                            "description": "List of required amenity IDs (use google_hotels_get_supported_amenities to see options)"
                        },
                        "brands": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of preferred hotel brand IDs"
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
            ),

            types.Tool(
                name="google_hotels_compare_hotel_prices",
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

            types.Tool(
                name="google_hotels_get_booking_links",
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

            types.Tool(
                name="google_hotels_get_supported_amenities",
                description=(
                    "Get a list of all supported amenities with their IDs for use in advanced hotel searches. "
                    "Use these amenity IDs with the google_hotels_search_hotels_with_filters tool to find hotels "
                    "with specific amenities like pools, gyms, free WiFi, etc."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        try:
            # Route to appropriate tool (updated names)
            if name == "google_hotels_search_hotels":
                result = await hotel_tools.search_hotels(arguments)
            elif name == "google_hotels_search_hotels_with_filters":
                result = await hotel_tools.search_hotels_with_filters(arguments)
            elif name == "google_hotels_compare_hotel_prices":
                result = await hotel_tools.compare_hotel_prices(arguments)
            elif name == "google_hotels_get_booking_links":
                result = await hotel_tools.get_booking_links(arguments)
            elif name == "google_hotels_get_supported_amenities":
                result = await hotel_tools.get_supported_amenities(arguments)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {name}",
                    "suggestion": "Use one of the available tools listed in list_tools"
                }
        # ... rest of the function stays the same
            
            # Return as TextContent
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False),
                )
            ]
            
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            error_result = {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool": name
            }
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(error_result, indent=2),
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(
                streams[0], streams[1], app.create_initialization_options()
            )
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Google Hotels MCP Server started with dual transports!")
            logger.info("Available tools: google_hotels_search_hotels, google_hotels_search_hotels_with_filters, google_hotels_compare_hotel_prices, google_hotels_get_booking_links, google_hotels_get_supported_amenities")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()