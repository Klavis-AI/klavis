import contextlib
import logging
import os
from collections.abc import AsyncIterator

import mcp.types as types
import uvicorn
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from .arxiv_search import ArxivSearch
from .google_scholar import GoogleScholar

logger = logging.getLogger(__name__)

server = Server("mcp-scholarly")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search-arxiv",
            description="Search arxiv for articles related to the given keyword.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                },
                "required": ["keyword"],
            },
        ),
        types.Tool(
            name="search-google-scholar",
            description="Search google scholar for articles related to the given keyword.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                },
                "required": ["keyword"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
        name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name != "search-arxiv" and name != "search-google-scholar":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Missing arguments")

    keyword = arguments.get("keyword")

    if not keyword:
        raise ValueError("Missing keyword")

    formatted_results = []
    if name == "search-arxiv":
        arxiv_search = ArxivSearch()
        formatted_results = arxiv_search.search(keyword)
    elif name == "search-google-scholar":
        google_scholar = GoogleScholar()
        formatted_results = google_scholar.search_pubs(keyword=keyword)

    return [
        types.TextContent(
            type="text",
            text=f"Search articles for {keyword}:\n"
                 + "\n\n\n".join(formatted_results)
        ),
    ]


def main():
    port = int(os.environ.get("PORT", 5000))

    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("mcp-scholarly server started")
            try:
                yield
            finally:
                logger.info("mcp-scholarly server shutting down")

    starlette_app = Starlette(
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Starting mcp-scholarly on port {port}, endpoint: /mcp")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
