import logging
import os
import sys
import click
from mcp.server.lowlevel import Server
from mcp.types import TextContent, Tool
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.sse import SseServerTransport
from starlette.types import Receive, Scope, Send
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from collections.abc import AsyncIterator
import contextlib
import uvicorn
from typing import Any
from dotenv import load_dotenv
from starlette.responses import Response

# Ensure local imports work whether executed from src/ or project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from tools import get_tavily_tools  # noqa: E402
from handlers.tavily_search import tavily_search_handler  # noqa: E402
from handlers.tavily_extract import tavily_extract_handler  # noqa: E402
from handlers.tavily_crawl import tavily_crawl_handler  # noqa: E402
from handlers.tavily_map import tavily_map_handler  # noqa: E402

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
TAVILY_MCP_SERVER_PORT = int(os.getenv("TAVILY_MCP_SERVER_PORT", "5002"))


@click.command()
@click.option(
    "--port", default=TAVILY_MCP_SERVER_PORT, help="Port to listen on for HTTP"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("tavily_mcp_server")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return get_tavily_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        logger.info(f"Calling tool '{name}'")

        try:
            if name == "tavily_search":
                result = await tavily_search_handler(arguments)
            elif name == "tavily_extract":
                result = await tavily_extract_handler(arguments)
            elif name == "tavily_crawl":
                result = await tavily_crawl_handler(arguments)
            elif name == "tavily_map":
                result = await tavily_map_handler(arguments)
            else:
                logger.error(f"Unknown tool name: {name}")
                return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

            logger.info(f"Tool '{name}' completed successfully")
            return [TextContent(type="text", text=result)]

        except ValueError as e:
            # Likely argument issue
            logger.warning(f"Invalid input for tool '{name}': {e}")
            return [TextContent(type="text", text=f"Invalid input: {str(e)}")]

        except Exception as e:
            logger.exception(f"Error running tool '{name}': {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Something went wrong while running tool '{name}'. Error: {str(e)}",
                )
            ]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        except Exception:
            logger.exception("SSE: unhandled error")
        return Response()

    # Create the session manager with stateless true stateless mode
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        try:
            await session_manager.handle_request(scope, receive, send)
        except Exception:
            logger.exception("StreamableHTTP: unhandled error")

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP Session Manager")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    routes = [
        # SSE routes
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
        # StreamableHTTP route
        Mount("/mcp", app=handle_streamable_http),
    ]

    # Create an ASGI application using the transport
    starlette_app = Starlette(
        debug=True,
        lifespan=lifespan,
        routes=routes,
    )

    uvicorn.run(
        starlette_app,
        host="0.0.0.0",
        port=port,
    )

    return 0


if __name__ == "__main__":
    main()
