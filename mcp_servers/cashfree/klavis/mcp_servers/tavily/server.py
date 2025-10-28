import os
import json
import logging
import contextlib
import base64
from collections.abc import AsyncIterator
from typing import Any, Dict

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    tavily_api_key_context,
    tavily_search,
    tavily_extract,
    tavily_crawl,
    tavily_map,
)

# Load env early
load_dotenv()

logger = logging.getLogger("tavily-mcp-server")
logging.basicConfig(level=logging.INFO)

TAVILY_MCP_SERVER_PORT = int(os.getenv("TAVILY_MCP_SERVER_PORT", "5000"))

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    auth_data = None
    
    if not api_key:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            header_value = request_or_scope.headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            header_value = headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')
        
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
@click.option("--port", default=TAVILY_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=True, help="Enable JSON responses for StreamableHTTP")
def main(port: int, log_level: str, json_response: bool) -> int:
    """Tavily MCP server with SSE + StreamableHTTP transports (LinkedIn-style)."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    app = Server("tavily-mcp-server")

    # ----------------------------- Tool Registry -----------------------------#
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="tavily_search",
                description=(
                    "Web Search (Tavily) — search the web with filters like topic/news, "
                    "date range, domains, and optional images/raw content.\n"
                    "Prompt hints: 'search web for', 'find recent articles about', 'get latest news on'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Search query text."},
                        "search_depth": {
                            "type": "string",
                            "enum": ["basic", "advanced"],
                            "description": "Depth of search. 'basic' is faster; 'advanced' is deeper.",
                            "default": "basic",
                        },
                        "topic": {
                            "type": "string",
                            "enum": ["general", "news"],
                            "description": "Bias results to a topic area.",
                            "default": "general",
                        },
                        "days": {"type": "integer", "description": "Look-back window in days for freshness.", "default": 3},
                        "time_range": {
                            "type": "string",
                            "enum": ["day", "week", "month", "year"],
                            "description": "Relative time window.",
                        },
                        "start_date": {"type": "string", "description": "Filter results after YYYY-MM-DD."},
                        "end_date": {"type": "string", "description": "Filter results before YYYY-MM-DD."},
                        "max_results": {
                            "type": "integer",
                            "minimum": 5,
                            "maximum": 20,
                            "description": "Number of results to return (5–20).",
                            "default": 10,
                        },
                        "include_images": {"type": "boolean", "description": "Include relevant images.", "default": False},
                        "include_image_descriptions": {
                            "type": "boolean",
                            "description": "Include descriptions for images.",
                            "default": False,
                        },
                        "include_raw_content": {
                            "type": "boolean",
                            "description": "Include cleaned raw page content.",
                            "default": False,
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Only include results from these domains.",
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exclude results from these domains.",
                        },
                        "country": {"type": "string", "description": "Country code to bias results (e.g., 'us')."},
                        "include_favicon": {"type": "boolean", "description": "Include site favicon URLs.", "default": False},
                        # Accept common aliases too (LLM-friendly)
                        "searchDepth": {"type": "string", "enum": ["basic", "advanced"]},
                        "timeRange": {"type": "string", "enum": ["day", "week", "month", "year"]},
                        "startDate": {"type": "string"},
                        "endDate": {"type": "string"},
                        "maxResults": {"type": "integer", "minimum": 5, "maximum": 20},
                        "includeImages": {"type": "boolean"},
                        "includeImageDescriptions": {"type": "boolean"},
                        "includeRawContent": {"type": "boolean"},
                        "includeDomains": {"type": "array", "items": {"type": "string"}},
                        "excludeDomains": {"type": "array", "items": {"type": "string"}},
                        "includeFavicon": {"type": "boolean"},
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "TAVILY_WEB_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="tavily_extract",
                description=(
                    "Extract Web Content — fetch and parse content from one or more URLs. "
                    "Supports 'basic'/'advanced' depth, markdown/text output, images, and favicons.\n"
                    "Prompt hints: 'extract content', 'scrape web page', 'fetch page summary'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["urls"],
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}, "description": "List of absolute URLs."},
                        "extract_depth": {
                            "type": "string",
                            "enum": ["basic", "advanced"],
                            "description": "Richer parsing with 'advanced'.",
                            "default": "basic",
                        },
                        "include_images": {"type": "boolean", "default": False},
                        "format": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
                        "include_favicon": {"type": "boolean", "default": False},
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "TAVILY_WEB_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="tavily_crawl",
                description=(
                    "Crawl Website — start from a root URL and follow links with depth/breadth controls. "
                    "Returns page content and metadata. Use for small, bounded explorations.\n"
                    "Prompt hints: 'crawl site', 'explore site structure', 'get all pages under'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string", "description": "Root absolute URL to crawl."},
                        "max_depth": {"type": "integer", "minimum": 1, "default": 1},
                        "max_breadth": {"type": "integer", "minimum": 1, "default": 20},
                        "limit": {"type": "integer", "minimum": 1, "default": 50},
                        "instructions": {"type": "string"},
                        "select_paths": {"type": "array", "items": {"type": "string"}},
                        "select_domains": {"type": "array", "items": {"type": "string"}},
                        "allow_external": {"type": "boolean", "default": False},
                        "categories": {"type": "array", "items": {"type": "string"}},
                        "extract_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "basic"},
                        "format": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
                        "include_favicon": {"type": "boolean", "default": False},
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "TAVILY_WEB_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="tavily_map",
                description=(
                    "Generate Website Map — discover reachable URLs from a root without extracting heavy content. "
                    "Great for structure lists.\n"
                    "Prompt hints: 'map website', 'list all pages on', 'show site structure for'"
                ),
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {"type": "string", "description": "Root absolute URL to map."},
                        "max_depth": {"type": "integer", "minimum": 1, "default": 1},
                        "max_breadth": {"type": "integer", "minimum": 1, "default": 20},
                        "limit": {"type": "integer", "minimum": 1, "default": 50},
                        "instructions": {"type": "string"},
                        "select_paths": {"type": "array", "items": {"type": "string"}},
                        "select_domains": {"type": "array", "items": {"type": "string"}},
                        "allow_external": {"type": "boolean", "default": False},
                        "categories": {"type": "array", "items": {"type": "string"}},
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "TAVILY_WEB_SEARCH", "readOnlyHint": True}
                ),
            ),
        ]

    # ---------------------------- Tool Dispatcher ----------------------------#
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        logger.info(f"call_tool: {name}")
        logger.debug(f"raw arguments: {json.dumps(arguments, indent=2)}")

        try:
            if name == "tavily_search":
                result = tavily_search(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "tavily_extract":
                result = tavily_extract(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "tavily_crawl":
                result = tavily_crawl(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            if name == "tavily_map":
                result = tavily_map(arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # ------------------------------- Transports ------------------------------#
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """
        SSE transport endpoint.
        If header 'x-auth-token' is present, bind it for the request via ContextVar.
        """
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        token = None
        if api_key:
            token = tavily_api_key_context.set(api_key)

        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            if token:
                tavily_api_key_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """
        Streamable HTTP transport endpoint.
        Accepts 'x-auth-token' header for per-request auth.
        """
        logger.info("Handling StreamableHTTP request")
        
        # Extract API key from headers
        api_key = extract_api_key(scope)

        token = None
        if api_key:
            token = tavily_api_key_context.set(api_key)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            if token:
                tavily_api_key_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
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
