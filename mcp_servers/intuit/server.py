#!/usr/bin/env python3
"""
Intuit MCP Server with SSE and Streamable HTTP Transport

This server provides MCP tools for interacting with Intuit QuickBooks APIs.
Supports both Server-Sent Events (SSE) and Streamable HTTP transport modes.
"""

import os
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import Any

import click
from tools.http_client import QuickBooksHTTPClient
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import accounts, invoices, customers, payments, vendors
from tools.invoices import InvoiceManager
from tools.customers import CustomerManager
from tools.payments import PaymentManager
from tools.vendors import VendorManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intuit-mcp-server")

# Environment configuration
INTUIT_MCP_SERVER_PORT = int(os.getenv("INTUIT_MCP_SERVER_PORT", "5001"))


class IntuitMCPService:
    def __init__(self):
        self.client = QuickBooksHTTPClient()
        self.account_manager = None
        self.invoice_manager = None
        self.customer_manager = None
        self.payment_manager = None
        self.vendor_manager = None
        if self.client.is_configured():
            logger.info("QuickBooks HTTP client initialized successfully")
            from tools.accounts import AccountManager
            self.account_manager = AccountManager(self.client)
            self.invoice_manager = InvoiceManager(self.client)
            self.customer_manager = CustomerManager(self.client)
            self.payment_manager = PaymentManager(self.client)
            self.vendor_manager = VendorManager(self.client)
        else:
            logger.warning(
                "QuickBooks configuration not found. Please set:\n"
                "- QB_ACCESS_TOKEN: Your QuickBooks access token\n"
                "- QB_REALM_ID: Your company/realm ID"
            )

    def get_client(self) -> QuickBooksHTTPClient:
        """Get the QuickBooks HTTP client instance."""
        return self.client


intuit_service = IntuitMCPService()

# Initialize the MCP server
server = Server("intuit-mcp-server")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Intuit tools."""
    tool_list = [*accounts.tools, *invoices.tools, *customers.tools, *payments.tools, *vendors.tools]
    logger.debug(f"Available tools: {[tool.name for tool in tool_list]}")
    return tool_list


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Execute a specific Intuit tool."""
    logger.debug(f"Calling tool: {name} with arguments: {arguments}")

    if not intuit_service.client.is_configured():
        return [types.TextContent(
            type="text",
            text="QuickBooks client not configured. Please set QB_ACCESS_TOKEN and QB_REALM_ID environment variables."
        )]

    tool_map = {
        "list_accounts": intuit_service.account_manager.list_accounts,
        "get_account": intuit_service.account_manager.get_account,
        "create_account": intuit_service.account_manager.create_account,
        "update_account": intuit_service.account_manager.update_account,
        "create_invoice": intuit_service.invoice_manager.create_invoice,
        "get_invoice": intuit_service.invoice_manager.get_invoice,
        "list_invoices": intuit_service.invoice_manager.list_invoices,
        "update_invoice": intuit_service.invoice_manager.update_invoice,
        "delete_invoice": intuit_service.invoice_manager.delete_invoice,
        "send_invoice": intuit_service.invoice_manager.send_invoice,
        "void_invoice": intuit_service.invoice_manager.void_invoice,
        "search_invoices": intuit_service.invoice_manager.search_invoices,
        "create_customer": intuit_service.customer_manager.create_customer,
        "get_customer": intuit_service.customer_manager.get_customer,
        "list_customers": intuit_service.customer_manager.list_customers,
        "update_customer": intuit_service.customer_manager.update_customer,
        "deactivate_customer": intuit_service.customer_manager.deactivate_customer,
        "activate_customer": intuit_service.customer_manager.activate_customer,
        "create_payment": intuit_service.payment_manager.create_payment,
        "get_payment": intuit_service.payment_manager.get_payment,
        "list_payments": intuit_service.payment_manager.list_payments,
        "update_payment": intuit_service.payment_manager.update_payment,
        "delete_payment": intuit_service.payment_manager.delete_payment,
        "send_payment": intuit_service.payment_manager.send_payment,
        "void_payment": intuit_service.payment_manager.void_payment,
        "search_payments": intuit_service.payment_manager.search_payments,
        "create_vendor": intuit_service.vendor_manager.create_vendor,
        "get_vendor": intuit_service.vendor_manager.get_vendor,
        "list_vendors": intuit_service.vendor_manager.list_vendors,
        "update_vendor": intuit_service.vendor_manager.update_vendor,
        "activate_vendor": intuit_service.vendor_manager.activate_vendor,
        "deactivate_vendor": intuit_service.vendor_manager.deactivate_vendor,
        "search_vendors": intuit_service.vendor_manager.search_vendors,
    }

    if name not in tool_map:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

    try:
        result = await tool_map[name](**arguments)
        if name in ["create_customer", "get_customer", "update_customer", "deactivate_customer", "activate_customer",
                   "create_payment", "get_payment", "update_payment", "delete_payment", "send_payment", "void_payment",
                   "create_vendor", "get_vendor", "update_vendor", "activate_vendor", "deactivate_vendor"]:
            if isinstance(result, dict):
                return [types.TextContent(
                    type="text",
                    text="\n".join(f"{k}: {v}" for k, v in result.items())
                )]
        return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        import traceback
        logger.error(f"Error executing tool {name}: {e.message if hasattr(e, 'message') else str(e)}")
        logger.error(traceback.format_exc())
        return [types.TextContent(
            type="text",
            text=f"Error executing tool {name}: {e.message if hasattr(e, 'message') else str(e)}"
        )]


@click.command()
@click.option("--port", default=INTUIT_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    """Start the Intuit MCP server with SSE and Streamable HTTP support."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE connections."""
        logger.info("Handling SSE connection")
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
        """Handle Streamable HTTP requests."""
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
                await intuit_service.client.close()
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
