import contextlib
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
brave_search,
brave_video_search,
brave_news_search,
brave_image_search
)



# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

BRAVE_SEARCH_MCP_SERVER_PORT = int(os.getenv("BRAVE_SEARCH_MCP_SERVER_PORT", "5000"))

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
                name="brave_search",
                description="""
        Perform a Brave search query with many optional filters and personalization headers.

        This tool queries Brave's Web Search API, which supports advanced parameters like freshness filtering, safesearch, spellcheck, text decorations, custom re-ranking (Goggles), and more.

        It also supports sending user location headers to personalize results.

        Typical use: finding live web results, news, videos, or mixed content based on the query.
        """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": """
        [Required] The search query to run.  
        Max 400 characters and 50 words. Supports standard search operators.
        """
                        },
                        "count": {
                            "type": "integer",
                            "description": """
        Number of web results to return (max 20, default 5).  
        Controls how many top results to include.
        """
                        },
                        "country": {
                            "type": "string",
                            "description": """
        2-letter country code to localize results (e.g., 'US', 'GB', 'IN').  
        See Brave supported country codes.
        """
                        },
                        "search_lang": {
                            "type": "string",
                            "description": """
        Language code for search results (e.g., 'en', 'fr').  
        Affects which language Brave prefers in results.
        """
                        },
                        "ui_lang": {
                            "type": "string",
                            "description": """
        UI language in format like 'en-US', 'fr-FR'.  
        Changes language for certain UI text in response.
        """
                        },
                        "offset": {
                            "type": "integer",
                            "description": """
        Zero-based offset for pagination (max 9).  
        Use with count to get next pages (e.g., offset=5, count=5 → get results 6–10).
        """
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": """
        Filter adult content.  
        - 'off': show everything  
        - 'moderate': hide explicit images/videos  
        - 'strict': hide most adult content
        """
                        },
                        "spellcheck": {
                            "type": "string",
                            "description": """
        Whether to enable spellcheck on query.  
        Usually 'true' or 'false'.
        """
                        },
                        "freshness": {
                            "type": "string",
                            "description": """
        Filter by discovery time:  
        - 'pd': last 24 hours  
        - 'pw': last 7 days  
        - 'pm': last 31 days  
        - 'py': last year  
        - Or custom range 'YYYY-MM-DDtoYYYY-MM-DD'
        """
                        },
                        "text_decorations": {
                            "type": "string",
                            "description": """
        Whether to include HTML-like highlight markers in snippets.  
        Usually 'true' or 'false'.
        """
                        },
                        "result_filter": {
                            "type": "string",
                            "description": """
        Comma-separated list of result sections to include.  
        Options: discussions, faq, infobox, news, query, summarizer, videos, web, locations.
        """
                        },
                        "units": {
                            "type": "string",
                            "enum": ["metric", "imperial"],
                            "description": """
        Measurement units system (metric or imperial).  
        Defaults based on country if not set.
        """
                        },
                        "goggles": {
                            "type": "string",
                            "description": """
        ID or URL of a Goggle definition to re-rank results.  
        Goggles let you change ranking logic.
        """
                        },
                        "extra_snippets": {
                            "type": "string",
                            "description": """
        Whether to return extra alternative text snippets per result.  
        Usually 'true' or 'false'.
        """
                        },
                        "summary": {
                            "type": "string",
                            "description": """
        Whether to include automatic summaries in web search results.  
        Usually 'true' or 'false'.
        """
                        },
                        "enable_rich_callback": {
                            "type": "string",
                            "description": """
        Undocumented advanced parameter. Rarely used.
        """
                        },
                        "x_loc_lat": {
                            "type": "number",
                            "description": "User latitude (e.g., 37.7749). Helps personalize results."
                        },
                        "x_loc_long": {
                            "type": "number",
                            "description": "User longitude (e.g., -122.4194). Helps personalize results."
                        },
                        "x_loc_timezone": {
                            "type": "string",
                            "description": "Timezone string like 'America/Los_Angeles'."
                        },
                        "x_loc_city": {
                            "type": "string",
                            "description": "City name (e.g., 'San Francisco')."
                        },
                        "x_loc_state": {
                            "type": "string",
                            "description": "State code (e.g., 'CA')."
                        },
                        "x_loc_state_name": {
                            "type": "string",
                            "description": "State full name (e.g., 'California')."
                        },
                        "x_loc_country": {
                            "type": "string",
                            "description": "Country code (e.g., 'US')."
                        },
                        "x_loc_postal_code": {
                            "type": "string",
                            "description": "Postal code (e.g., '94103')."
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="brave_image_search",
                description="""
        Perform an image search using Brave's Image Search API.

        Supports filters like safesearch, language, spellcheck, and country-based localization.
        Returns a list of images matching the query, optionally spellchecked.
        Useful when you want to get fresh images from the web.
        """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": """
        [Required] The search term to find images for.  
        Max 400 characters and 50 words. Cannot be empty.
        """
                        },
                        "count": {
                            "type": "integer",
                            "description": """
        Number of images to return (default: 5, max: 200).  
        Controls how many top images to include.
        """
                        },
                        "search_lang": {
                            "type": "string",
                            "description": """
        Language code (like 'en', 'fr') to prefer in results.  
        Helps surface content in a preferred language.
        """
                        },
                        "country": {
                            "type": "string",
                            "description": """
        2-letter country code to localize results (e.g., 'US', 'GB', 'IN').  
        See Brave supported country codes.
        """
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "strict"],
                            "description": """
        Filter adult content in images:  
        - 'off': no filtering  
        - 'strict': remove adult content (default behavior)
        """
                        },
                        "spellcheck": {
                            "type": "string",
                            "description": """
        Whether to auto-correct misspellings in the query.  
        Usually 'true' or 'false'.  
        If enabled and the query is changed, the new query appears in the 'altered' field of the response.
        """
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="brave_news_search",
                description="""
        Perform a news search using Brave's News Search API.

        Returns fresh, localized news results with support for safesearch, language filters,
        pagination, freshness filters, spellcheck, and Goggles for custom re-ranking.
        """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": """
        [Required] Search term to find news articles for.
        Cannot be empty; max 400 characters and 50 words.
        """
                        },
                        "count": {
                            "type": "integer",
                            "description": """
        Number of news results to return (default: 5, max: 50).
        Use with offset for pagination.
        """
                        },
                        "search_lang": {
                            "type": "string",
                            "description": """
        Language code (e.g., 'en', 'fr') to prefer in news content.
        """
                        },
                        "ui_lang": {
                            "type": "string",
                            "description": """
        User interface language in <language>-<country> format (e.g., 'en-US').
        Controls UI text and subtle ranking changes.
        """
                        },
                        "country": {
                            "type": "string",
                            "description": """
        2-letter country code (e.g., 'US', 'GB', 'IN') to localize results.
        """
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": """
        Filter adult or suggestive content in news:
        - 'off': no filtering
        - 'moderate': filter explicit content (default)
        - 'strict': filter explicit + suggestive content
        """
                        },
                        "offset": {
                            "type": "integer",
                            "description": """
        Zero-based offset for pagination (max 9). Use with count to get next pages.
        Example: count=20 & offset=1 fetches the second page of 20 results.
        """
                        },
                        "spellcheck": {
                            "type": "string",
                            "description": """
        Whether to auto-correct spelling in the query (usually 'true' or 'false').
        If changed, corrected query appears in 'altered' field of response.
        """
                        },
                        "freshness": {
                            "type": "string",
                            "description": """
        Limit results to recent news:
        - 'pd': Last 24 hours
        - 'pw': Last 7 days
        - 'pm': Last 31 days
        - 'py': Last year
        - Or custom: 'YYYY-MM-DDtoYYYY-MM-DD'
        """
                        },
                        "extra_snippets": {
                            "type": "string",
                            "description": """
        Include up to 5 extra alternative excerpts (requires specific API plans).
        """
                        },
                        "goggles": {
                            "type": "string",
                            "description": """
        Goggles ID, URL, or definition to custom re-rank news results.
        Can be repeated for multiple Goggles.
        """
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="brave_video_search",
                description="""
        Perform a Brave video search and get video results matching a query.

        Supports safesearch filtering, language and country localization, pagination,
        spellcheck, and freshness filters to narrow results to recent videos.
        """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": """
        [Required] Search term for videos. Cannot be empty.
        Max 400 characters and 50 words.
        """
                        },
                        "count": {
                            "type": "integer",
                            "description": """
        Number of video results to return (default: 5, max: 50).
        Use with offset for pagination.
        """
                        },
                        "safesearch": {
                            "type": "string",
                            "enum": ["off", "moderate", "strict"],
                            "description": """
        Adult content filter:
        - 'off': No filtering (default)
        - 'moderate': Filter explicit content
        - 'strict': Filter explicit and suggestive content
        """
                        },
                        "search_lang": {
                            "type": "string",
                            "description": """
        Language code (e.g., 'en', 'fr') to prefer in video content.
        """
                        },
                        "ui_lang": {
                            "type": "string",
                            "description": """
        User interface language in format <language>-<country> (e.g., 'en-US').
        Affects UI text and subtle ranking changes.
        """
                        },
                        "country": {
                            "type": "string",
                            "description": """
        2-letter country code (e.g., 'US', 'GB', 'IN') to localize results.
        """
                        },
                        "offset": {
                            "type": "integer",
                            "description": """
        Zero-based offset for pagination (max 9). Use with count to fetch next pages.
        Example: count=20 & offset=1 fetches second page of 20 results.
        """
                        },
                        "spellcheck": {
                            "type": "string",
                            "description": """
        Whether to enable spellcheck on the query ('true' or 'false').
        If enabled and the query is corrected, the corrected query appears in the 'altered' field.
        """
                        },
                        "freshness": {
                            "type": "string",
                            "description": """
        Filter by video discovery date:
        - 'pd': Last 24 hours
        - 'pw': Last 7 days
        - 'pm': Last 31 days
        - 'py': Last 365 days
        - Or custom: 'YYYY-MM-DDtoYYYY-MM-DD'
        """
                        }
                    },
                    "required": ["query"]
                }
            )

        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "brave_search":
            try:
                result = brave_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    country=arguments.get("country"),
                    search_lang=arguments.get("search_lang"),
                    ui_lang=arguments.get("ui_lang"),
                    offset=arguments.get("offset"),
                    safesearch=arguments.get("safesearch"),
                    spellcheck=arguments.get("spellcheck"),
                    freshness=arguments.get("freshness"),
                    text_decorations=arguments.get("text_decorations"),
                    result_filter=arguments.get("result_filter"),
                    units=arguments.get("units"),
                    goggles=arguments.get("goggles"),
                    extra_snippets=arguments.get("extra_snippets"),
                    summary=arguments.get("summary"),
                    enable_rich_callback=arguments.get("enable_rich_callback"),
                    x_loc_lat=arguments.get("x_loc_lat"),
                    x_loc_long=arguments.get("x_loc_long"),
                    x_loc_timezone=arguments.get("x_loc_timezone"),
                    x_loc_city=arguments.get("x_loc_city"),
                    x_loc_state=arguments.get("x_loc_state"),
                    x_loc_state_name=arguments.get("x_loc_state_name"),
                    x_loc_country=arguments.get("x_loc_country"),
                    x_loc_postal_code=arguments.get("x_loc_postal_code")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_image_search":
            try:
                result = brave_image_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    search_lang=arguments.get("search_lang"),
                    country=arguments.get("country"),
                    safesearch=arguments.get("safesearch"),
                    spellcheck=arguments.get("spellcheck")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_image_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_news_search":
            try:
                result = brave_news_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    search_lang=arguments.get("search_lang"),
                    ui_lang=arguments.get("ui_lang"),
                    country=arguments.get("country"),
                    safesearch=arguments.get("safesearch"),
                    offset=arguments.get("offset"),
                    spellcheck=arguments.get("spellcheck"),
                    freshness=arguments.get("freshness"),
                    extra_snippets=arguments.get("extra_snippets"),
                    goggles=arguments.get("goggles")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in brave_news_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "brave_video_search":
            try:
                result = brave_video_search(
                    query=arguments["query"],
                    count=arguments.get("count"),
                    safesearch=arguments.get("safesearch"),
                    search_lang=arguments.get("search_lang"),
                    ui_lang=arguments.get("ui_lang"),
                    country=arguments.get("country"),
                    offset=arguments.get("offset"),
                    spellcheck=arguments.get("spellcheck"),
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

        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = request.headers.get('x-auth-token')

        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(auth_token or "")
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

        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')

        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
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
