#!/usr/bin/env python3
"""
QuickBooks MCP Server with SSE and Streamable HTTP Transport

This server provides MCP tools for interacting with QuickBooks APIs.
Supports both Server-Sent Events (SSE) and Streamable HTTP transport modes.
"""

import os
import logging
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import accounts, invoices, customers, payments, vendors
from session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quickbooks-mcp-server")

# Environment configuration
QB_MCP_SERVER_PORT = int(os.getenv("QB_MCP_SERVER_PORT", "5000"))

# Context variable to store QB credentials for the current request
qb_credentials_context: ContextVar[dict] = ContextVar(
    'qb_credentials', default=None)

# Initialize session manager
session_manager_instance = SessionManager()

# Initialize the MCP server
server = Server("quickbooks-mcp-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available QuickBooks tools."""
    tool_list = [*accounts.tools, *invoices.tools, *
                 customers.tools, *payments.tools, *vendors.tools]
    logger.debug(f"Available tools: {[tool.name for tool in tool_list]}")
    return tool_list


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Execute a specific QuickBooks tool."""
    logger.debug(f"Calling tool: {name} with arguments: {arguments}")

    # Extract QuickBooks credentials from arguments if provided
    qb_access_token = arguments.pop('qb_access_token', None)
    qb_realm_id = arguments.pop('qb_realm_id', None)
    qb_environment = arguments.pop('qb_environment', None)

    # If no credentials in arguments, try to get from context (headers)
    if not any([qb_access_token, qb_realm_id, qb_environment]):
        context_credentials = qb_credentials_context.get()
        if context_credentials:
            qb_access_token = context_credentials.get('access_token')
            qb_realm_id = context_credentials.get('realm_id')
            qb_environment = context_credentials.get('environment')
            logger.debug("Using QB credentials from request headers")

    try:
        # Get session for this request
        session = session_manager_instance.get_session(
            qb_access_token, qb_realm_id, qb_environment)
    except ValueError as e:
        return [types.TextContent(
            type="text",
            text=f"Configuration error: {str(e)}. Please provide qb_access_token and qb_realm_id in the request arguments, or set QB_ACCESS_TOKEN and QB_REALM_ID environment variables, or provide credentials via HTTP headers (x-qb-access-token, x-qb-realm-id, x-qb-environment)."
        )]

    # Map tools to session managers
    tool_map = {
        "quickbooks_list_accounts": session.account_manager.list_accounts,
        "quickbooks_get_account": session.account_manager.get_account,
        "quickbooks_create_account": session.account_manager.create_account,
        "quickbooks_search_accounts": session.account_manager.search_accounts,
        "quickbooks_update_account": session.account_manager.update_account,
        "quickbooks_create_invoice": session.invoice_manager.create_invoice,
        "quickbooks_get_invoice": session.invoice_manager.get_invoice,
        "quickbooks_list_invoices": session.invoice_manager.list_invoices,
        "quickbooks_update_invoice": session.invoice_manager.update_invoice,
        "quickbooks_delete_invoice": session.invoice_manager.delete_invoice,
        "quickbooks_send_invoice": session.invoice_manager.send_invoice,
        "quickbooks_void_invoice": session.invoice_manager.void_invoice,
        "quickbooks_search_invoices": session.invoice_manager.search_invoices,
        "quickbooks_create_customer": session.customer_manager.create_customer,
        "quickbooks_get_customer": session.customer_manager.get_customer,
        "quickbooks_list_customers": session.customer_manager.list_customers,
        "quickbooks_search_customers": session.customer_manager.search_customers,
        "quickbooks_update_customer": session.customer_manager.update_customer,
        "quickbooks_deactivate_customer": session.customer_manager.deactivate_customer,
        "quickbooks_activate_customer": session.customer_manager.activate_customer,
        "quickbooks_create_payment": session.payment_manager.create_payment,
        "quickbooks_get_payment": session.payment_manager.get_payment,
        "quickbooks_list_payments": session.payment_manager.list_payments,
        "quickbooks_update_payment": session.payment_manager.update_payment,
        "quickbooks_delete_payment": session.payment_manager.delete_payment,
        "quickbooks_send_payment": session.payment_manager.send_payment,
        "quickbooks_void_payment": session.payment_manager.void_payment,
        "quickbooks_search_payments": session.payment_manager.search_payments,
        "quickbooks_create_vendor": session.vendor_manager.create_vendor,
        "quickbooks_get_vendor": session.vendor_manager.get_vendor,
        "quickbooks_list_vendors": session.vendor_manager.list_vendors,
        "quickbooks_update_vendor": session.vendor_manager.update_vendor,
        "quickbooks_activate_vendor": session.vendor_manager.activate_vendor,
        "quickbooks_deactivate_vendor": session.vendor_manager.deactivate_vendor,
        "quickbooks_search_vendors": session.vendor_manager.search_vendors,
    }

    if name not in tool_map:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

    try:
        result = await tool_map[name](**arguments)
        if name in [
            "quickbooks_create_account", "quickbooks_get_account", "quickbooks_update_account",
            "quickbooks_create_customer", "quickbooks_get_customer", "quickbooks_update_customer", "quickbooks_deactivate_customer", "quickbooks_activate_customer",
            "quickbooks_create_payment", "quickbooks_get_payment", "quickbooks_update_payment", "quickbooks_delete_payment", "quickbooks_send_payment", "quickbooks_void_payment",
            "quickbooks_create_vendor", "quickbooks_get_vendor", "quickbooks_update_vendor", "quickbooks_activate_vendor", "quickbooks_deactivate_vendor"
        ]:
            if isinstance(result, dict):
                return [types.TextContent(
                    type="text",
                    text="\n".join(f"{k}: {v}" for k, v in result.items())
                )]
        elif name in [
            "quickbooks_list_accounts", "quickbooks_search_accounts", "quickbooks_list_invoices", "quickbooks_search_invoices",
            "quickbooks_list_customers", "quickbooks_search_customers", "quickbooks_list_payments", "quickbooks_search_payments", "quickbooks_list_vendors", "quickbooks_search_vendors"
        ]:
            # Handle list results
            if isinstance(result, list):
                if not result:
                    return [types.TextContent(type="text", text="No results found.")]
                return [types.TextContent(type="text", text=str(result))]
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        import traceback
        logger.error(
            f"Error executing tool {name}: {e.message if hasattr(e, 'message') else str(e)}")
        logger.error(traceback.format_exc())
        return [types.TextContent(
            type="text",
            text=f"Error executing tool {name}: {e.message if hasattr(e, 'message') else str(e)}"
        )]


@click.command()
@click.option("--port", default=QB_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    """Start the QuickBooks MCP server with SSE and Streamable HTTP support."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE connections with QuickBooks credential extraction."""
        logger.info("Handling SSE connection")

        # Extract QB credentials from headers
        qb_access_token, qb_realm_id, qb_environment = session_manager_instance.extract_credentials_from_headers(
            request)

        # Store credentials in scope for later use
        if any([qb_access_token, qb_realm_id, qb_environment]):
            credentials = {
                'access_token': qb_access_token,
                'realm_id': qb_realm_id,
                'environment': qb_environment
            }
            request.scope['qb_credentials'] = credentials
            qb_credentials_context.set(credentials)
            logger.info(
                f"QB credentials extracted from SSE headers for realm: {qb_realm_id or 'env'}")

        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle Streamable HTTP requests with QuickBooks credential extraction."""
        logger.info("Handling StreamableHTTP request")

        # Extract QB credentials from headers
        qb_access_token, qb_realm_id, qb_environment = session_manager_instance.extract_credentials_from_headers(
            scope)

        # Store credentials in scope for later use
        if any([qb_access_token, qb_realm_id, qb_environment]):
            credentials = {
                'access_token': qb_access_token,
                'realm_id': qb_realm_id,
                'environment': qb_environment
            }
            scope['qb_credentials'] = credentials
            qb_credentials_context.set(credentials)
            logger.info(
                f"QB credentials extracted from headers for realm: {qb_realm_id or 'env'}")

        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                await session_manager_instance.cleanup()
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
