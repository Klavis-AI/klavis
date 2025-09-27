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
    google_news_search,
    google_news_trending,
    google_news_headlines,
    google_news_by_source,
    google_news_date_range,
    google_news_topics_list,
    google_news_sources_list
)

logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_NEWS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_NEWS_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=GOOGLE_NEWS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    # Initialize and start the Google News MCP server with configurable transport options
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("google-news-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        # Return the available MCP tools for Google News search and trending articles
        return [
            types.Tool(
                name="google_news_search",
                description="""
                Search Google News for articles using SerpApi.
                
                Supports searching by query, topic, publication, or story tokens.
                Results can be localized by country and language.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for news articles"
                        },
                        "country": {
                            "type": "string",
                            "description": "Two-letter country code (e.g., 'us', 'uk', 'ca'). Default: 'us'"
                        },
                        "language": {
                            "type": "string", 
                            "description": "Two-letter language code (e.g., 'en', 'es', 'fr'). Default: 'en'"
                        },
                        "topic_token": {
                            "type": "string",
                            "description": "Token for specific news topic (alternative to query)"
                        },
                        "publication_token": {
                            "type": "string",
                            "description": "Token for specific publisher (alternative to query)"
                        },
                        "story_token": {
                            "type": "string",
                            "description": "Token for full coverage of specific story (alternative to query)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="google_news_trending",
                description="""
                Get trending Google News articles.
                
                Returns the most popular news articles for the specified country and language.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "description": "Two-letter country code (e.g., 'us', 'uk', 'ca'). Default: 'us'"
                        },
                        "language": {
                            "type": "string",
                            "description": "Two-letter language code (e.g., 'en', 'es', 'fr'). Default: 'en'"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="google_news_headlines",
                description="""
                Get Google News headlines by category.
                
                Retrieve news headlines filtered by specific categories like business, technology, sports, etc.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "News category (business, technology, sports, health, entertainment, science, world, politics)"
                        },
                        "country": {
                            "type": "string",
                            "description": "Two-letter country code (e.g., 'us', 'uk', 'ca'). Default: 'us'"
                        },
                        "language": {
                            "type": "string",
                            "description": "Two-letter language code (e.g., 'en', 'es', 'fr'). Default: 'en'"
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort method: 'relevance' or 'date'. Default: 'relevance'"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="google_news_by_source",
                description="""
                Get Google News articles from a specific source.
                
                Retrieve news articles from a particular news outlet or publisher.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "News source name (e.g., 'CNN', 'BBC', 'Reuters')"
                        },
                        "country": {
                            "type": "string",
                            "description": "Two-letter country code (e.g., 'us', 'uk', 'ca'). Default: 'us'"
                        },
                        "language": {
                            "type": "string",
                            "description": "Two-letter language code (e.g., 'en', 'es', 'fr'). Default: 'en'"
                        }
                    },
                    "required": ["source"]
                }
            ),
            types.Tool(
                name="google_news_date_range",
                description="""
                Search Google News with date range filtering.
                
                Search for news articles within a specific date range using date operators.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for news articles"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (e.g., '2023-01-01')"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
                        },
                        "country": {
                            "type": "string",
                            "description": "Two-letter country code (e.g., 'us', 'uk', 'ca'). Default: 'us'"
                        },
                        "language": {
                            "type": "string",
                            "description": "Two-letter language code (e.g., 'en', 'es', 'fr'). Default: 'en'"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="google_news_topics_list",
                description="""
                Get available Google News topics/categories.
                
                Returns a list of available news topics and categories that can be used with other tools.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="google_news_sources_list",
                description="""
                Get popular Google News sources.
                
                Returns a list of popular news sources and publishers that can be used with the by_source tool.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str,
        arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Handle tool execution requests by routing to appropriate Google News functions
        if name == "google_news_search":
            try:
                result = await google_news_search(
                    query=arguments.get("query"),
                    country=arguments.get("country", "us"),
                    language=arguments.get("language", "en"),
                    topic_token=arguments.get("topic_token"),
                    publication_token=arguments.get("publication_token"),
                    story_token=arguments.get("story_token")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_trending":
            try:
                result = await google_news_trending(
                    country=arguments.get("country", "us"),
                    language=arguments.get("language", "en")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_trending: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_headlines":
            try:
                result = await google_news_headlines(
                    category=arguments.get("category"),
                    country=arguments.get("country", "us"),
                    language=arguments.get("language", "en"),
                    sort_by=arguments.get("sort_by", "relevance")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_headlines: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_by_source":
            try:
                result = await google_news_by_source(
                    source=arguments.get("source"),
                    country=arguments.get("country", "us"),
                    language=arguments.get("language", "en")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_by_source: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_date_range":
            try:
                result = await google_news_date_range(
                    query=arguments.get("query"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    country=arguments.get("country", "us"),
                    language=arguments.get("language", "en")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_date_range: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_topics_list":
            try:
                result = await google_news_topics_list()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_topics_list: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "google_news_sources_list":
            try:
                result = await google_news_sources_list()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in google_news_sources_list: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        # Handle Server-Sent Events connections with authentication token management
        logger.info("Handling SSE connection")
        
        auth_token = request.headers.get('x-auth-token')
        
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

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        # Handle HTTP streaming requests with authentication token extraction and context management
        logger.info("Handling StreamableHTTP request")
        
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')

        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        # Manage the application lifecycle with proper startup and shutdown handling
        async with session_manager.run():
            logger.info("Google News MCP Server started with dual transports!")
            try:
                yield
            finally:
                logger.info("Google News MCP Server shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Google News MCP Server starting on port {port}")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")
    logger.info(f"  - Required env var: SERPAPI_API_KEY")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()