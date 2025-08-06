#!/usr/bin/env python3
"""
Reddit MCP Server for Klavis AI
Provides atomic tools for interacting with Reddit API with dual transport support.
"""

import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

import click
import mcp.types as types
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools.base import auth_token_context
from tools.posts import PostsTools
from tools.subreddits import SubredditsTools
from tools.users import UsersTools
from tools.search import SearchTools

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

REDDIT_MCP_SERVER_PORT = int(os.getenv("REDDIT_MCP_SERVER_PORT", "5000"))


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

    app = Server("reddit-mcp-server")

    # Initialize tool modules
    posts_tools = PostsTools()
    subreddits_tools = SubredditsTools()
    users_tools = UsersTools()
    search_tools = SearchTools()

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        logger.info("📋 Listing available Reddit MCP tools...")
        return [
            types.Tool(
                name="search_reddit_posts",
                description="Search for posts across Reddit using keywords or phrases. Returns relevant posts with titles, authors, scores, and URLs.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'Python programming', 'machine learning')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of posts to return (default: 10, max: 25)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 25
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="get_subreddit_posts",
                description="Get the latest posts from a specific subreddit. Returns posts with titles, authors, scores, and engagement metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subreddit": {
                            "type": "string",
                            "description": "Subreddit name without 'r/' prefix (e.g., 'programming', 'python')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of posts to return (default: 10, max: 25)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 25
                        }
                    },
                    "required": ["subreddit"]
                }
            ),
            types.Tool(
                name="get_trending_subreddits",
                description="Get currently trending subreddits. Returns popular subreddits with subscriber counts and descriptions.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of trending subreddits to return (default: 10, max: 25)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 25
                        }
                    }
                }
            ),
            types.Tool(
                name="get_post_details",
                description="Get detailed information about a specific Reddit post including full text, author, score, and engagement metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Reddit post ID (found in post URL)"
                        }
                    },
                    "required": ["post_id"]
                }
            ),
            types.Tool(
                name="get_post_comments",
                description="Get comments for a specific Reddit post. Returns comment threads with authors, scores, and text content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "post_id": {
                            "type": "string",
                            "description": "Reddit post ID (found in post URL)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of comments to return (default: 10, max: 50)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["post_id"]
                }
            ),
            types.Tool(
                name="get_user_profile",
                description="Get information about a Reddit user including karma, account age, and recent activity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Reddit username (without 'u/' prefix)"
                        }
                    },
                    "required": ["username"]
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"🛠️ Calling tool: {name} with arguments: {arguments}")
        
        try:
            if name == "search_reddit_posts":
                result = await search_tools.search_posts(arguments)
            elif name == "get_subreddit_posts":
                result = await subreddits_tools.get_posts(arguments)
            elif name == "get_trending_subreddits":
                result = await subreddits_tools.get_trending(arguments)
            elif name == "get_post_details":
                result = await posts_tools.get_details(arguments)
            elif name == "get_post_comments":
                result = await posts_tools.get_comments(arguments)
            elif name == "get_user_profile":
                result = await users_tools.get_profile(arguments)
            else:
                logger.error(f"❌ Unknown tool: {name}")
                return [types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
            
            logger.info(f"✅ Tool {name} executed successfully")
            return [types.TextContent(
                type="text",
                text=str(result)
            )]
            
        except Exception as e:
            logger.error(f"❌ Error executing tool {name}: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]

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
            logger.info("Reddit MCP Server started with dual transports!")
            try:
                yield
            finally:
                logger.info("Reddit MCP Server shutting down...")

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