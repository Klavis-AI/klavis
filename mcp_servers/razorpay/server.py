import os
import json
import logging
import asyncio
from typing import Any, Dict

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from tools import (
    key_id_context,
    key_secret_context,
    fetch_order_by_id,
    create_order,
    update_order,
    fetch_all_orders,
    fetch_payments_by_order_id,
    capture_payment,
    update_payment,
    fetch_payment_by_id,
    fetch_all_payments,
    fetch_card_details_of_payment,
    create_QR_code,
    cancel_payment_link,
    close_QR_code,
    fetch_QR_code_by_id,
    update_QR_code,
    fetch_all_QR_codes,
    fetch_payment_downtime_details,
    fetch_all_customers,
    fetch_all_payment_links,
    fetch_customer_by_id,
    fetch_document_content,
    fetch_document_information,
    fetch_payment_downtime_details_with_id,
    fetch_payment_links_with_id,
    send_or_resend_payment_link_notifications,
    create_payment_link,
    create_customer,
    edit_customer_details,
    update_payment_link,
)

# Load env early
load_dotenv()

logger = logging.getLogger("razorpay-mcp-server")
logging.basicConfig(level=logging.INFO)

# Load credentials from environment
RAZORPAY_API_ID = os.getenv("RAZORPAY_API_ID") or ""
RAZORPAY_API_SECRET = os.getenv("RAZORPAY_API_SECRET") or ""


async def run_server(log_level: str = "INFO"):
    """Run the Razorpay MCP server with stdio transport."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Set API keys in context from environment variables
    if RAZORPAY_API_ID and RAZORPAY_API_SECRET:
        key_id_context.set(RAZORPAY_API_ID)
        key_secret_context.set(RAZORPAY_API_SECRET)
        logger.info("Razorpay API credentials configured from environment")
    else:
        logger.warning("Razorpay API credentials not found in environment. Tools may fail.")

    app = Server("razorpay")

    # ----------------------------- Tool Registry -----------------------------#
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available Razorpay tools."""
        tools = [
            # --- Order Tools ---
            types.Tool(
                name="razorpay_create_order",
                description="Creates a new Razorpay Order.",
                inputSchema={
                    "type": "object",
                    "required": ["amount", "currency"],
                    "properties": {
                        "amount": {"type": "integer", "description": "Amount in the smallest currency unit (e.g., 50000 for ₹500.00)."},
                        "currency": {"type": "string", "description": "3-letter ISO currency code (e.g., 'INR')."},
                        "receipt": {"type": "string", "description": "A unique receipt ID for your reference (max 40 chars)."},
                        "notes": {"type": "object", "description": "Key-value pairs for additional information."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_ORDERS"}),
            ),
            types.Tool(
                name="razorpay_update_order",
                description="Updates the notes for an existing order.",
                inputSchema={
                    "type": "object", "required": ["order_id", "notes"],
                    "properties": {
                        "order_id": {"type": "string", "description": "The unique ID of the order to update."},
                        "notes": {"type": "object", "description": "The key-value pairs to set as notes."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_ORDERS"}),
            ),
            types.Tool(
                name="razorpay_fetch_all_orders",
                description="Fetches a list of Razorpay Orders based on specified criteria.",
                inputSchema={
                    "type": "object", "properties": {
                        "from_ts": {"type": "integer", "description": "Start Unix timestamp."},
                        "to_ts": {"type": "integer", "description": "End Unix timestamp."},
                        "count": {"type": "integer", "description": "Number of orders to fetch (default 10, max 100)."},
                        "skip": {"type": "integer", "description": "Number of orders to skip for pagination."},
                        "authorized": {"type": "boolean", "description": "Filter for authorized (true) or unauthorized (false) orders."},
                        "receipt": {"type": "string", "description": "Filter by a specific receipt ID."},
                        "expand": {"type": "array", "items": {"type": "string"}, "description": "Sub-entities to expand (e.g., 'payments')."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_ORDERS"}),
            ),
            types.Tool(
                name="razorpay_fetch_order_by_id",
                description="Fetches a single order by its unique ID.",
                inputSchema={"type": "object", "required": ["order_id"], "properties": {"order_id": {"type": "string", "description": "The ID of the order to fetch."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_ORDERS"}),
            ),
            types.Tool(
                name="razorpay_fetch_payments_by_order_id",
                description="Fetches all payments associated with a specific order ID.",
                inputSchema={"type": "object", "required": ["order_id"], "properties": {"order_id": {"type": "string", "description": "The ID of the order."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_ORDERS"}),
            ),

            # --- Customer Tools ---
            types.Tool(
                name="razorpay_create_customer",
                description="Creates a new Razorpay Customer.",
                inputSchema={
                    "type": "object", "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "description": "Customer's name (3-50 characters)."},
                        "email": {"type": "string", "description": "Customer's email address."},
                        "contact": {"type": "string", "description": "Customer's phone number."},
                        "gstin": {"type": "string", "description": "Customer's GST number."},
                        "fail_existing": {"type": "string", "enum": ["0", "1"], "description": "'1' to error on duplicates, '0' to fetch existing."},
                        "notes": {"type": "object", "description": "Key-value pairs for additional information."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_CUSTOMERS"}),
            ),
            types.Tool(
                name="razorpay_edit_customer_details",
                description="Edits a customer's details by their ID.",
                inputSchema={
                    "type": "object", "required": ["customer_id"],
                    "properties": {
                        "customer_id": {"type": "string", "description": "The unique ID of the customer to edit."},
                        "name": {"type": "string", "description": "Customer's new name."},
                        "email": {"type": "string", "description": "Customer's new email."},
                        "contact": {"type": "string", "description": "Customer's new contact number."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_CUSTOMERS"}),
            ),
            types.Tool(
                name="razorpay_fetch_all_customers",
                description="Fetches a list of all customers.",
                inputSchema={
                    "type": "object", "properties": {
                        "count": {"type": "integer", "description": "Number of customers to fetch (default 10, max 100)."},
                        "skip": {"type": "integer", "description": "Number of customers to skip for pagination."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_CUSTOMERS"}),
            ),
            types.Tool(
                name="razorpay_fetch_customer_by_id",
                description="Fetches a single customer by their unique ID.",
                inputSchema={"type": "object", "required": ["customer_id"], "properties": {"customer_id": {"type": "string", "description": "The ID of the customer to fetch."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_CUSTOMERS"}),
            ),
            
            # --- Payment Tools ---
            types.Tool(
                name="razorpay_capture_payment",
                description="Captures a previously authorized payment.",
                inputSchema={
                    "type": "object", "required": ["payment_id", "amount", "currency"],
                    "properties": {
                        "payment_id": {"type": "string", "description": "The unique ID of the payment to capture."},
                        "amount": {"type": "integer", "description": "Amount to capture in the smallest currency unit."},
                        "currency": {"type": "string", "description": "3-letter ISO currency code."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENTS"}),
            ),
            types.Tool(
                name="razorpay_update_payment",
                description="Updates the notes for an existing payment.",
                inputSchema={
                    "type": "object", "required": ["payment_id", "notes"],
                    "properties": {
                        "payment_id": {"type": "string", "description": "The unique ID of the payment to update."},
                        "notes": {"type": "object", "description": "Key-value pairs to set as notes."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENTS"}),
            ),
            types.Tool(
                name="razorpay_fetch_all_payments",
                description="Fetches a list of payments.",
                inputSchema={
                    "type": "object", "properties": {
                        "from_ts": {"type": "integer", "description": "Start Unix timestamp."},
                        "to_ts": {"type": "integer", "description": "End Unix timestamp."},
                        "count": {"type": "integer", "description": "Number of payments to fetch (default 10, max 100)."},
                        "skip": {"type": "integer", "description": "Number of payments to skip for pagination."},
                        "expand": {"type": "array", "items": {"type": "string", "enum": ['card', 'emi', 'transaction']}, "description": "Sub-entities to expand (e.g., 'card')."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENTS"}),
            ),
            types.Tool(
                name="razorpay_fetch_payment_by_id",
                description="Fetches a single payment by its unique ID.",
                inputSchema={
                    "type": "object", "required": ["payment_id"],
                    "properties": {
                        "payment_id": {"type": "string", "description": "The ID of the payment to fetch."},
                        "expand": {"type": "array", "items": {"type": "string", "enum": ['card', 'emi', 'transaction']}, "description": "Sub-entities to expand."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENTS"}),
            ),
            types.Tool(
                name="razorpay_fetch_card_details_of_payment",
                description="Fetches the card details for a specific payment.",
                inputSchema={"type": "object", "required": ["payment_id"], "properties": {"payment_id": {"type": "string", "description": "The ID of the payment."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENTS"}),
            ),

            # --- QR Code Tools ---
            types.Tool(
                name="razorpay_create_QR_code",
                description="Creates a new Razorpay QR Code.",
                inputSchema={
                    "type": "object", "required": ["type", "usage"],
                    "properties": {
                        "type": {"type": "string", "enum": ["upi_qr"], "description": "Type of QR Code. Must be 'upi_qr'."},
                        "usage": {"type": "string", "enum": ["single_use", "multiple_use"], "description": "Usage type."},
                        "name": {"type": "string", "description": "Name or label for the QR Code."},
                        "fixed_amount": {"type": "boolean", "description": "If the QR code is for a fixed amount."},
                        "payment_amount": {"type": "integer", "description": "The fixed amount in currency subunits."},
                        "description": {"type": "string", "description": "A description for the QR Code."},
                        "customer_id": {"type": "string", "description": "ID of the customer it is assigned to."},
                        "close_by": {"type": "integer", "description": "Unix timestamp for expiry (single_use only)."},
                        "notes": {"type": "object", "description": "Key-value pairs for additional information."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_QR_CODES"}),
            ),
            types.Tool(
                name="razorpay_close_QR_code",
                description="Closes an active QR code.",
                inputSchema={"type": "object", "required": ["qr_id"], "properties": {"qr_id": {"type": "string", "description": "The ID of the QR code to close."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_QR_CODES"}),
            ),
            types.Tool(
                name="razorpay_fetch_all_QR_codes",
                description="Fetches a list of all QR codes.",
                inputSchema={
                    "type": "object", "properties": {
                        "from_ts": {"type": "integer", "description": "Start Unix timestamp."},
                        "to_ts": {"type": "integer", "description": "End Unix timestamp."},
                        "count": {"type": "integer", "description": "Number of codes to fetch (default 10, max 100)."},
                        "skip": {"type": "integer", "description": "Number of codes to skip for pagination."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_QR_CODES"}),
            ),
            types.Tool(
                name="razorpay_fetch_QR_code_by_id",
                description="Fetches a single QR code by its unique ID.",
                inputSchema={"type": "object", "required": ["qr_id"], "properties": {"qr_id": {"type": "string", "description": "The ID of the QR code to fetch."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_QR_CODES"}),
            ),
            types.Tool(
                name="razorpay_update_QR_code",
                description="Updates the notes for an existing QR code.",
                inputSchema={
                    "type": "object", "required": ["qr_id", "notes"],
                    "properties": {
                        "qr_id": {"type": "string", "description": "The unique ID of the QR code to update."},
                        "notes": {"type": "object", "description": "Key-value pairs to set as notes."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_QR_CODES"}),
            ),

            # --- Payment Link Tools ---
            types.Tool(
                name="razorpay_create_payment_link",
                description="Creates a new Razorpay Payment Link.",
                inputSchema={
                    "type": "object", "required": ["amount", "description"],
                    "properties": {
                        "amount": {"type": "integer", "description": "Amount in the smallest currency unit."},
                        "description": {"type": "string", "description": "A description for the payment link."},
                        "currency": {"type": "string", "description": "3-letter ISO currency code (defaults to 'INR')."},
                        "accept_partial": {"type": "boolean", "description": "If partial payments are allowed."},
                        "first_min_partial_amount": {"type": "integer", "description": "The minimum first partial payment amount."},
                        "upi_link": {"type": "boolean", "description": "True to create a UPI Payment Link."},
                        "customer": {"type": "object", "properties": {"name": {"type": "string"}, "email": {"type": "string"}, "contact": {"type": "string"}}},
                        "expire_by": {"type": "integer", "description": "Unix timestamp for link expiry."},
                        "reference_id": {"type": "string", "description": "A unique reference ID."},
                        "notify": {"type": "object", "properties": {"sms": {"type": "boolean"}, "email": {"type": "boolean"}}},
                        "reminder_enable": {"type": "boolean", "description": "To enable payment reminders."},
                        "notes": {"type": "object", "description": "Key-value pairs for additional information."},
                        "callback_url": {"type": "string", "description": "URL to redirect to after payment."},
                        "callback_method": {"type": "string", "enum": ["get"], "description": "Must be 'get' if callback_url is provided."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),
            types.Tool(
                name="razorpay_update_payment_link",
                description="Updates an existing Payment Link.",
                inputSchema={
                    "type": "object", "required": ["payment_link_id"],
                    "properties": {
                        "payment_link_id": {"type": "string", "description": "The ID of the payment link to update."},
                        "reference_id": {"type": "string", "description": "New reference ID."},
                        "expire_by": {"type": "integer", "description": "New expiry timestamp."},
                        "notes": {"type": "object", "description": "New notes object."},
                        "accept_partial": {"type": "boolean", "description": "New value for accepting partial payments."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),
            types.Tool(
                name="razorpay_fetch_all_payment_links",
                description="Fetches a list of all payment links, with optional filters.",
                inputSchema={
                    "type": "object", "properties": {
                        "payment_id": {"type": "string", "description": "Filter by payment ID."},
                        "reference_id": {"type": "string", "description": "Filter by reference ID."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),
            types.Tool(
                name="razorpay_fetch_payment_links_with_id",
                description="Fetches a single payment link by its unique ID.",
                inputSchema={"type": "object", "required": ["payment_link_id"], "properties": {"payment_link_id": {"type": "string", "description": "The ID of the payment link to fetch."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),
            types.Tool(
                name="razorpay_send_or_resend_payment_link_notifications",
                description="Sends or resends a notification for a payment link.",
                inputSchema={
                    "type": "object", "required": ["payment_link_id", "medium"],
                    "properties": {
                        "payment_link_id": {"type": "string", "description": "The ID of the payment link."},
                        "medium": {"type": "string", "enum": ["sms", "email"], "description": "Notification medium."},
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),
            types.Tool(
                name="razorpay_cancel_payment_link",
                description="Cancels an active payment link.",
                inputSchema={"type": "object", "required": ["payment_link_id"], "properties": {"payment_link_id": {"type": "string", "description": "The ID of the payment link to cancel."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_PAYMENT_LINKS"}),
            ),

            # --- Downtime Tools ---
            types.Tool(
                name="razorpay_fetch_payment_downtime_details",
                description="Fetches details of all payment downtimes.",
                inputSchema={"type": "object", "properties": {}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_DOWNTIMES"}),
            ),
            types.Tool(
                name="razorpay_fetch_payment_downtime_details_with_id",
                description="Fetches downtime status for a specific payment ID.",
                inputSchema={"type": "object", "required": ["payment_id"], "properties": {"payment_id": {"type": "string", "description": "The ID of the payment to check."}}},
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_DOWNTIMES"}),
            ),

            # --- Document Tools ---
            types.Tool(
                name="razorpay_fetch_document_information",
                description="Retrieves the details of a previously uploaded document.",
                inputSchema={
                    "type": "object", "required": ["document_id"],
                    "properties": {"document_id": {"type": "string", "description": "The ID of the document to fetch."}},
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_DOCUMENTS"}),
            ),
            types.Tool(
                name="razorpay_fetch_document_content",
                description="Downloads the content of a previously uploaded document.",
                inputSchema={
                    "type": "object", "required": ["document_id"],
                    "properties": {"document_id": {"type": "string", "description": "The ID of the document to download."}},
                },
                annotations=types.ToolAnnotations(**{"category": "RAZORPAY_DOCUMENTS"}),
            ),
        ]
        logger.info(f"Returning {len(tools)} tools")
        return tools

    # ---------------------------- Tool Dispatcher ----------------------------#
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        logger.info(f"Calling tool: {name}")

        try:
            result = {}
            # --- Order Tools ---
            if name == "razorpay_create_order":
                if not all(k in arguments for k in ["amount", "currency"]):
                    raise ValueError("Missing required arguments: amount and currency")
                result = await create_order(**arguments)
            elif name == "razorpay_update_order":
                if not all(k in arguments for k in ["order_id", "notes"]):
                    raise ValueError("Missing required arguments: order_id and notes")
                result = await update_order(**arguments)
            elif name == "razorpay_fetch_all_orders":
                result = await fetch_all_orders(**arguments)
            elif name == "razorpay_fetch_order_by_id":
                if "order_id" not in arguments:
                    raise ValueError("Missing required argument: order_id")
                result = await fetch_order_by_id(**arguments)
            elif name == "razorpay_fetch_payments_by_order_id":
                if "order_id" not in arguments:
                    raise ValueError("Missing required argument: order_id")
                result = await fetch_payments_by_order_id(**arguments)

            # --- Customer Tools ---
            elif name == "razorpay_create_customer":
                if "name" not in arguments:
                    raise ValueError("Missing required argument: name")
                result = await create_customer(**arguments)
            elif name == "razorpay_edit_customer_details":
                if "customer_id" not in arguments:
                    raise ValueError("Missing required argument: customer_id")
                result = await edit_customer_details(**arguments)
            elif name == "razorpay_fetch_all_customers":
                result = await fetch_all_customers(**arguments)
            elif name == "razorpay_fetch_customer_by_id":
                if "customer_id" not in arguments:
                    raise ValueError("Missing required argument: customer_id")
                result = await fetch_customer_by_id(**arguments)

            # --- Payment Tools ---
            elif name == "razorpay_capture_payment":
                if not all(k in arguments for k in ["payment_id", "amount", "currency"]):
                    raise ValueError("Missing required arguments: payment_id, amount, and currency")
                result = await capture_payment(**arguments)
            elif name == "razorpay_update_payment":
                if not all(k in arguments for k in ["payment_id", "notes"]):
                    raise ValueError("Missing required arguments: payment_id and notes")
                result = await update_payment(**arguments)
            elif name == "razorpay_fetch_all_payments":
                result = await fetch_all_payments(**arguments)
            elif name == "razorpay_fetch_payment_by_id":
                if "payment_id" not in arguments:
                    raise ValueError("Missing required argument: payment_id")
                result = await fetch_payment_by_id(**arguments)
            elif name == "razorpay_fetch_card_details_of_payment":
                if "payment_id" not in arguments:
                    raise ValueError("Missing required argument: payment_id")
                result = await fetch_card_details_of_payment(**arguments)

            # --- QR Code Tools ---
            elif name == "razorpay_create_QR_code":
                if not all(k in arguments for k in ["type", "usage"]):
                    raise ValueError("Missing required arguments: type and usage")
                result = await create_QR_code(**arguments)
            elif name == "razorpay_close_QR_code":
                if "qr_id" not in arguments:
                    raise ValueError("Missing required argument: qr_id")
                result = await close_QR_code(**arguments)
            elif name == "razorpay_fetch_all_QR_codes":
                result = await fetch_all_QR_codes(**arguments)
            elif name == "razorpay_fetch_QR_code_by_id":
                if "qr_id" not in arguments:
                    raise ValueError("Missing required argument: qr_id")
                result = await fetch_QR_code_by_id(**arguments)
            elif name == "razorpay_update_QR_code":
                if not all(k in arguments for k in ["qr_id", "notes"]):
                    raise ValueError("Missing required arguments: qr_id and notes")
                result = await update_QR_code(**arguments)

            # --- Payment Link Tools ---
            elif name == "razorpay_create_payment_link":
                if not all(k in arguments for k in ["amount", "description"]):
                    raise ValueError("Missing required arguments: amount and description")
                result = await create_payment_link(**arguments)
            elif name == "razorpay_update_payment_link":
                if "payment_link_id" not in arguments:
                    raise ValueError("Missing required argument: payment_link_id")
                result = await update_payment_link(**arguments)
            elif name == "razorpay_fetch_all_payment_links":
                result = await fetch_all_payment_links(**arguments)
            elif name == "razorpay_fetch_payment_links_with_id":
                if "payment_link_id" not in arguments:
                    raise ValueError("Missing required argument: payment_link_id")
                result = await fetch_payment_links_with_id(**arguments)
            elif name == "razorpay_send_or_resend_payment_link_notifications":
                if not all(k in arguments for k in ["payment_link_id", "medium"]):
                    raise ValueError("Missing required arguments: payment_link_id and medium")
                result = await send_or_resend_payment_link_notifications(**arguments)
            elif name == "razorpay_cancel_payment_link":
                if "payment_link_id" not in arguments:
                    raise ValueError("Missing required argument: payment_link_id")
                result = await cancel_payment_link(**arguments)

            # --- Downtime Tools ---
            elif name == "razorpay_fetch_payment_downtime_details":
                result = await fetch_payment_downtime_details(**arguments)
            elif name == "razorpay_fetch_payment_downtime_details_with_id":
                if "payment_id" not in arguments:
                    raise ValueError("Missing required argument: payment_id")
                result = await fetch_payment_downtime_details_with_id(**arguments)

            # --- Document Tools ---
            elif name == "razorpay_fetch_document_information":
                if "document_id" not in arguments:
                    raise ValueError("Missing required argument: document_id")
                result = await fetch_document_information(**arguments)
            elif name == "razorpay_fetch_document_content":
                if "document_id" not in arguments:
                    raise ValueError("Missing required argument: document_id")
                result = await fetch_document_content(**arguments)

            else:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=json.dumps({"error": error_msg}))]

            logger.info(f"Tool {name} executed successfully")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            error_response = {
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments,
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    # Run with stdio transport
    logger.info("Starting Razorpay MCP server with stdio transport")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


@click.command()
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
def main(log_level: str) -> int:
    """Razorpay MCP server with stdio transport."""
    try:
        asyncio.run(run_server(log_level))
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    main()