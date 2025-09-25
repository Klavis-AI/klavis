import contextlib
import json
import logging
import os
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
    find_relevant_subreddits as find_subreddits_impl,
    search_subreddit_posts as search_posts_impl,
    get_post_and_top_comments as get_comments_impl,
    find_similar_posts_reddit as find_similar_impl,
    create_post as create_post_impl,
)

from tools.base import init_http_clients, close_http_clients

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

REDDIT_MCP_SERVER_PORT = int(os.getenv("REDDIT_MCP_SERVER_PORT", "5001"))

@click.command()
@click.option("--port", default=REDDIT_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("reddit-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="reddit_find_subreddits",
                description="Find relevant subreddits based on a query. Use this first to discover communities when a user does not specify one.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant subreddits"
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="reddit_search_posts",
                description="Search for posts in a specific subreddit matching a query.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "Name of the subreddit to search in (without r/ prefix)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant posts"
                        }
                    },
                    "required": ["subreddit", "query"]
                }
            ),
            types.Tool(
                name="reddit_get_post_comments",
                description="Get the top comments for a specific Reddit post.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Reddit post ID (without t3_ prefix)"
                        },
                        "subreddit": {
                            "type": "string",
                            "description": "Name of the subreddit containing the post"
                        }
                    },
                    "required": ["post_id", "subreddit"]
                }
            ),
            types.Tool(
                name="reddit_find_similar_posts",
                description="Find posts similar to a given Reddit post using semantic matching.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Reddit post ID to find similar posts for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of similar posts to return (default: 10, max: 50)",
                            "default": 10
                        }
                    },
                    "required": ["post_id"]
                }
            ),
            types.Tool(
                name="reddit_create_post",
                description="Create a new post in a subreddit.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "Name of the subreddit to create the post in (without r/ prefix)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the post"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text of the post"
                        }
                    },
                    "required": ["subreddit", "title", "text"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "reddit_find_subreddits":
            try:
                logger.info("Tool call: reddit_find_subreddits(query=%r)", arguments["query"])
                result = await find_subreddits_impl(arguments["query"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing reddit_find_subreddits: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "reddit_search_posts":
            try:
                logger.info(
                    "Tool call: reddit_search_posts(subreddit=%r, query=%r)",
                    arguments["subreddit"],
                    arguments["query"],
                )
                result = await search_posts_impl(arguments["subreddit"], arguments["query"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing reddit_search_posts: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "reddit_get_post_comments":
            try:
                logger.info(
                    "Tool call: reddit_get_post_comments(post_id=%r, subreddit=%r)",
                    arguments["post_id"],
                    arguments["subreddit"],
                )
                result = await get_comments_impl(arguments["post_id"], arguments["subreddit"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing reddit_get_post_comments: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "reddit_find_similar_posts":
            try:
                post_id = arguments["post_id"]
                limit = arguments.get("limit", 10)
                logger.info(
                    "Tool call: reddit_find_similar_posts(post_id=%r, limit=%r)",
                    post_id,
                    limit,
                )
                # Ensure limit is within bounds
                limit = max(1, min(50, limit))
                result = await find_similar_impl(post_id, limit)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing reddit_find_similar_posts: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "reddit_create_post":
            try:
                result = await create_post_impl(arguments["subreddit"], arguments["title"], arguments["text"])
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error executing reddit_create_post: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")
    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
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
        """Context manager for session manager and HTTP clients."""
        await init_http_clients()
        async with session_manager.run():
            logger.info("Reddit MCP Server started with dual transports!")
            try:
                yield
            finally:
                logger.info("Reddit MCP Server shutting down...")
                await close_http_clients()

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
