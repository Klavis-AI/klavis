import os
import logging
import contextlib
import uuid
import tempfile
from collections.abc import AsyncIterator
from typing import Annotated

import click
import pypandoc
import datetime
import google.auth
from google.auth.transport import requests
from google.cloud import storage
from google.cloud.exceptions import NotFound
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pandoc-mcp-server")

# Default port configuration
PANDOC_MCP_SERVER_PORT = int(os.getenv("PANDOC_MCP_SERVER_PORT", "5000"))


def upload_blob_and_get_signed_url(
    bucket_name, source_file_name, destination_blob_name
):
    """
    Uploads a file to a Google Cloud Storage bucket and generates a URL for it.

    Args:
        bucket_name (str): The name of your GCS bucket.
        source_file_name (str): The path to the local file to upload.
        destination_blob_name (str): The desired name/path for the file within the bucket.

    Returns:
        str: The signed URL for downloading the blob, or None if an error occurred.
    """
    try:
        credentials, _ = google.auth.default()
        request = requests.Request()
        credentials.refresh(request)

        # Initialize the Cloud Storage client
        # Uses Application Default Credentials (ADC) by default.
        storage_client = storage.Client(credentials=credentials)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        logger.info(
            f"Uploading {source_file_name} to gs://{bucket_name}/{destination_blob_name}..."
        )
        url = blob.generate_signed_url(
            version="v4",
            service_account_email=credentials.service_account_email,
            access_token=credentials.token,
            # This URL is valid for 7 days
            expiration=datetime.timedelta(days=7),
            # Allow GET requests using this URL.
            method="GET",
        )

        return url

    except NotFound:
        logger.error(
            f"Error: Bucket '{bucket_name}' not found or insufficient permissions."
        )
        return None
    except FileNotFoundError:
        logger.error(f"Error: Source file not found at '{source_file_name}'")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


async def convert_markdown_to_file(markdown_text: str, output_format: str) -> str:
    """
    Convert markdown text to pdf, microsoft word and html files.
    
    Args:
        markdown_text: The text in markdown format to convert
        output_format: The format to convert the markdown to (pdf, docx, doc, html, html5)
        
    Returns:
        The converted file url.
    """
    if output_format not in ["pdf", "docx", "doc", "html", "html5"]:
        return f"Unsupported format. Only pdf, docx, doc, html and html5 are supported."
    with tempfile.NamedTemporaryFile(
        delete=True, suffix=f".{output_format}", delete_on_close=True
    ) as temp_file:
        temp_file_path = temp_file.name
        pypandoc.convert_text(
            markdown_text,
            to=output_format,
            format="md",
            outputfile=temp_file_path,
            sandbox=True,
        )
        url = upload_blob_and_get_signed_url(
            os.environ["GCS_BUCKET_NAME"],
            temp_file_path,
            f"{str(uuid.uuid4())}.{output_format}",
        )
    return url


@click.command()
@click.option("--port", default=PANDOC_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
        "pandoc-mcp-server",
        instructions="Using pandoc to convert markdown text to pdf, microsoft word and html files.",
    )

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="convert_markdown_to_file",
                description="Convert markdown text to pdf, microsoft word and html files. Returns the url of the converted file.",
                inputSchema={
                    "type": "object",
                    "required": ["markdown_text", "output_format"],
                    "properties": {
                        "markdown_text": {
                            "type": "string",
                            "description": "The text in markdown format to convert."
                        },
                        "output_format": {
                            "type": "string",
                            "description": "The format to convert the markdown to. Must be one of pdf, docx, doc, html, html5."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PANDOC_CONVERT"}),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "convert_markdown_to_file":
            markdown_text = arguments.get("markdown_text")
            output_format = arguments.get("output_format")
            
            if not markdown_text or not output_format:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Both markdown_text and output_format parameters are required",
                    )
                ]
                
            try:
                result = await convert_markdown_to_file(markdown_text, output_format)
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
