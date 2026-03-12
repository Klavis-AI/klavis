#  cli.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import contextlib
import logging
from collections.abc import AsyncIterator

import click
import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from mcp_youtube_transcript import server

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--response-limit",
    type=int,
    help="Maximum number of characters each response contains. Set a negative value to disable pagination.",
    default=50000,
)
@click.option(
    "--webshare-proxy-username",
    metavar="NAME",
    envvar="WEBSHARE_PROXY_USERNAME",
    help="Webshare proxy service username.",
)
@click.option(
    "--webshare-proxy-password",
    metavar="PASSWORD",
    envvar="WEBSHARE_PROXY_PASSWORD",
    help="Webshare proxy service password.",
)
@click.option("--http-proxy", metavar="URL", envvar="HTTP_PROXY", help="HTTP proxy server URL.")
@click.option("--https-proxy", metavar="URL", envvar="HTTPS_PROXY", help="HTTPS proxy server URL.")
@click.option("--transport", type=click.Choice(["stdio", "streamable-http"]), default="streamable-http", help="Transport type.")
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
@click.option("--port", type=int, default=5000, help="Port to listen on.")
@click.version_option()
def main(
    response_limit: int | None,
    webshare_proxy_username: str | None,
    webshare_proxy_password: str | None,
    http_proxy: str | None,
    https_proxy: str | None,
    transport: str,
    host: str,
    port: int,
) -> None:
    """YouTube Transcript MCP server."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    mcp = server(response_limit, webshare_proxy_username, webshare_proxy_password, http_proxy, https_proxy)

    if transport == "stdio":
        logger.info("Starting Youtube Transcript MCP server (stdio)")
        mcp.run(transport="stdio")
        return

    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP transport!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on {host}:{port}")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    uvicorn.run(starlette_app, host=host, port=port)
