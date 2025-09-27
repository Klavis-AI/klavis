"""
MCP Server – Google News (SerpAPI)
----------------------------------
* google_news_search_news
* google_news_get_top_headlines
* google_news_get_trending_topics
"""

from __future__ import annotations

import contextlib, os, json, logging, tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Dict, List

import time
import click, dotenv, uvicorn
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

# ──────────────────────────────  local business logic  ───────────────────────── #
from google_news.tools.base import ToolExecutionError
from google_news.tools.search_news import run as search_news, ArticleSearchIn

from google_news.tools.utils import schema_from_model

# ──────────────────────────────────────────────────────────────────────────────── #

dotenv.load_dotenv()  # pick up SERPAPI_API_KEY / JSON_RESPONSE
PORT = int(os.getenv("GOOGLE_NEWS_MCP_SERVER_PORT", "5000"))

# ---------------------------------------------------------------------------- #
#  Logging (file + stderr)                                                     #
# ---------------------------------------------------------------------------- #
BASE = Path(".")
LOG_FILE = BASE / "google_news_mcp_server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
    filemode="w",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
logging.getLogger("").addHandler(console)

logger = logging.getLogger("google-news-mcp-server")
for noisy in ("httpcore", "anyio"):
    logging.getLogger(noisy).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------- #
#  🖥  CLI                                                                    #
# ---------------------------------------------------------------------------- #
@click.command()
@click.option("--port", default=PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Python log level")
@click.option(
    "--json-response", is_flag=True, help="Return one-shot JSON instead of SSE"
)
def main(port: int, log_level: str, json_response: bool) -> int:
    # defer heavy imports so `click --help` stays fast
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))

    # ── MCP core ───────────────────────────────────────────────────────────── #
    app = Server(
        "google-news-mcp-server",
        instructions="Google News Server via SerpAPI: you're allowed to perform keyword search to search for news, top headlines and trending topics.",
    )

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="google_news_search_news",
                description="Keyword search across Google News results.",
                inputSchema=schema_from_model(ArticleSearchIn),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        logger.info("Tool call %s args=%s", name, arguments)
        ctx = app.request_context

        try:
            if name == "google_news_search_news":
                res = await search_news(ArticleSearchIn(**arguments))
            else:
                raise ValueError(f"Unknown tool {name}")

            # Evaluate whether to return a JSONRPCResponse or a TextContent
            # Successful call → serialize via Pydantic
            return [types.TextContent(type="text", text=res.model_dump_json(indent=2))]

        except ToolExecutionError as e:
            logger.warning(
                "%s failed: %s [status_code=%s]",
                name,
                e,
                getattr(e, "status_code", None),
            )
            # Rate‐limit? SerpAPI returns HTTP 429 when you exceed your quota
            if getattr(e, "status_code", None) == 429:
                # If SerpAPI provided retry info, you could inspect e.details or headers
                payload = {
                    "error": "Rate limit exceeded",
                    "retry_after": "It has been reached a Rate limit error for SerpAPI services. Inform the user about it: please wait before retrying.",
                    "details": str(e),
                }

                time.sleep(
                    5
                )  # Sleep guardrail -> other approaches are eventually applicable, like wait and retry, depends on UX

                return [
                    types.TextContent(type="text", text=json.dumps(payload, indent=2))
                ]

            # Other expected errors
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"The following tool execution error occured during runtime: {str(e)}"
                        },
                        indent=2,
                    ),
                )
            ]

        except Exception as e:  # Exception fallbak
            logger.exception("Unexpected error in %s", name)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {"error": "Unexpected", "detail": str(e)}, indent=2
                    ),
                )
            ]

    # ── Transports ─────────────────────────────────────────────────────────── #
    sse = SseServerTransport("/messages/")
    manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_sse(request):
        logger.info("SSE connect")
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    async def handle_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        async with manager.run():
            logger.info("Google News MCP server ready!")
            yield
            logger.info("Google News MCP server shutting down…")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_http),
            Mount("/mcp/", app=handle_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Google News MCP Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level=log_level.lower())
    return 0


if __name__ == "__main__":
    main()
