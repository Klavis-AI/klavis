import os
import logging
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

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
    linkedin_token_context,
    get_profile_info,
    create_post,
    get_user_posts,
    get_company_info,
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkedin-mcp-server")

# LinkedIn API constants and configuration
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
if not LINKEDIN_ACCESS_TOKEN:
    raise ValueError("LINKEDIN_ACCESS_TOKEN environment variable is required")

LINKEDIN_MCP_SERVER_PORT = int(os.getenv("LINKEDIN_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=LINKEDIN_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("linkedin-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="linkedin_get_profile_info",
                description="Get LinkedIn profile information. If person_id is not provided, gets current user's profile.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "string",
                            "description": "The LinkedIn person ID to retrieve information for. Leave empty for current user."
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_create_post",
                description="Create a post on LinkedIn with optional title for article-style posts.",
                inputSchema={
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text content of the post."
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for article-style posts. When provided, creates an article format."
                        },
                        "visibility": {
                            "type": "string",
                            "description": "Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN_USERS).",
                            "default": "PUBLIC"
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_get_user_posts",
                description="Get recent posts from a user's profile (default 10, max 50).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "string",
                            "description": "The LinkedIn person ID. Leave empty for current user's posts."
                        },
                        "count": {
                            "type": "integer",
                            "description": "The number of posts to retrieve (1-50).",
                            "default": 10
                        }
                    }
                }
            ),
            types.Tool(
                name="linkedin_get_company_info",
                description="Get information about a LinkedIn company.",
                inputSchema={
                    "type": "object",
                    "required": ["company_id"],
                    "properties": {
                        "company_id": {
                            "type": "string",
                            "description": "The LinkedIn company ID to retrieve information for."
                        }
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "linkedin_create_post":
            text = arguments.get("text")
            title = arguments.get("title")
            visibility = arguments.get("visibility", "PUBLIC")
            if not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: text parameter is required",
                    )
                ]
            try:
                result = await create_post(text, title, visibility)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
        
        elif name == "linkedin_get_profile_info":
            person_id = arguments.get("person_id")
            try:
                result = await get_profile_info(person_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
        
        elif name == "linkedin_get_user_posts":
            person_id = arguments.get("person_id")
            count = arguments.get("count", 10)
            try:
                result = await get_user_posts(person_id, count)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
        
        
        elif name == "linkedin_get_company_info":
            company_id = arguments.get("company_id")
            if not company_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: company_id parameter is required",
                    )
                ]
            try:
                result = await get_company_info(company_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
        
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract LinkedIn access token from headers (fallback to environment)
        linkedin_token = request.headers.get('x-linkedin-token') or LINKEDIN_ACCESS_TOKEN
        
        # Set the LinkedIn token in context for this request
        token = linkedin_token_context.set(linkedin_token or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            linkedin_token_context.reset(token)
        
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
        
        # Extract LinkedIn access token from headers (fallback to environment)
        headers = dict(scope.get("headers", []))
        linkedin_token = headers.get(b'x-linkedin-token')
        if linkedin_token:
            linkedin_token = linkedin_token.decode('utf-8')
        else:
            linkedin_token = LINKEDIN_ACCESS_TOKEN
        
        # Set the LinkedIn token in context for this request
        token = linkedin_token_context.set(linkedin_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            linkedin_token_context.reset(token)

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
