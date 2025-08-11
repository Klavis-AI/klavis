import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

# Import Playwright tool functions from your tools/ package
from tools import (
    launch_browser,
    close_browser,
    new_page,
    close_page,
    go_to_url,
    click_selector,
    fill_selector,
    get_text,
    take_screenshot,
)

logger = logging.getLogger(__name__)
PLAYWRIGHT_MCP_SERVER_PORT = int(os.getenv("PLAYWRIGHT_MCP_SERVER_PORT", "5050"))


@click.command()
@click.option("--port", default=PLAYWRIGHT_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Return JSON bodies for StreamableHTTP (vs SSE streams)",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    # Logging setup
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Low-level MCP server (matches Affinity)
    app = Server("playwright-mcp-server")

    # ---------- Tool discovery ----------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Browsers
            types.Tool(
                name="launch_browser",
                description="Launch a Playwright browser. browser_type: chromium|firefox|webkit; headless: bool.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "browser_type": {
                            "type": "string",
                            "description": "chromium|firefox|webkit (default from env or chromium)",
                        },
                        "headless": {
                            "type": "boolean",
                            "description": "Run headless (default from env)",
                        },
                    },
                },
            ),
            types.Tool(
                name="close_browser",
                description="Close a browser by browser_id.",
                inputSchema={
                    "type": "object",
                    "required": ["browser_id"],
                    "properties": {"browser_id": {"type": "string"}},
                },
            ),

            # Pages
            types.Tool(
                name="new_page",
                description="Create a new page (tab) in a given browser.",
                inputSchema={
                    "type": "object",
                    "required": ["browser_id"],
                    "properties": {"browser_id": {"type": "string"}},
                },
            ),
            types.Tool(
                name="close_page",
                description="Close a page by page_id.",
                inputSchema={
                    "type": "object",
                    "required": ["page_id"],
                    "properties": {"page_id": {"type": "string"}},
                },
            ),
            types.Tool(
                name="go_to_url",
                description='Navigate a page to a URL. Optional wait_until ("load"|"domcontentloaded"|...), timeout_ms.',
                inputSchema={
                    "type": "object",
                    "required": ["page_id", "url"],
                    "properties": {
                        "page_id": {"type": "string"},
                        "url": {"type": "string"},
                        "wait_until": {"type": "string"},
                        "timeout_ms": {"type": "integer"},
                    },
                },
            ),

            # Actions
            types.Tool(
                name="click_selector",
                description="Click an element matching a CSS selector.",
                inputSchema={
                    "type": "object",
                    "required": ["page_id", "selector"],
                    "properties": {
                        "page_id": {"type": "string"},
                        "selector": {"type": "string"},
                        "timeout_ms": {"type": "integer"},
                    },
                },
            ),
            types.Tool(
                name="fill_selector",
                description="Fill an input/textarea selected by CSS with text.",
                inputSchema={
                    "type": "object",
                    "required": ["page_id", "selector", "text"],
                    "properties": {
                        "page_id": {"type": "string"},
                        "selector": {"type": "string"},
                        "text": {"type": "string"},
                        "timeout_ms": {"type": "integer"},
                    },
                },
            ),
            types.Tool(
                name="get_text",
                description="Return textContent from the first element matching selector.",
                inputSchema={
                    "type": "object",
                    "required": ["page_id", "selector"],
                    "properties": {
                        "page_id": {"type": "string"},
                        "selector": {"type": "string"},
                        "timeout_ms": {"type": "integer"},
                    },
                },
            ),

            # Media
            types.Tool(
                name="take_screenshot",
                description="Take a PNG screenshot; returns base64 string.",
                inputSchema={
                    "type": "object",
                    "required": ["page_id"],
                    "properties": {
                        "page_id": {"type": "string"},
                        "full_page": {"type": "boolean"},
                    },
                },
            ),
        ]

    # ---------- Tool execution ----------
    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            if name == "launch_browser":
                res = await launch_browser(**arguments)
            elif name == "close_browser":
                res = await close_browser(**arguments)
            elif name == "new_page":
                res = await new_page(**arguments)
            elif name == "close_page":
                res = await close_page(**arguments)
            elif name == "go_to_url":
                res = await go_to_url(**arguments)
            elif name == "click_selector":
                res = await click_selector(**arguments)
            elif name == "fill_selector":
                res = await fill_selector(**arguments)
            elif name == "get_text":
                res = await get_text(**arguments)
            elif name == "take_screenshot":
                res = await take_screenshot(**arguments)
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            return [types.TextContent(type="text", text=json.dumps(res, indent=2))]
        except ValueError as ve:
            return [types.TextContent(type="text", text=f"Error: {ve}")]
        except Exception as e:
            logger.exception("Unhandled error")
            return [types.TextContent(type="text", text=f"Error: {e}")]

    # ---------- Transports: SSE + StreamableHTTP ----------
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app_: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Playwright MCP started")
            yield
            logger.info("Playwright MCP stopped")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server on port {port}")
    logger.info(f"  - SSE:             http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP:  http://localhost:{port}/mcp")

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    main()
