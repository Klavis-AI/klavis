import contextlib
import base64
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
    auth_token_context,
    moneybird_list_administrations,
    moneybird_list_contacts, moneybird_get_contact, moneybird_create_contact, moneybird_create_contact_person,
    moneybird_list_sales_invoices, moneybird_get_sales_invoice, moneybird_create_sales_invoice,
    moneybird_list_financial_accounts, moneybird_list_products,
    moneybird_list_projects, moneybird_list_time_entries
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

MONEYBIRD_MCP_SERVER_PORT = int(os.getenv("MONEYBIRD_MCP_SERVER_PORT", "5000"))

def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract access_token
                auth_json = json.loads(auth_data)
                return auth_json.get('access_token', '')
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                return ""
    
    return ""

@click.command()
@click.option("--port", default=MONEYBIRD_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("moneybird-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Administration
            types.Tool(
                name="moneybird_list_administrations",
                description="List all administrations that the authenticated user has access to. This should be called first to discover available administrations before using other tools.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_ADMINISTRATION", "readOnlyHint": True}),
            ),
            # Contacts
            types.Tool(
                name="moneybird_list_contacts",
                description="List all contacts in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query to filter contacts.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_CONTACT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_get_contact",
                description="Get details for a specific contact by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id", "contact_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "The ID of the contact to retrieve.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_CONTACT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_create_contact",
                description="Create a new company contact in Moneybird (for organizations/companies).",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id", "contact_data"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "contact_data": {
                            "type": "object",
                            "description": "Contact information for company/organization.",
                            "properties": {
                                "contact": {
                                    "type": "object",
                                    "properties": {
                                        "company_name": {"type": "string", "description": "Company name (required)"},
                                        "phone": {"type": "string"},
                                        "send_invoices_to_email": {"type": "string"},
                                        "address1": {"type": "string"},
                                        "city": {"type": "string"},
                                        "country": {"type": "string"},
                                    }
                                }
                            }
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_CONTACT"}),
            ),
            types.Tool(
                name="moneybird_create_contact_person",
                description="Create a new contact person within an existing company contact in Moneybird.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id", "contact_id", "contact_person_data"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "The ID of the existing company contact.",
                        },
                        "contact_person_data": {
                            "type": "object",
                            "description": "Contact person information.",
                            "properties": {
                                "contact_person": {
                                    "type": "object",
                                    "properties": {
                                        "firstname": {"type": "string", "description": "First name (required)"},
                                        "lastname": {"type": "string", "description": "Last name (required)"},
                                        "phone": {"type": "string"},
                                        "email": {"type": "string"},
                                        "department": {"type": "string"},
                                    }
                                }
                            }
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_CONTACT"}),
            ),
            # Sales Invoices
            types.Tool(
                name="moneybird_list_sales_invoices",
                description="List all sales invoices in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "state": {
                            "type": "string",
                            "description": "Filter by invoice state (draft, open, paid, etc.).",
                        },
                        "period": {
                            "type": "string",
                            "description": "Filter by period (this_month, this_year, etc.).",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Filter by contact ID.",
                        },
                        "created_after": {
                            "type": "string",
                            "description": "Filter invoices created after this date (YYYY-MM-DD).",
                        },
                        "updated_after": {
                            "type": "string",
                            "description": "Filter invoices updated after this date (YYYY-MM-DD).",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_INVOICE", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_get_sales_invoice",
                description="Get details for a specific sales invoice by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id", "invoice_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "invoice_id": {
                            "type": "string",
                            "description": "The ID of the sales invoice to retrieve.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_INVOICE", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_create_sales_invoice",
                description="Create a new sales invoice in Moneybird.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id", "invoice_data"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "invoice_data": {
                            "type": "object",
                            "description": "Sales invoice data including contact_id and details.",
                            "properties": {
                                "sales_invoice": {
                                    "type": "object",
                                    "properties": {
                                        "contact_id": {"type": "string"},
                                        "invoice_date": {"type": "string"},
                                        "due_date": {"type": "string"},
                                        "reference": {"type": "string"},
                                        "details_attributes": {"type": "array"}
                                    }
                                }
                            }
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_INVOICE"}),
            ),
            # Financial
            types.Tool(
                name="moneybird_list_financial_accounts",
                description="List all financial accounts in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_list_products",
                description="List all products in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query to filter products.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_PRODUCT", "readOnlyHint": True}),
            ),
            # Projects & Time
            types.Tool(
                name="moneybird_list_projects",
                description="List all projects in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "state": {
                            "type": "string",
                            "description": "Filter by project state (active, archived, all).",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_PROJECT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="moneybird_list_time_entries",
                description="List all time entries in Moneybird administration.",
                inputSchema={
                    "type": "object",
                    "required": ["administration_id"],
                    "properties": {
                        "administration_id": {
                            "type": "string",
                            "description": "The ID of the Moneybird administration.",
                        },
                        "period": {
                            "type": "string",
                            "description": "Filter by time period.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Filter by contact ID.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Filter by project ID.",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Filter by user ID.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "MONEYBIRD_ENTRY", "readOnlyHint": True}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # Administration
        if name == "moneybird_list_administrations":
            try:
                result = await moneybird_list_administrations()
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
        
        # Contacts
        if name == "moneybird_list_contacts":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            query = arguments.get("query")
            page = arguments.get("page")
            
            try:
                result = await moneybird_list_contacts(administration_id, query, page)
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
        
        elif name == "moneybird_get_contact":
            administration_id = arguments.get("administration_id")
            contact_id = arguments.get("contact_id")
            if not administration_id or not contact_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id and contact_id parameters are required",
                    )
                ]
            
            try:
                result = await moneybird_get_contact(administration_id, contact_id)
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
        
        elif name == "moneybird_create_contact":
            administration_id = arguments.get("administration_id")
            contact_data = arguments.get("contact_data")
            if not administration_id or not contact_data:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id and contact_data parameters are required",
                    )
                ]
            
            try:
                result = await moneybird_create_contact(administration_id, contact_data)
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
        
        elif name == "moneybird_create_contact_person":
            administration_id = arguments.get("administration_id")
            contact_id = arguments.get("contact_id")
            contact_person_data = arguments.get("contact_person_data")
            if not administration_id or not contact_id or not contact_person_data:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id, contact_id, and contact_person_data parameters are required",
                    )
                ]
            
            try:
                result = await moneybird_create_contact_person(administration_id, contact_id, contact_person_data)
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
        
        # Sales Invoices
        elif name == "moneybird_list_sales_invoices":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            state = arguments.get("state")
            period = arguments.get("period")
            contact_id = arguments.get("contact_id")
            created_after = arguments.get("created_after")
            updated_after = arguments.get("updated_after")
            page = arguments.get("page")
            
            try:
                result = await moneybird_list_sales_invoices(administration_id, state, period, contact_id, created_after, updated_after, page)
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
        
        elif name == "moneybird_get_sales_invoice":
            administration_id = arguments.get("administration_id")
            invoice_id = arguments.get("invoice_id")
            if not administration_id or not invoice_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id and invoice_id parameters are required",
                    )
                ]
            
            try:
                result = await moneybird_get_sales_invoice(administration_id, invoice_id)
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
        
        elif name == "moneybird_create_sales_invoice":
            administration_id = arguments.get("administration_id")
            invoice_data = arguments.get("invoice_data")
            if not administration_id or not invoice_data:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id and invoice_data parameters are required",
                    )
                ]
            
            try:
                result = await moneybird_create_sales_invoice(administration_id, invoice_data)
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
        
        # Financial
        elif name == "moneybird_list_financial_accounts":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            try:
                result = await moneybird_list_financial_accounts(administration_id)
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
        
        elif name == "moneybird_list_products":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            query = arguments.get("query")
            page = arguments.get("page")
            
            try:
                result = await moneybird_list_products(administration_id, query, page)
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
        
        # Projects & Time
        elif name == "moneybird_list_projects":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            state = arguments.get("state")
            page = arguments.get("page")
            
            try:
                result = await moneybird_list_projects(administration_id, state, page)
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
        
        elif name == "moneybird_list_time_entries":
            administration_id = arguments.get("administration_id")
            if not administration_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: administration_id parameter is required",
                    )
                ]
            
            period = arguments.get("period")
            contact_id = arguments.get("contact_id")
            project_id = arguments.get("project_id")
            user_id = arguments.get("user_id")
            page = arguments.get("page")
            
            try:
                result = await moneybird_list_time_entries(administration_id, period, contact_id, project_id, user_id, page)
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
        
        # Extract access token from headers
        access_token = extract_access_token(request)

        # Set the access token in context for this request
        token = auth_token_context.set(access_token)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
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
        
        # Extract access token from headers
        access_token = extract_access_token(scope)

        # Set the access token in context for this request
        token = auth_token_context.set(access_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

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