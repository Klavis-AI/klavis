#!/usr/bin/env python3

import contextlib
import os
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Dict, List, Sequence, Optional

import click
import stripe
from dotenv import load_dotenv

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import AnyUrl

from tools import get_stripe_tools

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stripe-mcp-server")

# Stripe API constants and configuration
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
if not STRIPE_API_KEY:
    raise ValueError("STRIPE_API_KEY environment variable is required")

STRIPE_MCP_SERVER_PORT = int(os.getenv("STRIPE_MCP_SERVER_PORT", "5002"))

# Initialize Stripe
stripe.api_key = STRIPE_API_KEY

def custom_json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, stripe.StripeObject):
        return json.loads(str(obj))
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Stripe Manager class
class StripeManager:
    def __init__(self):
        logger.info("🔄 Initializing StripeManager")
        self.audit_entries = []  # MUST be first line in __init__
        
        # Verify API key works
        logger.info("✅ Stripe configured")
        logger.debug("Test connection...")
        try:
            stripe.Customer.list(limit=1)
        except stripe.error.AuthenticationError as e:
            logger.critical("🔴 Invalid API key: %s", e)
            raise

    def log_operation(self, operation: str, parameters: dict) -> None:
        """Log all Stripe operations for audit purposes."""
        logger.debug("📝 Logging operation: %s with params: %s", operation, parameters)
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "parameters": parameters
        }
        self.audit_entries.append(audit_entry)

    def _synthesize_audit_log(self) -> str:
        """Generate a human-readable audit log of all operations."""
        logger.debug("Generating audit log with %d entries", len(self.audit_entries))
        if not self.audit_entries:
            return "No Stripe operations performed yet."
        
        report = "📋 Stripe Operations Audit Log 📋\n\n"
        for entry in self.audit_entries:
            report += f"[{entry['timestamp']}]\n"
            report += f"Operation: {entry['operation']}\n"
            report += f"Parameters: {json.dumps(entry['parameters'], indent=2)}\n"
            report += "-" * 50 + "\n"
        return report

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

    # Create the Stripe manager
    manager = StripeManager()
    
    # Create the MCP server instance
    app = Server("stripe-mcp-server")

    @app.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl("audit://stripe-operations"),
                name="Stripe Operations Audit Log",
                description="Log of all Stripe operations performed",
                mimeType="text/plain",
            )
        ]

    @app.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        if uri.scheme != "audit":
            raise ValueError("Unsupported URI scheme")
        return manager._synthesize_audit_log()

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return get_stripe_tools()

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        logger.debug("=== RECEIVED JSON-RPC callTool request ===")
        
        try:
            if name.startswith("customer_"):
                result = await handle_customer_operations(manager, name, arguments)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            elif name.startswith("payment_"):
                result = await handle_payment_operations(manager, name, arguments)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            elif name.startswith("refund_"):
                result = await handle_refund_operations(manager, name, arguments)
                return [
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}",
                    )
                ]
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Payment processing failed: {str(e)}",
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

    async def handle_customer_operations(manager, name: str, args: dict) -> str:
        """Handle customer-related operations."""
        if name == "customer_create":
            customer = stripe.Customer.create(
                email=args["email"],
                name=args.get("name"),
                metadata=args.get("metadata", {})
            )
            manager.log_operation("customer_create", args)
            return json.dumps(customer, default=custom_json_serializer)
        
        elif name == "customer_retrieve":
            customer = stripe.Customer.retrieve(args["customer_id"])
            return json.dumps(customer, default=custom_json_serializer)
        
        elif name == "customer_update":
            customer = stripe.Customer.modify(
                args["customer_id"],
                **args["update_fields"]
            )
            manager.log_operation("customer_update", args)
            return json.dumps(customer, default=custom_json_serializer)
        
        raise ValueError(f"Unknown customer operation: {name}")

    async def handle_payment_operations(manager, name: str, args: dict) -> str:
        """Handle payment-related operations."""
        if name == "payment_intent_create":
            intent = stripe.PaymentIntent.create(
                amount=args["amount"],
                currency=args["currency"],
                payment_method_types=args.get("payment_method_types", ["card"]),
                customer=args.get("customer"),
                metadata=args.get("metadata", {})
            )
            manager.log_operation("payment_intent_create", args)
            return json.dumps(intent, default=custom_json_serializer)
        
        elif name == "charge_list":
            charges = stripe.Charge.list(
                limit=args.get("limit", 10),
                customer=args.get("customer_id")
            )
            return json.dumps(charges, default=custom_json_serializer)
        
        raise ValueError(f"Unknown payment operation: {name}")

    async def handle_refund_operations(manager, name: str, args: dict) -> str:
        """Handle refund-related operations."""
        if name == "refund_create":
            refund = stripe.Refund.create(
                charge=args["charge_id"],
                amount=args.get("amount"),
                reason=args.get("reason", "requested_by_customer")
            )
            manager.log_operation("refund_create", args)
            return json.dumps(refund, default=custom_json_serializer)
        
        raise ValueError(f"Unknown refund operation: {name}")

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
