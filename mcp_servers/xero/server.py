import contextlib
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
    xero_token_context,
    xero_list_organisation_details,
    xero_list_contacts,
    xero_list_invoices,
    xero_list_accounts,
    xero_list_items,
    xero_create_contact,
    xero_create_quote,
    xero_update_contact,
    xero_get_payroll_timesheet,
    xero_list_quotes,
    xero_create_invoice,
    xero_update_invoice,
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("xero-mcp-server")

XERO_ACCESS_TOKEN = os.getenv("XERO_ACCESS_TOKEN") or ""  # for local use
XERO_MCP_SERVER_PORT = int(os.getenv("XERO_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=XERO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("xero-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="xero_list_organisation_details",
                description="Retrieve details about the Xero organisation",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="xero_list_contacts",
                description="Retrieve a list of contacts from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of contacts to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="xero_list_invoices",
                description="Retrieve a list of invoices from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of invoices to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by invoice status",
                            "enum": ["DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED"]
                        }
                    }
                }
            ),
            types.Tool(
                name="xero_list_accounts",
                description="Retrieve a list of accounts from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_type": {
                            "type": "string",
                            "description": "Filter by account type",
                            "enum": ["BANK", "CURRENT", "CURRENTLIABILITY", "DEPRECIATN", "DIRECTCOSTS", "EQUITY", "EXPENSE", "FIXED", "INVENTORY", "LIABILITY", "NONCURRENT", "OTHERINCOME", "OVERHEADS", "PREPAYMENT", "REVENUE", "SALES", "TERMLIABILITY", "PAYGLIABILITY"]
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by account status",
                            "enum": ["ACTIVE", "ARCHIVED"]
                        }
                    }
                }
            ),
            types.Tool(
                name="xero_list_items",
                description="Retrieve a list of items from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of items to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                }
            ),
            types.Tool(
                name="xero_create_contact",
                description="Create a new contact in Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Contact name (required)"
                        },
                        "first_name": {
                            "type": "string",
                            "description": "First name for individuals"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Last name for individuals"
                        },
                        "email_address": {
                            "type": "string",
                            "description": "Contact email address"
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Contact phone number"
                        },
                        "is_supplier": {
                            "type": "boolean",
                            "description": "Whether contact is a supplier (default: false)",
                            "default": False
                        },
                        "is_customer": {
                            "type": "boolean",
                            "description": "Whether contact is a customer (default: true)",
                            "default": True
                        },
                        "address_line1": {
                            "type": "string",
                            "description": "Address line 1"
                        },
                        "address_city": {
                            "type": "string",
                            "description": "Address city"
                        },
                        "address_postal_code": {
                            "type": "string",
                            "description": "Address postal/zip code"
                        },
                        "address_country": {
                            "type": "string",
                            "description": "Address country"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="xero_create_quote",
                description="Create a new quote in Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "Contact ID for the quote (required)"
                        },
                        "date": {
                            "type": "string",
                            "description": "Quote date in YYYY-MM-DD format (defaults to today)"
                        },
                        "expiry_date": {
                            "type": "string",
                            "description": "Quote expiry date in YYYY-MM-DD format"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Quote reference number"
                        },
                        "currency_code": {
                            "type": "string",
                            "description": "Currency code (default: USD)",
                            "default": "USD"
                        },
                        "line_items": {
                            "type": "array",
                            "description": "List of line items for the quote",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Line item description"
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "Quantity"
                                    },
                                    "unit_amount": {
                                        "type": "number",
                                        "description": "Unit amount/price"
                                    },
                                    "account_code": {
                                        "type": "string",
                                        "description": "Account code (e.g., '200' for Sales)"
                                    },
                                    "item_code": {
                                        "type": "string",
                                        "description": "Item code if using inventory items"
                                    },
                                    "tax_type": {
                                        "type": "string",
                                        "description": "Tax type code"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="xero_update_contact",
                description="Update an existing contact in Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "Contact ID to update (required)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Contact name"
                        },
                        "first_name": {
                            "type": "string",
                            "description": "First name for individuals"
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Last name for individuals"
                        },
                        "email_address": {
                            "type": "string",
                            "description": "Contact email address"
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Contact phone number"
                        },
                        "is_supplier": {
                            "type": "boolean",
                            "description": "Whether contact is a supplier"
                        },
                        "is_customer": {
                            "type": "boolean",
                            "description": "Whether contact is a customer"
                        },
                        "address_line1": {
                            "type": "string",
                            "description": "Address line 1"
                        },
                        "address_city": {
                            "type": "string",
                            "description": "Address city"
                        },
                        "address_postal_code": {
                            "type": "string",
                            "description": "Address postal/zip code"
                        },
                        "address_country": {
                            "type": "string",
                            "description": "Address country"
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="xero_get_payroll_timesheet",
                description="Retrieve an existing Payroll Timesheet from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timesheet_id": {
                            "type": "string",
                            "description": "The unique identifier for the timesheet (required)"
                        }
                    },
                    "required": ["timesheet_id"]
                }
            ),
            types.Tool(
                name="xero_list_quotes",
                description="Retrieve a list of quotes from Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of quotes to retrieve. Defaults to 10.",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by quote status",
                            "enum": ["DRAFT", "SENT", "ACCEPTED", "DECLINED", "INVOICED", "DELETED"]
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Filter by specific contact ID"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Filter quotes from this date (YYYY-MM-DD format)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Filter quotes to this date (YYYY-MM-DD format)"
                        }
                    }
                }
            ),
            types.Tool(
                name="xero_create_invoice",
                description="Create a new invoice in Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "Contact ID for the invoice (required)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Invoice type (default: ACCREC)",
                            "enum": ["ACCREC", "ACCPAY"],
                            "default": "ACCREC"
                        },
                        "date": {
                            "type": "string",
                            "description": "Invoice date in YYYY-MM-DD format (defaults to today)"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in YYYY-MM-DD format"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Invoice reference number"
                        },
                        "currency_code": {
                            "type": "string",
                            "description": "Currency code (default: USD)",
                            "default": "USD"
                        },
                        "status": {
                            "type": "string",
                            "description": "Invoice status (default: DRAFT)",
                            "enum": ["DRAFT", "SUBMITTED", "AUTHORISED"],
                            "default": "DRAFT"
                        },
                        "line_items": {
                            "type": "array",
                            "description": "List of line items for the invoice",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Line item description"
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "Quantity"
                                    },
                                    "unit_amount": {
                                        "type": "number",
                                        "description": "Unit amount/price"
                                    },
                                    "account_code": {
                                        "type": "string",
                                        "description": "Account code (e.g., '200' for Sales, '400' for Purchases)"
                                    },
                                    "item_code": {
                                        "type": "string",
                                        "description": "Item code if using inventory items"
                                    },
                                    "tax_type": {
                                        "type": "string",
                                        "description": "Tax type code"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["contact_id"]
                }
            ),
            types.Tool(
                name="xero_update_invoice",
                description="Update an existing draft invoice in Xero",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "invoice_id": {
                            "type": "string",
                            "description": "Invoice ID to update (required)"
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Contact ID for the invoice"
                        },
                        "type": {
                            "type": "string",
                            "description": "Invoice type",
                            "enum": ["ACCREC", "ACCPAY"]
                        },
                        "date": {
                            "type": "string",
                            "description": "Invoice date in YYYY-MM-DD format"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in YYYY-MM-DD format"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Invoice reference number"
                        },
                        "currency_code": {
                            "type": "string",
                            "description": "Currency code (e.g., USD, EUR)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Invoice status",
                            "enum": ["DRAFT", "SUBMITTED", "AUTHORISED"]
                        },
                        "line_items": {
                            "type": "array",
                            "description": "List of line items for the invoice",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Line item description"
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "description": "Quantity"
                                    },
                                    "unit_amount": {
                                        "type": "number",
                                        "description": "Unit amount/price"
                                    },
                                    "account_code": {
                                        "type": "string",
                                        "description": "Account code (e.g., '200' for Sales)"
                                    },
                                    "item_code": {
                                        "type": "string",
                                        "description": "Item code if using inventory items"
                                    },
                                    "tax_type": {
                                        "type": "string",
                                        "description": "Tax type code"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["invoice_id"]
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "xero_list_organisation_details":
            try:
                result = await xero_list_organisation_details()
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
        
        elif name == "xero_list_contacts":
            try:
                limit = arguments.get("limit", 10)
                result = await xero_list_contacts(limit)
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
        
        elif name == "xero_list_invoices":
            try:
                limit = arguments.get("limit", 10)
                status = arguments.get("status")
                result = await xero_list_invoices(limit, status)
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
        
        elif name == "xero_list_accounts":
            try:
                account_type = arguments.get("account_type")
                status = arguments.get("status")
                result = await xero_list_accounts(account_type, status)
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
        
        elif name == "xero_list_items":
            try:
                limit = arguments.get("limit", 10)
                result = await xero_list_items(limit)
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
        
        elif name == "xero_create_contact":
            try:
                # Extract required parameter
                name = arguments.get("name")
                if not name:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'name' parameter is required for creating a contact",
                        )
                    ]
                
                # Extract optional parameters
                result = await xero_create_contact(
                    name=name,
                    first_name=arguments.get("first_name"),
                    last_name=arguments.get("last_name"),
                    email_address=arguments.get("email_address"),
                    phone_number=arguments.get("phone_number"),
                    is_supplier=arguments.get("is_supplier", False),
                    is_customer=arguments.get("is_customer", True),
                    address_line1=arguments.get("address_line1"),
                    address_city=arguments.get("address_city"),
                    address_postal_code=arguments.get("address_postal_code"),
                    address_country=arguments.get("address_country")
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
        
        elif name == "xero_create_quote":
            try:
                # Extract required parameter
                contact_id = arguments.get("contact_id")
                if not contact_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'contact_id' parameter is required for creating a quote",
                        )
                    ]
                
                # Extract optional parameters
                result = await xero_create_quote(
                    contact_id=contact_id,
                    date=arguments.get("date"),
                    expiry_date=arguments.get("expiry_date"),
                    reference=arguments.get("reference"),
                    currency_code=arguments.get("currency_code", "USD"),
                    line_items=arguments.get("line_items")
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
        
        elif name == "xero_update_contact":
            try:
                # Extract required parameter
                contact_id = arguments.get("contact_id")
                if not contact_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'contact_id' parameter is required for updating a contact",
                        )
                    ]
                
                # Extract optional parameters
                result = await xero_update_contact(
                    contact_id=contact_id,
                    name=arguments.get("name"),
                    first_name=arguments.get("first_name"),
                    last_name=arguments.get("last_name"),
                    email_address=arguments.get("email_address"),
                    phone_number=arguments.get("phone_number"),
                    is_supplier=arguments.get("is_supplier"),
                    is_customer=arguments.get("is_customer"),
                    address_line1=arguments.get("address_line1"),
                    address_city=arguments.get("address_city"),
                    address_postal_code=arguments.get("address_postal_code"),
                    address_country=arguments.get("address_country")
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
        
        elif name == "xero_get_payroll_timesheet":
            try:
                # Extract required parameter
                timesheet_id = arguments.get("timesheet_id")
                if not timesheet_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'timesheet_id' parameter is required for retrieving a timesheet",
                        )
                    ]
                
                result = await xero_get_payroll_timesheet(timesheet_id=timesheet_id)
                
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
        
        elif name == "xero_list_quotes":
            try:
                limit = arguments.get("limit", 10)
                status = arguments.get("status")
                contact_id = arguments.get("contact_id")
                date_from = arguments.get("date_from")
                date_to = arguments.get("date_to")
                
                result = await xero_list_quotes(
                    limit=limit,
                    status=status,
                    contact_id=contact_id,
                    date_from=date_from,
                    date_to=date_to
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
        
        elif name == "xero_create_invoice":
            try:
                # Extract required parameter
                contact_id = arguments.get("contact_id")
                if not contact_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'contact_id' parameter is required for creating an invoice",
                        )
                    ]
                
                # Extract optional parameters
                result = await xero_create_invoice(
                    contact_id=contact_id,
                    type=arguments.get("type", "ACCREC"),
                    date=arguments.get("date"),
                    due_date=arguments.get("due_date"),
                    reference=arguments.get("reference"),
                    currency_code=arguments.get("currency_code", "USD"),
                    line_items=arguments.get("line_items"),
                    status=arguments.get("status", "DRAFT")
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
        
        elif name == "xero_update_invoice":
            try:
                # Extract required parameter
                invoice_id = arguments.get("invoice_id")
                if not invoice_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Error: 'invoice_id' parameter is required for updating an invoice",
                        )
                    ]
                
                # Extract optional parameters
                result = await xero_update_invoice(
                    invoice_id=invoice_id,
                    contact_id=arguments.get("contact_id"),
                    type=arguments.get("type"),
                    date=arguments.get("date"),
                    due_date=arguments.get("due_date"),
                    reference=arguments.get("reference"),
                    currency_code=arguments.get("currency_code"),
                    line_items=arguments.get("line_items"),
                    status=arguments.get("status")
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
        
        # Extract Xero access token from headers (fallback to environment)
        xero_token = request.headers.get('x-xero-token') or XERO_ACCESS_TOKEN
        
        # Set the Xero token in context for this request
        token = xero_token_context.set(xero_token or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            xero_token_context.reset(token)
        
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
        
        # Extract auth token from headers (fallback to environment)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        else:
            auth_token = XERO_ACCESS_TOKEN
        
        # Set the Xero token in context for this request
        token = xero_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            xero_token_context.reset(token)

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
