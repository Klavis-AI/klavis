"""Main server module for Strata MCP Router."""

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .mcp_client_manager import MCPClientManager
from .tools import execute_tool, get_tool_definitions

# Configure logging
logger = logging.getLogger(__name__)

MCP_ROUTER_PORT = int(os.getenv("MCP_ROUTER_PORT", "8080"))

# Global client manager
client_manager = MCPClientManager()


@contextlib.asynccontextmanager
async def config_watching_context():
    """Shared context manager for config watching in both stdio and HTTP modes."""
    # Initialize client manager
    try:
        await client_manager.initialize_from_config()
        logger.info("Client managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize client managers: {e}")
        # Continue anyway, managers will be created on demand

    # Start config watching in background
    def on_config_changed(new_servers):
        """Handle config changes by syncing the client manager."""
        logger.info("Config file changed, syncing client manager...")

        async def safe_sync():
            """Safely sync with config, catching any errors."""
            try:
                await client_manager.sync_with_config(new_servers)
            except Exception as e:
                logger.error(f"Error during config sync: {e}")
                # Don't let sync errors crash the server

        # Schedule sync on the event loop
        asyncio.create_task(safe_sync())

    # Start watching config file for changes
    watch_task = asyncio.create_task(
        client_manager.server_list.watch_config(on_config_changed)
    )
    logger.info("Config file watching enabled - changes will be auto-synced")

    try:
        yield
    finally:
        logger.info("Shutting down...")
        # Stop config watching
        watch_task.cancel()
        try:
            await watch_task
        except asyncio.CancelledError:
            logger.info("Config watching stopped")
        # Clean up client managers
        await client_manager.disconnect_all()


def setup_server_handlers(server: Server) -> None:
    """Set up shared MCP server handlers for both stdio and HTTP modes."""

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available Strata tools."""
        try:
            # Get available servers from client manager
            user_available_servers = list(client_manager.active_clients.keys())
            return get_tool_definitions(user_available_servers)
        except Exception as e:
            logger.error(f"Error listing strata tools: {str(e)}")
            return []

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
        """Call one of the strata tools."""
        return await execute_tool(name, arguments, client_manager)


async def run_stdio_server_async() -> None:
    """Run the Strata MCP router in stdio mode."""

    # Create server instance
    server = Server("strata-mcp-stdio")

    # Set up shared handlers
    setup_server_handlers(server)

    # Use shared config watching context manager
    logger.info("Strata MCP Router running in stdio mode")
    async with config_watching_context():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )


def run_stdio_server() -> int:
    """Run the stdio server synchronously."""
    try:
        asyncio.run(run_stdio_server_async())
        return 0
    except KeyboardInterrupt:
        logger.info("Stdio server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running stdio server: {e}")
        return 1


def run_server(port: int, json_response: bool) -> int:
    """Run the MCP router server with the given configuration."""

    # Create the MCP router server instance
    app = Server("strata-mcp-server")

    # Set up shared handlers
    setup_server_handlers(app)

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection for router")

        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request for router")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            logger.info("StreamableHTTP request completed")

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager and client initialization."""
        async with config_watching_context():
            async with session_manager.run():
                logger.info("Strata MCP Router started with dual transports!")
                logger.info("Available tools:")
                logger.info("- discover_server_actions: Discover available actions")
                logger.info("- get_action_details: Get detailed action parameters")
                logger.info("- execute_action: Execute server actions")
                logger.info("- search_documentation: Search server documentation")
                logger.info("- handle_auth_failure: Handle authentication issues")
                yield

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

    logger.info(f"Strata MCP Router starting on port {port} with dual transports")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0
