import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Optional

import aiohttp
import click
import mcp.types as types
import uvicorn
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airtable-mcp-server")

AIRTABLE_PERSONAL_ACCESS_TOKEN = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
if not AIRTABLE_PERSONAL_ACCESS_TOKEN:
    raise ValueError("AIRTABLE_PERSONAL_ACCESS_TOKEN environment variable is required")

AIRTABLE_API_BASE = "https://api.airtable.com/v0"
AIRTABLE_MCP_SERVER_PORT = int(os.getenv("AIRTABLE_MCP_SERVER_PORT", "5000"))


def _get_airtable_headers() -> dict:
    return {
        "Authorization": f"Bearer {AIRTABLE_PERSONAL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def _make_airtable_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    expect_empty_response: bool = False,
) -> dict | None:
    url = f"{AIRTABLE_API_BASE}/{endpoint}"
    headers = _get_airtable_headers()
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_data) as response:
                response.raise_for_status()  # Raise exception for non-2xx status codes
                if expect_empty_response:
                    # For requests like DELETE or PUT roles/reactions where success is 204 No Content
                    if response.status == 204:
                        return None
                    else:
                        # If we expected empty but got something else (and it wasn't an error raised above)
                        logger.warning(
                            f"Expected empty response for {method} {endpoint}, but got status {response.status}"
                        )
                        # Try to parse JSON anyway, might be useful error info
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            return await response.text()  # Return text if not json
                else:
                    # Check if response is JSON before parsing
                    if "application/json" in response.headers.get("Content-Type", ""):
                        return await response.json()
                    else:
                        # Handle non-JSON responses if necessary, e.g., log or return text
                        text_content = await response.text()
                        logger.warning(
                            f"Received non-JSON response for {method} {endpoint}: {text_content[:100]}..."
                        )
                        return {"raw_content": text_content}
        except aiohttp.ClientResponseError as e:
            logger.error(
                f"Airtable API request failed: {e.status} {e.message} for {method} {url}"
            )
            error_details = e.message
            try:
                # Airtable often returns JSON errors
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                # If response body isn't JSON or can't be read
                pass
            raise RuntimeError(
                f"Airtable API Error ({e.status}): {error_details}"
            ) from e
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Airtable API request: {e}"
            )
            raise RuntimeError(
                f"Unexpected error during API call to {method} {url}"
            ) from e


async def get_bases_info() -> dict:
    endpoint = "meta/bases"
    return await _make_airtable_request("GET", endpoint)


@click.command()
@click.option(
    "--port", default=AIRTABLE_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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

    app = Server("airtable-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="airtable_list_bases_info",
                description="Get information about all bases",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "airtable_list_bases_info":
            result = await get_bases_info()
            return [
                types.TextContent(
                    type="text",
                    text=str(result),
                )
            ]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
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

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    main()
