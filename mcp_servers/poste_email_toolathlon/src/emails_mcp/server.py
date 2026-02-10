import argparse
import base64
import json
import logging
import sys
import os

from mcp.server.fastmcp import FastMCP
from .config import config_manager
from .models.config import EmailConfig
from .server_context import (
    email_config_context,
    get_email_config,
    parse_email_config_from_dict,
    create_services,
)
from .tools import (
    register_email_tools,
    register_folder_tools,
    register_management_tools,
)

# Configure logging
logger = logging.getLogger(__name__)

EMAILS_MCP_SERVER_PORT = int(os.getenv("EMAILS_MCP_SERVER_PORT", "5000"))


def extract_access_token(request_or_scope) -> EmailConfig | None:
    """Extract email config from x-auth-data header or AUTH_DATA env var.

    The auth data JSON is expected to contain email config fields:
    email, password, name, imap_server, imap_port, smtp_server, smtp_port,
    use_ssl, use_starttls.
    """
    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            raw = request_or_scope.headers.get(b'x-auth-data')
            if raw:
                auth_data = base64.b64decode(raw).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            raw = headers.get(b'x-auth-data')
            if raw:
                auth_data = base64.b64decode(raw).decode('utf-8')

    if not auth_data:
        return None

    try:
        data = json.loads(auth_data)
        email_config = parse_email_config_from_dict(data)
        logging.info(f"Extracted email config for {email_config} from auth data")
        return email_config
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return None


def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def main():
    """Main function to run the emails MCP server"""
    import contextlib
    from collections.abc import AsyncIterator

    import uvicorn
    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Mount, Route
    from starlette.types import Receive, Scope, Send

    parser = argparse.ArgumentParser(description="Emails MCP Server")
    parser.add_argument(
        "--attachment_upload_path",
        type=str,
        default=None,
        help="Directory path for attachment uploads (restricts file selection to this path and subdirectories)",
    )
    parser.add_argument(
        "--attachment_download_path",
        type=str,
        default=None,
        help="Directory path for attachment downloads (files will be saved here with unique names)",
    )
    parser.add_argument(
        "--email_export_path",
        type=str,
        default=None,
        help="Directory path for email exports (exports will be saved here with date-based filenames)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=EMAILS_MCP_SERVER_PORT,
        help="Port to listen on for HTTP",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Load workspace configuration (paths only, no email config)
    config_manager.load_workspace_config(
        attachment_upload_path=args.attachment_upload_path,
        attachment_download_path=args.attachment_download_path,
        email_export_path=args.email_export_path,
    )

    # Initialize MCP server (FastMCP for tool registration only)
    mcp = FastMCP(
        "emails-mcp",
        host="0.0.0.0",
        port=str(args.port),
        streamable_http_path="/mcp/",
    )

    # Register MCP tools — services are created per-request via get_email_config()
    register_email_tools(mcp)
    register_folder_tools(mcp)
    register_management_tools(mcp)

    logger.info("All MCP tools registered successfully")

    # Log path restrictions if set
    if config_manager.workspace_config:
        ws = config_manager.workspace_config
        if ws.attachment_upload_path:
            logger.info(f"Attachment uploads restricted to: {ws.attachment_upload_path}")
        if ws.attachment_download_path:
            logger.info(f"Attachment downloads will be saved to: {ws.attachment_download_path}")
        if ws.email_export_path:
            logger.info(f"Email exports will be saved to: {ws.email_export_path}")

    # --- Build Starlette app with auth-context wiring ---

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        email_cfg = extract_access_token(request)
        if not email_cfg:
            return Response("Missing or invalid x-auth-data header", status_code=401)

        token = email_config_context.set(email_cfg)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp._mcp_server.run(
                    streams[0], streams[1], mcp._mcp_server.create_initialization_options()
                )
        finally:
            email_config_context.reset(token)

        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        email_cfg = extract_access_token(scope)
        if not email_cfg:
            response = Response("Missing or invalid x-auth-data header", status_code=401)
            await response(scope, receive, send)
            return

        token = email_config_context.set(email_cfg)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            email_config_context.reset(token)

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
        debug=args.debug,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {args.port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{args.port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{args.port}/mcp")
    logger.info("Email config is provided at runtime via x-auth-data header or AUTH_DATA env var")

    uvicorn.run(starlette_app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
