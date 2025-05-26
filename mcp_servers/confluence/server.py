import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
import json

import click
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv
import aiohttp
import asyncio

# Import the Confluence tools
from tools import ConfluenceFetcher, ConfluenceConfig, ConfluenceClient
import mcp.types as types

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Confluence API constants and configuration
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_MCP_SERVER_PORT = int(os.getenv("CONFLUENCE_MCP_SERVER_PORT", "5001"))

if not CONFLUENCE_BASE_URL or not (CONFLUENCE_API_TOKEN or CONFLUENCE_USERNAME):
    raise ValueError("CONFLUENCE_BASE_URL and either CONFLUENCE_API_TOKEN or CONFLUENCE_USERNAME environment variables are required")

# Create the Confluence client instance
client = ConfluenceClient(
    base_url=CONFLUENCE_BASE_URL,
    username=CONFLUENCE_USERNAME,
    api_token=CONFLUENCE_API_TOKEN
)

fetcher = ConfluenceFetcher()
fetcher.client = client

@click.command()
@click.option("--port", default=CONFLUENCE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("confluence-mcp-server")

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="search_confluence",
                description="Search for content in Confluence",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        },
                        "space_key": {
                            "type": "string",
                            "description": "Limit search to a specific space",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                },
            ),
            types.Tool(
                name="get_page",
                description="Get a Confluence page by ID",
                inputSchema={
                    "type": "object",
                    "required": ["page_id"],
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page to retrieve",
                        },
                        "expand": {
                            "type": "string",
                            "description": "Properties to expand (comma-separated)"
                        }
                    },
                },
            ),
            types.Tool(
                name="get_spaces",
                description="Get a list of Confluence spaces",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of spaces to return",
                            "default": 10
                        },
                        "space_type": {
                            "type": "string",
                            "description": "Type of spaces to return (global, personal)",
                            "enum": ["global", "personal"]
                        }
                    },
                },
            ),
            types.Tool(
                name="get_page_children",
                description="Get children of a Confluence page",
                inputSchema={
                    "type": "object",
                    "required": ["page_id"],
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the parent page",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of children to return",
                            "default": 10
                        }
                    },
                },
            ),
            types.Tool(
                name="get_page_comments",
                description="Get comments on a Confluence page",
                inputSchema={
                    "type": "object",
                    "required": ["page_id"],
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The ID of the page",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of comments to return",
                            "default": 10
                        }
                    },
                },
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "search_confluence":
            query = arguments.get("query")
            space_key = arguments.get("space_key")
            limit = arguments.get("limit", 10)
            
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await search_content(query, space_key, limit)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "get_page":
            page_id = arguments.get("page_id")
            expand = arguments.get("expand", "body.storage,version")
            
            if not page_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: page_id parameter is required",
                    )
                ]
            
            try:
                result = await get_page_content(page_id, expand)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "get_spaces":
            limit = arguments.get("limit", 10)
            space_type = arguments.get("space_type")
            
            try:
                result = await get_spaces(limit, space_type)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "get_page_children":
            page_id = arguments.get("page_id")
            limit = arguments.get("limit", 10)
            
            if not page_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: page_id parameter is required",
                    )
                ]
            
            try:
                result = await get_page_children(page_id, limit)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "get_page_comments":
            page_id = arguments.get("page_id")
            limit = arguments.get("limit", 10)
            
            if not page_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: page_id parameter is required",
                    )
                ]
            
            try:
                result = await get_page_comments(page_id, limit)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )
        ]

    async def search_content(query: str, space_key: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Search for content in Confluence."""
        try:
            logger.info(f"Searching Confluence for: {query}, space_key: {space_key}, limit: {limit}")
            
            search_params = {
                "cql": f"text ~ \"{query}\""
            }
            
            if space_key:
                search_params["cql"] += f" AND space = \"{space_key}\""
            
            search_params["limit"] = limit
            
            results = await fetcher.search_content(**search_params)
            
            # Format and return results
            formatted_results = []
            for item in results.get("results", []):
                formatted_results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "type": item.get("type"),
                    "space": item.get("space", {}).get("key", "") if item.get("space") else "",
                    "url": item.get("_links", {}).get("webui", "") if item.get("_links") else ""
                })
            
            return {
                "query": query,
                "total": results.get("totalSize", 0),
                "results": formatted_results
            }
        except Exception as e:
            logger.exception(f"Error searching Confluence: {e}")
            return {"error": str(e)}

    async def get_page_content(page_id: str, expand: str = "body.storage,version") -> Dict[str, Any]:
        """Get a Confluence page by ID."""
        try:
            logger.info(f"Getting Confluence page: {page_id}, expand: {expand}")
            page = await fetcher.get_page(page_id=page_id, expand=expand)
            
            # Format and return page content
            result = {
                "id": page.get("id"),
                "title": page.get("title"),
                "type": page.get("type"),
                "version": page.get("version", {}).get("number", 0) if page.get("version") else 0,
                "space": page.get("space", {}).get("key", "") if page.get("space") else "",
                "url": page.get("_links", {}).get("webui", "") if page.get("_links") else "",
                "body": page.get("body", {}).get("storage", {}).get("value", "") if page.get("body") and page.get("body").get("storage") else ""
            }
            
            return result
        except Exception as e:
            logger.exception(f"Error getting Confluence page: {e}")
            return {"error": str(e)}

    async def get_spaces(limit: int = 10, space_type: Optional[str] = None) -> Dict[str, Any]:
        """Get a list of Confluence spaces."""
        try:
            logger.info(f"Getting Confluence spaces, limit: {limit}, type: {space_type}")
            
            params = {"limit": limit}
            if space_type:
                params["type"] = space_type
            
            spaces_result = await fetcher.get_spaces(**params)
            
            # Format and return spaces
            formatted_spaces = []
            for space in spaces_result.get("results", []):
                formatted_spaces.append({
                    "id": space.get("id"),
                    "key": space.get("key"),
                    "name": space.get("name"),
                    "type": space.get("type"),
                    "url": space.get("_links", {}).get("webui", "") if space.get("_links") else ""
                })
            
            return {
                "total": spaces_result.get("size", 0),
                "spaces": formatted_spaces
            }
        except Exception as e:
            logger.exception(f"Error getting Confluence spaces: {e}")
            return {"error": str(e)}

    async def get_page_children(page_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get children of a Confluence page."""
        try:
            logger.info(f"Getting children of Confluence page: {page_id}, limit: {limit}")
            
            children = await fetcher.get_page_children(page_id=page_id, limit=limit)
            
            # Format and return children
            formatted_children = []
            for child in children.get("results", []):
                formatted_children.append({
                    "id": child.get("id"),
                    "title": child.get("title"),
                    "type": child.get("type"),
                    "url": child.get("_links", {}).get("webui", "") if child.get("_links") else ""
                })
            
            return {
                "parent_id": page_id,
                "total": children.get("size", 0),
                "children": formatted_children
            }
        except Exception as e:
            logger.exception(f"Error getting page children: {e}")
            return {"error": str(e)}

    async def get_page_comments(page_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get comments on a Confluence page."""
        try:
            logger.info(f"Getting comments for Confluence page: {page_id}, limit: {limit}")
            
            comments = await fetcher.get_page_comments(content_id=page_id, limit=limit)
            
            # Format and return comments
            formatted_comments = []
            for comment in comments.get("results", []):
                formatted_comments.append({
                    "id": comment.get("id"),
                    "title": comment.get("title"),
                    "created": comment.get("created"),
                    "author": comment.get("author", {}).get("displayName", "") if comment.get("author") else "",
                    "body": comment.get("body", {}).get("storage", {}).get("value", "") if comment.get("body") and comment.get("body").get("storage") else ""
                })
            
            return {
                "page_id": page_id,
                "total": comments.get("size", 0),
                "comments": formatted_comments
            }
        except Exception as e:
            logger.exception(f"Error getting page comments: {e}")
            return {"error": str(e)}

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
        event_store=None,  # Stateless mode - can be changed to use an event store
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
            logger.info("Application started with dual transports!")
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
