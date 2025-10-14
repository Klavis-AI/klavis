import os
import logging
import contextlib
import tempfile
from collections.abc import AsyncIterator
from typing import Annotated

import click
import requests
from markitdown import MarkItDown
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("markitdown-mcp-server")

# Default port configuration
MARKITDOWN_MCP_SERVER_PORT = int(os.getenv("MARKITDOWN_MCP_SERVER_PORT", "5000"))


async def convert_document_to_markdown(uri: str) -> str:
    """Convert a resource described by an http:, https: to markdown.

    Args:
        uri: The URI of the resource to convert to markdown

    Returns:
        The markdown representation of the resource.
    """
    if not uri.startswith("http") and not uri.startswith("https"):
        return f"Unsupported uri. Only http:, https: are supported."

    response = requests.get(uri)
    if response.status_code == 200:
        # Save the PDF to a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=True, delete_on_close=True
        ) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
            return MarkItDown().convert_uri(f"file://{temp_path}").markdown
    return f"Failed to download the resource. Status code: {response.status_code}"


@click.command()
@click.option("--port", default=MARKITDOWN_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server(
        "markitdown-mcp-server",
        instructions="A file reader and converter that can read files from urls and convert them to markdown."
        "It currently supports: PDF, PowerPoint, Word, Excel, HTML, Text-based formats (CSV, JSON, XML), ZIP files (iterates over contents), EPubs.",
    )

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="convert_document_to_markdown",
                description="Convert a resource described by an http:, https: to markdown.",
                inputSchema={
                    "type": "object",
                    "required": ["uri"],
                    "properties": {
                        "uri": {
                            "type": "string",
                            "description": "The URI of the resource to convert to markdown. The resource MUST be one of the supported types: PDF, "
                            "PowerPoint, Word, Excel, HTML, Text-based formats (CSV, JSON, XML), ZIP files (iterates over contents), EPubs."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MARKITDOWN_CONVERT", "readOnlyHint": True}),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "convert_document_to_markdown":
            uri = arguments.get("uri")
            
            if not uri:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: URI parameter is required",
                    )
                ]
                
            try:
                result = await convert_document_to_markdown(uri)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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
