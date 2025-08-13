import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
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
from dotenv import load_dotenv

from tools import (
    stripe_secret_key_context,
    create_customer, list_customers,
    create_product, list_products, create_price, list_prices,
    create_payment_link, list_payment_intents, create_refund,
    list_invoices, create_invoice, create_invoice_item, finalize_invoice,
    create_billing_portal_session,
    retrieve_balance
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

STRIPE_MCP_SERVER_PORT = int(os.getenv("STRIPE_MCP_SERVER_PORT", "5001"))

@click.command()
@click.option("--port", default=STRIPE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("stripe-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="stripe_create_customer",
                description="Create a customer in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the customer.",
                        },
                        "email": {
                            "type": "string",
                            "description": "The email of the customer.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_list_customers",
                description="Fetch a list of customers from Stripe.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "A limit on the number of objects to be returned. Limit can range between 1 and 100.",
                        },
                        "email": {
                            "type": "string",
                            "description": "A case-sensitive filter on the list based on the customer's email field.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_product",
                description="Create a product in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the product.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the product.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_list_products",
                description="Fetch a list of products from Stripe.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_price",
                description="Create a price for a product in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["product", "unit_amount", "currency"],
                    "properties": {
                        "product": {
                            "type": "string",
                            "description": "The ID of the product to create the price for.",
                        },
                        "unit_amount": {
                            "type": "integer",
                            "description": "The unit amount of the price in cents.",
                        },
                        "currency": {
                            "type": "string",
                            "description": "The currency of the price.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_list_prices",
                description="Fetch a list of prices from Stripe.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product": {
                            "type": "string",
                            "description": "The ID of the product to list prices for.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_payment_link",
                description="Create a payment link in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["price", "quantity"],
                    "properties": {
                        "price": {
                            "type": "string",
                            "description": "The ID of the price to create the payment link for.",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "The quantity of the product to include.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_list_payment_intents",
                description="List payment intents in Stripe.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer": {
                            "type": "string",
                            "description": "The ID of the customer to list payment intents for.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "A limit on the number of objects to be returned. Limit can range between 1 and 100.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_refund",
                description="Refund a payment intent in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["payment_intent"],
                    "properties": {
                        "payment_intent": {
                            "type": "string",
                            "description": "The ID of the PaymentIntent to refund.",
                        },
                        "amount": {
                            "type": "integer",
                            "description": "The amount to refund in cents.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_list_invoices",
                description="List invoices in Stripe.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "customer": {
                            "type": "string",
                            "description": "The ID of the customer to list invoices for.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_invoice",
                description="Create an invoice in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["customer"],
                    "properties": {
                        "customer": {
                            "type": "string",
                            "description": "The ID of the customer to create the invoice for.",
                        },
                        "days_until_due": {
                            "type": "integer",
                            "description": "The number of days until the invoice is due.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_invoice_item",
                description="Create an invoice item in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["customer", "price", "invoice"],
                    "properties": {
                        "customer": {
                            "type": "string",
                            "description": "The ID of the customer to create the invoice item for.",
                        },
                        "price": {
                            "type": "string",
                            "description": "The ID of the price for the item.",
                        },
                        "invoice": {
                            "type": "string",
                            "description": "The ID of the invoice to create the item for.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_finalize_invoice",
                description="Finalize an invoice in Stripe.",
                inputSchema={
                    "type": "object",
                    "required": ["invoice"],
                    "properties": {
                        "invoice": {
                            "type": "string",
                            "description": "The ID of the invoice to finalize.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_create_billing_portal_session",
                description="Create a billing portal session.",
                inputSchema={
                    "type": "object",
                    "required": ["customer"],
                    "properties": {
                        "customer": {
                            "type": "string",
                            "description": "The ID of the customer to create the billing portal session for.",
                        },
                        "return_url": {
                            "type": "string",
                            "description": "The default URL to return to afterwards.",
                        },
                    },
                },
            ),
            types.Tool(
                name="stripe_retrieve_balance",
                description="Retrieve the balance from Stripe. It takes no input.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "stripe_create_customer":
            name_arg = arguments.get("name")
            email = arguments.get("email")
            if not name_arg:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            try:
                result = await create_customer(name_arg, email)
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
        
        elif name == "stripe_list_customers":
            limit = arguments.get("limit")
            email = arguments.get("email")
            try:
                result = await list_customers(limit, email)
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
        
        elif name == "stripe_create_product":
            name_arg = arguments.get("name")
            description = arguments.get("description")
            if not name_arg:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            try:
                result = await create_product(name_arg, description)
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
        
        elif name == "stripe_list_products":
            limit = arguments.get("limit")
            try:
                result = await list_products(limit)
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
        
        elif name == "stripe_create_price":
            product = arguments.get("product")
            unit_amount = arguments.get("unit_amount")
            currency = arguments.get("currency")
            if not all([product, unit_amount, currency]):
                return [
                    types.TextContent(
                        type="text",
                        text="Error: product, unit_amount, and currency parameters are required",
                    )
                ]
            try:
                result = await create_price(product, unit_amount, currency)
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
        
        elif name == "stripe_list_prices":
            product = arguments.get("product")
            limit = arguments.get("limit")
            try:
                result = await list_prices(product, limit)
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
        
        elif name == "stripe_create_payment_link":
            price = arguments.get("price")
            quantity = arguments.get("quantity")
            if not price or not quantity:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: price and quantity parameters are required",
                    )
                ]
            try:
                result = await create_payment_link(price, quantity)
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
        
        elif name == "stripe_list_payment_intents":
            customer = arguments.get("customer")
            limit = arguments.get("limit")
            try:
                result = await list_payment_intents(customer, limit)
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
        
        elif name == "stripe_create_refund":
            payment_intent = arguments.get("payment_intent")
            amount = arguments.get("amount")
            if not payment_intent:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: payment_intent parameter is required",
                    )
                ]
            try:
                result = await create_refund(payment_intent, amount)
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
        
        elif name == "stripe_list_invoices":
            customer = arguments.get("customer")
            limit = arguments.get("limit")
            try:
                result = await list_invoices(customer, limit)
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
        
        elif name == "stripe_create_invoice":
            customer = arguments.get("customer")
            days_until_due = arguments.get("days_until_due")
            if not customer:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer parameter is required",
                    )
                ]
            try:
                result = await create_invoice(customer, days_until_due)
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
        
        elif name == "stripe_create_invoice_item":
            customer = arguments.get("customer")
            price = arguments.get("price")
            invoice = arguments.get("invoice")
            if not all([customer, price, invoice]):
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer, price, and invoice parameters are required",
                    )
                ]
            try:
                result = await create_invoice_item(customer, price, invoice)
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
        
        elif name == "stripe_finalize_invoice":
            invoice = arguments.get("invoice")
            if not invoice:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: invoice parameter is required",
                    )
                ]
            try:
                result = await finalize_invoice(invoice)
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
        
        elif name == "stripe_create_billing_portal_session":
            customer = arguments.get("customer")
            return_url = arguments.get("return_url")
            if not customer:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer parameter is required",
                    )
                ]
            try:
                result = await create_billing_portal_session(customer, return_url)
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
        
        elif name == "stripe_retrieve_balance":
            try:
                result = await retrieve_balance()
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
        
        # Extract Stripe secret key from headers (allow None - will be handled at tool level)
        stripe_secret_key = request.headers.get('x-stripe-secret-key')
        
        # Set the Stripe secret key in context for this request (can be None)
        token = stripe_secret_key_context.set(stripe_secret_key or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            stripe_secret_key_context.reset(token)
        
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
        
        # Extract Stripe secret key from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        stripe_secret_key = headers.get(b'x-stripe-secret-key')
        if stripe_secret_key:
            stripe_secret_key = stripe_secret_key.decode('utf-8')
        
        # Set the Stripe secret key in context for this request (can be None/empty)
        token = stripe_secret_key_context.set(stripe_secret_key or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            stripe_secret_key_context.reset(token)

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