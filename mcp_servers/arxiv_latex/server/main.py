#!/usr/bin/env python3
"""
ArXiv LaTeX MCP Server

This server provides tools to fetch and process arXiv papers' LaTeX source code
for better mathematical expression interpretation.
"""

import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import click
import mcp.types as types
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from arxiv_to_prompt import process_latex_source, list_sections, extract_section

# Configure logging
logger = logging.getLogger(__name__)

ARXIV_MCP_SERVER_PORT = int(os.getenv("ARXIV_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option(
    "--port", default=ARXIV_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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

    # Configure webshare proxy for arxiv_to_prompt (uses requests library).
    # Set PROXY_USERNAME and PROXY_PASSWORD env vars to enable.
    proxy_user = os.environ.get("PROXY_USERNAME")
    proxy_pass = os.environ.get("PROXY_PASSWORD")
    if proxy_user and proxy_pass:
        proxy_host = os.environ.get("PROXY_HOST", "p.webshare.io")
        proxy_port = os.environ.get("PROXY_PORT", "80")
        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        os.environ.setdefault("HTTP_PROXY", proxy_url)
        os.environ.setdefault("HTTPS_PROXY", proxy_url)
        logger.info(f"Proxy configured: http://{proxy_host}:{proxy_port}")

    # Create the MCP server instance
    app = Server("arxiv-latex-mcp")

    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="get_paper_prompt",
                description="Get a flattened LaTeX code of a paper from arXiv ID for precise interpretation of mathematical expressions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "The arXiv ID of the paper (e.g., '2403.12345')",
                        }
                    },
                    "required": ["arxiv_id"],
                },
            ),
            types.Tool(
                name="get_paper_abstract",
                description="Get just the abstract of an arXiv paper (faster and cheaper than fetching the full paper)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "The arXiv ID of the paper (e.g., '2403.12345')",
                        }
                    },
                    "required": ["arxiv_id"],
                },
            ),
            types.Tool(
                name="list_paper_sections",
                description="List section headings of an arXiv paper to see its structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "The arXiv ID of the paper (e.g., '2403.12345')",
                        }
                    },
                    "required": ["arxiv_id"],
                },
            ),
            types.Tool(
                name="get_paper_section",
                description="Get a specific section of an arXiv paper by section path (use list_paper_sections first to find available sections)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "The arXiv ID of the paper (e.g., '2403.12345')",
                        },
                        "section_path": {
                            "type": "string",
                            "description": "The section path to extract (e.g., '1', '2.1', 'Introduction'). Use list_paper_sections to find available paths.",
                        },
                    },
                    "required": ["arxiv_id", "section_path"],
                },
            ),
        ]

    LATEX_RENDER_INSTRUCTIONS = """

IMPORTANT INSTRUCTIONS FOR RENDERING:
When discussing this paper, please use dollar sign notation ($...$) for inline equations and double dollar signs ($$...$$) for display equations when providing responses that include LaTeX mathematical expressions.
"""

    @app.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent]:
        """Handle tool calls."""
        if not arguments or "arxiv_id" not in arguments:
            raise ValueError("Missing required argument: arxiv_id")

        arxiv_id = arguments["arxiv_id"]

        try:
            if name == "get_paper_prompt":
                logger.info(f"Processing arXiv paper: {arxiv_id}")
                prompt = process_latex_source(arxiv_id)
                result = prompt + LATEX_RENDER_INSTRUCTIONS
                logger.info(f"Successfully processed arXiv paper: {arxiv_id}")

            elif name == "get_paper_abstract":
                logger.info(f"Getting abstract for arXiv paper: {arxiv_id}")
                result = process_latex_source(arxiv_id, abstract_only=True)
                logger.info(f"Successfully got abstract for: {arxiv_id}")

            elif name == "list_paper_sections":
                logger.info(f"Listing sections for arXiv paper: {arxiv_id}")
                text = process_latex_source(arxiv_id)
                sections = list_sections(text)
                result = "\n".join(sections)
                logger.info(f"Successfully listed sections for: {arxiv_id}")

            elif name == "get_paper_section":
                if "section_path" not in arguments:
                    raise ValueError("Missing required argument: section_path")
                section_path = arguments["section_path"]
                logger.info(f"Getting section '{section_path}' for arXiv paper: {arxiv_id}")
                text = process_latex_source(arxiv_id)
                result = extract_section(text, section_path)
                if result is None:
                    result = f"Section '{section_path}' not found. Use list_paper_sections to see available sections."
                else:
                    result = result + LATEX_RENDER_INSTRUCTIONS
                logger.info(f"Successfully got section for: {arxiv_id}")

            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=result)]

        except Exception as e:
            error_msg = f"Error processing arXiv paper {arxiv_id}: {str(e)}"
            logger.error(error_msg)

            return [types.TextContent(type="text", text=error_msg)]

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
        event_store=None,
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
