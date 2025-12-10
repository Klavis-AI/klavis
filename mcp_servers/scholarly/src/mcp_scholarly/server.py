import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import List

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from .arxiv_search import ArxivSearch
from .google_scholar import GoogleScholar

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

SCHOLARLY_MCP_SERVER_PORT = int(os.getenv("SCHOLARLY_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option("--port", default=SCHOLARLY_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("mcp-scholarly")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """
        List available tools.
        Each tool specifies its arguments using JSON Schema validation.
        """
        return [
            types.Tool(
                name="search-arxiv",
                description="Search arxiv for articles related to the given keyword.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string", "description": "Search keyword for arXiv articles"},
                        "max_results": {"type": "integer", "description": "Maximum number of results (default: 10)", "default": 10},
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
                        "keyword": {"type": "string", "description": "Search keyword for Google Scholar articles"},
                    },
                    "required": ["keyword"],
                },
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Handle tool execution requests.
        Tools can modify server state and notify clients of changes.
        """
        try:
            if name == "search-arxiv":
                keyword = arguments.get("keyword")
                max_results = arguments.get("max_results", 10)
                
                if not keyword:
                    raise ValueError("Missing keyword")
                
                arxiv_search = ArxivSearch()
                formatted_results = arxiv_search.search(keyword, max_results)
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Search arXiv for '{keyword}':\n\n"
                             + "\n\n---\n\n".join(formatted_results)
                    ),
                ]
            
            elif name == "search-google-scholar":
                keyword = arguments.get("keyword")
                
                if not keyword:
                    raise ValueError("Missing keyword")
                
                google_scholar = GoogleScholar()
                formatted_results = google_scholar.search_pubs(keyword=keyword)
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Search Google Scholar for '{keyword}':\n\n"
                             + "\n\n---\n\n".join(formatted_results)
                    ),
                ]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}",
                )
            ]

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
            logger.info("Application started!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with StreamableHTTP route
    starlette_app = Starlette(
        debug=True,
        routes=[
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port}")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()
