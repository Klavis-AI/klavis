import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

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
    auth_token_context,
    site_context,
    list_customers,
    get_customer,
    create_customer,
    update_customer,
    delete_customer,
    list_subscriptions,
    get_subscription,
    create_subscription,
    update_subscription,
    cancel_subscription,
    list_invoices,
    get_invoice,
    list_transactions,
    list_events,
    get_event,
    list_items,
    get_item,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CHARGEBEE_MCP_SERVER_PORT = int(os.getenv("CHARGEBEE_MCP_SERVER_PORT", "5000"))
CHARGEBEE_SITE = os.getenv("CHARGEBEE_SITE", "")


def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')

    if not auth_data:
        return ""

    try:
        # Parse the JSON auth data to extract access_token
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token') or auth_json.get('api_key') or auth_json.get('token') or ''
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""


def extract_site(request_or_scope) -> str:
    """Extract Chargebee site from x-auth-data header or environment."""
    site = os.getenv("CHARGEBEE_SITE", "")

    if site:
        return site

    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')

    if not auth_data:
        return ""

    try:
        auth_json = json.loads(auth_data)
        return auth_json.get('site') or ''
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""


@click.command()
@click.option("--port", default=CHARGEBEE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("chargebee-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Customers
            types.Tool(
                name="chargebee_list_customers",
                description="List all customers from Chargebee. Returns a paginated list of customers with their details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of customers to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "email": {
                            "type": "string",
                            "description": "Filter by exact email address.",
                        },
                        "first_name": {
                            "type": "string",
                            "description": "Filter by exact first name.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Filter by exact last name.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_CUSTOMER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_get_customer",
                description="Get detailed information for a specific customer from Chargebee.",
                inputSchema={
                    "type": "object",
                    "required": ["customer_id"],
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The unique identifier of the customer.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_CUSTOMER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_create_customer",
                description="Create a new customer in Chargebee.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "First name of the customer.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Last name of the customer.",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address of the customer.",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Phone number of the customer.",
                        },
                        "company": {
                            "type": "string",
                            "description": "Company name of the customer.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_CUSTOMER", "readOnlyHint": False}
                ),
            ),
            types.Tool(
                name="chargebee_update_customer",
                description="Update an existing customer's details in Chargebee.",
                inputSchema={
                    "type": "object",
                    "required": ["customer_id"],
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The unique identifier of the customer to update.",
                        },
                        "first_name": {
                            "type": "string",
                            "description": "First name of the customer.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Last name of the customer.",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address of the customer.",
                        },
                        "phone": {
                            "type": "string",
                            "description": "Phone number of the customer.",
                        },
                        "company": {
                            "type": "string",
                            "description": "Company name of the customer.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_CUSTOMER", "readOnlyHint": False}
                ),
            ),
            types.Tool(
                name="chargebee_delete_customer",
                description="Delete a customer from Chargebee. This will also delete all subscriptions, invoices, and other data associated with the customer.",
                inputSchema={
                    "type": "object",
                    "required": ["customer_id"],
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The unique identifier of the customer to delete.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_CUSTOMER", "readOnlyHint": False}
                ),
            ),
            # Subscriptions
            types.Tool(
                name="chargebee_list_subscriptions",
                description="List all subscriptions from Chargebee with optional filters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of subscriptions to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Filter by customer ID.",
                        },
                        "plan_id": {
                            "type": "string",
                            "description": "Filter by plan ID.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (active, cancelled, non_renewing, future, in_trial, paused).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_SUBSCRIPTION", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_get_subscription",
                description="Get detailed information for a specific subscription from Chargebee.",
                inputSchema={
                    "type": "object",
                    "required": ["subscription_id"],
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The unique identifier of the subscription.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_SUBSCRIPTION", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_create_subscription",
                description="Create a new subscription for a customer in Chargebee (Product Catalog 2.0).",
                inputSchema={
                    "type": "object",
                    "required": ["customer_id", "item_price_id"],
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "The unique identifier of the customer.",
                        },
                        "item_price_id": {
                            "type": "string",
                            "description": "The item price ID to subscribe the customer to.",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity of the item (default 1).",
                        },
                        "start_date": {
                            "type": "integer",
                            "description": "Start date of the subscription (Unix timestamp).",
                        },
                        "trial_end": {
                            "type": "integer",
                            "description": "End date of the trial period (Unix timestamp).",
                        },
                        "billing_cycles": {
                            "type": "integer",
                            "description": "Number of billing cycles for the subscription.",
                        },
                        "auto_collection": {
                            "type": "string",
                            "description": "Auto collection mode (on or off).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_SUBSCRIPTION", "readOnlyHint": False}
                ),
            ),
            types.Tool(
                name="chargebee_update_subscription",
                description="Update an existing subscription in Chargebee (Product Catalog 2.0).",
                inputSchema={
                    "type": "object",
                    "required": ["subscription_id"],
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The unique identifier of the subscription to update.",
                        },
                        "item_price_id": {
                            "type": "string",
                            "description": "The new item price ID for the subscription.",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "New quantity of the item.",
                        },
                        "start_date": {
                            "type": "integer",
                            "description": "New start date of the subscription (Unix timestamp).",
                        },
                        "trial_end": {
                            "type": "integer",
                            "description": "New end date of the trial period (Unix timestamp).",
                        },
                        "billing_cycles": {
                            "type": "integer",
                            "description": "New number of billing cycles for the subscription.",
                        },
                        "auto_collection": {
                            "type": "string",
                            "description": "Auto collection mode (on or off).",
                        },
                        "po_number": {
                            "type": "string",
                            "description": "Purchase order number for the subscription.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_SUBSCRIPTION", "readOnlyHint": False}
                ),
            ),
            types.Tool(
                name="chargebee_cancel_subscription",
                description="Cancel a subscription in Chargebee. Can cancel immediately or at end of term.",
                inputSchema={
                    "type": "object",
                    "required": ["subscription_id"],
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The unique identifier of the subscription to cancel.",
                        },
                        "end_of_term": {
                            "type": "boolean",
                            "description": "If true, the subscription will be cancelled at the end of the current term. If false, cancelled immediately.",
                        },
                        "cancel_at": {
                            "type": "integer",
                            "description": "Specific timestamp to cancel the subscription (Unix timestamp).",
                        },
                        "credit_option_for_current_term_charges": {
                            "type": "string",
                            "description": "How to handle current term charges (none, prorate, full).",
                        },
                        "unbilled_charges_option": {
                            "type": "string",
                            "description": "How to handle unbilled charges (invoice, delete).",
                        },
                        "cancel_reason_code": {
                            "type": "string",
                            "description": "Reason code for cancellation.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_SUBSCRIPTION", "readOnlyHint": False}
                ),
            ),
            # Invoices
            types.Tool(
                name="chargebee_list_invoices",
                description="List all invoices from Chargebee with optional filters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of invoices to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Filter by customer ID.",
                        },
                        "subscription_id": {
                            "type": "string",
                            "description": "Filter by subscription ID.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (paid, posted, payment_due, not_paid, voided, pending).",
                        },
                        "paid_at_after": {
                            "type": "integer",
                            "description": "Filter invoices paid after this timestamp (Unix epoch).",
                        },
                        "paid_at_before": {
                            "type": "integer",
                            "description": "Filter invoices paid before this timestamp (Unix epoch).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_INVOICE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_get_invoice",
                description="Get detailed information for a specific invoice from Chargebee.",
                inputSchema={
                    "type": "object",
                    "required": ["invoice_id"],
                    "properties": {
                        "invoice_id": {
                            "type": "string",
                            "description": "The unique identifier of the invoice.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_INVOICE", "readOnlyHint": True}
                ),
            ),
            # Transactions
            types.Tool(
                name="chargebee_list_transactions",
                description="List all payment transactions from Chargebee with optional filters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of transactions to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Filter by customer ID.",
                        },
                        "subscription_id": {
                            "type": "string",
                            "description": "Filter by subscription ID.",
                        },
                        "payment_source_id": {
                            "type": "string",
                            "description": "Filter by payment source ID.",
                        },
                        "payment_method": {
                            "type": "string",
                            "description": "Filter by payment method (card, cash, check, bank_transfer, etc.).",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (success, voided, failure, timeout, needs_attention).",
                        },
                        "date_after": {
                            "type": "integer",
                            "description": "Filter transactions after this timestamp (Unix epoch).",
                        },
                        "date_before": {
                            "type": "integer",
                            "description": "Filter transactions before this timestamp (Unix epoch).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_TRANSACTION", "readOnlyHint": True}
                ),
            ),
            # Events
            types.Tool(
                name="chargebee_list_events",
                description="List all events from Chargebee. Events are useful for syncing data and tracking changes in your Chargebee account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of events to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "event_type": {
                            "type": "string",
                            "description": "Filter by event type (e.g., customer_created, subscription_created, invoice_generated, payment_succeeded).",
                        },
                        "occurred_at_after": {
                            "type": "integer",
                            "description": "Filter events that occurred after this timestamp (Unix epoch).",
                        },
                        "occurred_at_before": {
                            "type": "integer",
                            "description": "Filter events that occurred before this timestamp (Unix epoch).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_EVENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_get_event",
                description="Get detailed information for a specific event from Chargebee.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The unique identifier of the event.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_EVENT", "readOnlyHint": True}
                ),
            ),
            # Items (Product Catalog 2.0)
            types.Tool(
                name="chargebee_list_items",
                description="List all items (plans, addons, charges) from Chargebee Product Catalog 2.0.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of items to return (max 100, default 10).",
                        },
                        "offset": {
                            "type": "string",
                            "description": "Offset for pagination (use next_offset from previous response).",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (active, archived).",
                        },
                        "item_type": {
                            "type": "string",
                            "description": "Filter by item type (plan, addon, charge).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_ITEM", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="chargebee_get_item",
                description="Get detailed information for a specific item from Chargebee Product Catalog 2.0.",
                inputSchema={
                    "type": "object",
                    "required": ["item_id"],
                    "properties": {
                        "item_id": {
                            "type": "string",
                            "description": "The unique identifier of the item.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CHARGEBEE_ITEM", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        # Customers
        if name == "chargebee_list_customers":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            email = arguments.get("email")
            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")

            try:
                result = await list_customers(
                    limit=limit,
                    offset=offset,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_get_customer":
            customer_id = arguments.get("customer_id")
            if not customer_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer_id parameter is required",
                    )
                ]

            try:
                result = await get_customer(customer_id=customer_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_create_customer":
            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")
            email = arguments.get("email")
            phone = arguments.get("phone")
            company = arguments.get("company")

            try:
                result = await create_customer(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    company=company,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_update_customer":
            customer_id = arguments.get("customer_id")
            if not customer_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer_id parameter is required",
                    )
                ]

            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")
            email = arguments.get("email")
            phone = arguments.get("phone")
            company = arguments.get("company")

            try:
                result = await update_customer(
                    customer_id=customer_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    company=company,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_delete_customer":
            customer_id = arguments.get("customer_id")
            if not customer_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer_id parameter is required",
                    )
                ]

            try:
                result = await delete_customer(customer_id=customer_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        # Subscriptions
        elif name == "chargebee_list_subscriptions":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            customer_id = arguments.get("customer_id")
            plan_id = arguments.get("plan_id")
            status = arguments.get("status")

            try:
                result = await list_subscriptions(
                    limit=limit,
                    offset=offset,
                    customer_id=customer_id,
                    plan_id=plan_id,
                    status=status,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_get_subscription":
            subscription_id = arguments.get("subscription_id")
            if not subscription_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: subscription_id parameter is required",
                    )
                ]

            try:
                result = await get_subscription(subscription_id=subscription_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_create_subscription":
            customer_id = arguments.get("customer_id")
            item_price_id = arguments.get("item_price_id")
            if not customer_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: customer_id parameter is required",
                    )
                ]
            if not item_price_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: item_price_id parameter is required",
                    )
                ]

            quantity = arguments.get("quantity")
            start_date = arguments.get("start_date")
            trial_end = arguments.get("trial_end")
            billing_cycles = arguments.get("billing_cycles")
            auto_collection = arguments.get("auto_collection")

            try:
                result = await create_subscription(
                    customer_id=customer_id,
                    item_price_id=item_price_id,
                    quantity=quantity,
                    start_date=start_date,
                    trial_end=trial_end,
                    billing_cycles=billing_cycles,
                    auto_collection=auto_collection,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_update_subscription":
            subscription_id = arguments.get("subscription_id")
            if not subscription_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: subscription_id parameter is required",
                    )
                ]

            item_price_id = arguments.get("item_price_id")
            quantity = arguments.get("quantity")
            start_date = arguments.get("start_date")
            trial_end = arguments.get("trial_end")
            billing_cycles = arguments.get("billing_cycles")
            auto_collection = arguments.get("auto_collection")
            po_number = arguments.get("po_number")

            try:
                result = await update_subscription(
                    subscription_id=subscription_id,
                    item_price_id=item_price_id,
                    quantity=quantity,
                    start_date=start_date,
                    trial_end=trial_end,
                    billing_cycles=billing_cycles,
                    auto_collection=auto_collection,
                    po_number=po_number,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_cancel_subscription":
            subscription_id = arguments.get("subscription_id")
            if not subscription_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: subscription_id parameter is required",
                    )
                ]

            end_of_term = arguments.get("end_of_term")
            cancel_at = arguments.get("cancel_at")
            credit_option_for_current_term_charges = arguments.get("credit_option_for_current_term_charges")
            unbilled_charges_option = arguments.get("unbilled_charges_option")
            cancel_reason_code = arguments.get("cancel_reason_code")

            try:
                result = await cancel_subscription(
                    subscription_id=subscription_id,
                    end_of_term=end_of_term,
                    cancel_at=cancel_at,
                    credit_option_for_current_term_charges=credit_option_for_current_term_charges,
                    unbilled_charges_option=unbilled_charges_option,
                    cancel_reason_code=cancel_reason_code,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        # Invoices
        elif name == "chargebee_list_invoices":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            customer_id = arguments.get("customer_id")
            subscription_id = arguments.get("subscription_id")
            status = arguments.get("status")
            paid_at_after = arguments.get("paid_at_after")
            paid_at_before = arguments.get("paid_at_before")

            try:
                result = await list_invoices(
                    limit=limit,
                    offset=offset,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    status=status,
                    paid_at_after=paid_at_after,
                    paid_at_before=paid_at_before,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_get_invoice":
            invoice_id = arguments.get("invoice_id")
            if not invoice_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: invoice_id parameter is required",
                    )
                ]

            try:
                result = await get_invoice(invoice_id=invoice_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        # Transactions
        elif name == "chargebee_list_transactions":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            customer_id = arguments.get("customer_id")
            subscription_id = arguments.get("subscription_id")
            payment_source_id = arguments.get("payment_source_id")
            payment_method = arguments.get("payment_method")
            status = arguments.get("status")
            date_after = arguments.get("date_after")
            date_before = arguments.get("date_before")

            try:
                result = await list_transactions(
                    limit=limit,
                    offset=offset,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    payment_source_id=payment_source_id,
                    payment_method=payment_method,
                    status=status,
                    date_after=date_after,
                    date_before=date_before,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        # Events
        elif name == "chargebee_list_events":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            event_type = arguments.get("event_type")
            occurred_at_after = arguments.get("occurred_at_after")
            occurred_at_before = arguments.get("occurred_at_before")

            try:
                result = await list_events(
                    limit=limit,
                    offset=offset,
                    event_type=event_type,
                    occurred_at_after=occurred_at_after,
                    occurred_at_before=occurred_at_before,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_get_event":
            event_id = arguments.get("event_id")
            if not event_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: event_id parameter is required",
                    )
                ]

            try:
                result = await get_event(event_id=event_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        # Items (Product Catalog 2.0)
        elif name == "chargebee_list_items":
            limit = arguments.get("limit")
            offset = arguments.get("offset")
            status = arguments.get("status")
            item_type = arguments.get("item_type")

            try:
                result = await list_items(
                    limit=limit,
                    offset=offset,
                    status=status,
                    item_type=item_type,
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        elif name == "chargebee_get_item":
            item_id = arguments.get("item_id")
            if not item_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: item_id parameter is required",
                    )
                ]

            try:
                result = await get_item(item_id=item_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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

        else:
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

        # Extract auth token and site from headers
        auth_token = extract_access_token(request)
        site = extract_site(request)

        # Set the auth token and site in context for this request
        token_ctx = auth_token_context.set(auth_token)
        site_ctx = site_context.set(site)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token_ctx)
            site_context.reset(site_ctx)

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

        # Extract auth token and site from headers
        auth_token = extract_access_token(scope)
        site = extract_site(scope)

        # Set the auth token and site in context for this request
        token_ctx = auth_token_context.set(auth_token)
        site_ctx = site_context.set(site)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token_ctx)
            site_context.reset(site_ctx)

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
