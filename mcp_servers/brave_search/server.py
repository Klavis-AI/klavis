import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import List

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

from tools import (
auth_token_context,
brave_web_search,
brave_video_search,
brave_news_search,
brave_image_search
)



# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

BRAVE_SEARCH_MCP_SERVER_PORT = int(os.getenv("BRAVE_SEARCH_MCP_SERVER_PORT", "5000"))

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""


@click.command()
@click.option("--port", default=BRAVE_SEARCH_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("brave-search-mcp-server")
#-------------------------------------------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="brave_web_search",
                description="""
                Perform a Brave web search.

                Typical use: get live web results by query, with optional pagination, country, language, and safesearch filters.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Required. The search query. Max 400 chars & 50 words."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of results to return (max 20, default 5)."
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Zero-based offset for pagination."
                        },
                        "country": {
                            "type": "string",
                            "description": "2-letter country code to localize results, e.g., 'US'."
                        },
                        "search_lang": {
                            "type": "string",
                            "description": "Language code for search results, e.g., 'en'."
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": "Filter adult content."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "BRAVE_SEARCH", "readOnlyHint": True}
                ),
            ),

            types.Tool(
                name="brave_image_search",
                description="""
                Perform a Brave image search by query.

                Supports safesearch filtering, language and country localization, and pagination.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "[Required] Search term for images. Max 400 chars & 50 words."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of image results to return (default: 5, max: 200)."
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Zero-based offset for pagination."
                        },
                        "search_lang": {
                            "type": "string",
                            "description": "Language code for image results, e.g., 'en'."
                        },
                        "country": {
                            "type": "string",
                            "description": "2-letter country code to localize results, e.g., 'US'."
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "strict"],
                            "description": "Adult content filter: 'off' or 'strict'."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "BRAVE_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="brave_news_search",
                description="""
                Perform a Brave news search by query.

                Supports safesearch filtering, language and country localization, pagination, and freshness filter to get recent news.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "[Required] Search term for news articles. Max 400 chars & 50 words."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of news results to return (default: 5, max: 50)."
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Zero-based offset for pagination."
                        },
                        "country": {
                            "type": "string",
                            "description": "2-letter country code to localize results, e.g., 'US'."
                        },
                        "search_lang": {
                            "type": "string",
                            "description": "Language code for news results, e.g., 'en'."
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": "Adult content filter: 'off', 'moderate', or 'strict'."
                        },
                        "freshness": {
                            "type": "string",
                            "description": "Filter by recency: 'pd' (24h), 'pw' (7d), 'pm' (31d), 'py' (year), or custom 'YYYY-MM-DDtoYYYY-MM-DD'."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "BRAVE_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="brave_video_search",
                description="""
                Perform a Brave video search by query.
                Supports safesearch filtering, language and country localization, pagination, and freshness filter to get recent videos.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "[Required] Search term for videos. Max 400 chars & 50 words."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of video results to return (default: 5, max: 50)."
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Zero-based offset for pagination."
                        },
                        "country": {
                            "type": "string",
                            "description": "2-letter country code to localize results, e.g., 'US'."
                        },
                        "search_lang": {
                            "type": "string",
                            "description": "Language code for video results, e.g., 'en'."
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": "Adult content filter: 'off', 'moderate', or 'strict'."
                        },
                        "freshness": {
                            "type": "string",
                            "description": "Filter by discovery date: 'pd' (24h), 'pw' (7d), 'pm' (31d), 'py' (year), or custom 'YYYY-MM-DDtoYYYY-MM-DD'."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "BRAVE_SEARCH", "readOnlyHint": True}
                ),
            )

        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "brave_web_search":
            try:
                result = await brave_web_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    offset=arguments.get("offset"),
                    country=arguments.get("country"),
                    search_lang=arguments.get("search_lang"),
                    safesearch=arguments.get("safesearch")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_image_search":
            try:
                result = await brave_image_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    offset=arguments.get("offset"),
                    search_lang=arguments.get("search_lang"),
                    country=arguments.get("country"),
                    safesearch=arguments.get("safesearch")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_image_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_news_search":
            try:
                result = await brave_news_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    offset=arguments.get("offset"),
                    country=arguments.get("country"),
                    search_lang=arguments.get("search_lang"),
                    safesearch=arguments.get("safesearch"),
                    freshness=arguments.get("freshness")
                )

                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_news_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_video_search":
            try:
                result = await brave_video_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    offset=arguments.get("offset"),
                    country=arguments.get("country"),
                    search_lang=arguments.get("search_lang"),
                    safesearch=arguments.get("safesearch"),
                    freshness=arguments.get("freshness")
                )

                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_video_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    #-------------------------------------------------------------------------

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        # Set the API key in context for this request
        token = auth_token_context.set(api_key)
        try:
            async with sse.connect_sse(
                    request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)

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
        
        # Extract API key from headers
        api_key = extract_api_key(scope)
        
        # Set the API key in context for this request
        token = auth_token_context.set(api_key)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

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
