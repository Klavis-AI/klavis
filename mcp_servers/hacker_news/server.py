import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    hackerNews_item,
    hackerNews_user,
    hackerNews_maxitem,
    hackerNews_updates_ids,
    hackerNews_showstories_ids,
    hackerNews_beststories_ids,
    hackerNews_newstories_ids,
    hackerNews_jobstories_ids,
    hackerNews_askstories_ids,
    hackerNews_topstories_ids,
    hackerNews_askstories,
    hackerNews_jobstories,
    hackerNews_showstories,
    hackerNews_updates,
    hackerNews_topstories,
    hackerNews_newstories,
    hackerNews_beststories
)

# Configure logging
logger = logging.getLogger(__name__)

HACKER_NEWS_MCP_SERVER_PORT = int(os.getenv("HACKER_NEWS_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=HACKER_NEWS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("hacker-news-mcp-server")

    #-----------------------------------------------------------------------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # For hackerNews_item
            types.Tool(
                name="hackerNews_item",
                description="Fetch a Hacker News item by its numeric item_id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {
                            "type": "integer",
                            "description": "The item's unique identifier (e.g., 8863)"
                        }
                    },
                    "required": ["item_id"]
                }
            ),

            # For hackerNews_user
            types.Tool(
                name="hackerNews_user",
                description="Fetch a Hacker News user by username.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "The user's unique username (e.g., 'pg')"
                        }
                    },
                    "required": ["username"]
                }
            ),

            # For hackerNews_maxitem
            types.Tool(
                name="hackerNews_maxitem",
                description="Fetch the current largest item ID on Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            # For hackerNews_topstories
            types.Tool(
                name="hackerNews_topstories",
                description="Fetch top stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of top stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_beststories
            types.Tool(
                name="hackerNews_beststories",
                description="Fetch best stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of best stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_newstories
            types.Tool(
                name="hackerNews_newstories",
                description="Fetch newest stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of new stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_showstories
            types.Tool(
                name="hackerNews_showstories",
                description="Fetch show stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of show stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_askstories
            types.Tool(
                name="hackerNews_askstories",
                description="Fetch ask stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of ask stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_jobstories
            types.Tool(
                name="hackerNews_jobstories",
                description="Fetch job stories details from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of job stories to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),

            # For hackerNews_updates
            types.Tool(
                name="hackerNews_updates",
                description="Fetch recent updates including items and profiles from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of updates to fetch (default: 5)",
                            "default": 5
                        }
                    },
                    "required": []
                }
            ),
            # For hackerNews_topstories_ids
            types.Tool(
                name="hackerNews_topstories_ids",
                description="Fetch IDs of current top stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_newstories_ids
            types.Tool(
                name="hackerNews_newstories_ids",
                description="Fetch IDs of newest stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_askstories_ids
            types.Tool(
                name="hackerNews_askstories_ids",
                description="Fetch IDs of current ask stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_showstories_ids
            types.Tool(
                name="hackerNews_showstories_ids",
                description="Fetch IDs of current show stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_jobstories_ids
            types.Tool(
                name="hackerNews_jobstories_ids",
                description="Fetch IDs of current job stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_updates_ids
            types.Tool(
                name="hackerNews_updates_ids",
                description="Fetch recent updates (items and profiles) from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),

            # For hackerNews_beststories_ids
            types.Tool(
                name="hackerNews_beststories_ids",
                description="Fetch IDs of current best stories from Hacker News.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Hacker News Item
        if name == "hackerNews_item":
            try:
                item_id = arguments.get("item_id")
                if not item_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameter: item_id",
                        )
                    ]

                result = await hackerNews_item(item_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_item: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News User
        elif name == "hackerNews_user":
            try:
                username = arguments.get("username")
                if not username:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameter: username",
                        )
                    ]

                result = await hackerNews_user(username)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_user: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Max Item
        elif name == "hackerNews_maxitem":
            try:
                result = await hackerNews_maxitem()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_maxitem: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Hacker News Top Stories
        elif name == "hackerNews_topstories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_topstories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_topstories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Best Stories
        elif name == "hackerNews_beststories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_beststories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_beststories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News New Stories
        elif name == "hackerNews_newstories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_newstories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_newstories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Show Stories
        elif name == "hackerNews_showstories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_showstories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_showstories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Ask Stories
        elif name == "hackerNews_askstories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_askstories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_askstories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Job Stories
        elif name == "hackerNews_jobstories":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_jobstories(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_jobstories: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Hacker News Updates
        elif name == "hackerNews_updates":
            try:
                count = arguments.get("count", 5)
                result = await hackerNews_updates(count)
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2)
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_updates: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Hacker News Top Stories IDs
        if name == "hackerNews_topstories_ids":
            try:
                result = await hackerNews_topstories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_topstories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News New Stories IDs
        elif name == "hackerNews_newstories_ids":
            try:
                result = await hackerNews_newstories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_newstories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News Ask Stories IDs
        elif name == "hackerNews_askstories_ids":
            try:
                result = await hackerNews_askstories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_askstories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News Show Stories IDs
        elif name == "hackerNews_showstories_ids":
            try:
                result = await hackerNews_showstories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_showstories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News Job Stories IDs
        elif name == "hackerNews_jobstories_ids":
            try:
                result = await hackerNews_jobstories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_jobstories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News Updates IDs
        elif name == "hackerNews_updates_ids":
            try:
                result = await hackerNews_updates_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_updates_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]

        # Hacker News Best Stories IDs
        elif name == "hackerNews_beststories_ids":
            try:
                result = await hackerNews_beststories_ids()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2) if not isinstance(result, str) else result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing hackerNews_beststories_ids: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps({"error": str(e)})
                    )
                ]



    #-----------------------------------------------------------------------------------------------
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