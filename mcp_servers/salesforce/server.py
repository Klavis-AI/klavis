import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar
import base64

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
    access_token_context, instance_url_context,
    # Accounts
    get_accounts, create_account, update_account, delete_account,
    # Contacts
    get_contacts, create_contact, update_contact, delete_contact,
    # Opportunities
    get_opportunities, create_opportunity, update_opportunity, delete_opportunity,
    # Leads
    get_leads, create_lead, update_lead, delete_lead, convert_lead,
    # Cases
    get_cases, create_case, update_case, delete_case,
    # Campaigns
    get_campaigns, create_campaign, update_campaign, delete_campaign,
    # Metadata & Queries
    describe_object, execute_soql_query
)

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()
SALESFORCE_MCP_SERVER_PORT = int(os.getenv("SALESFORCE_MCP_SERVER_PORT", "5000"))

def extract_auth_credentials(request_or_scope) -> tuple[str, str]:
    """Extract access token and instance URL from request headers.
    
    Returns:
        tuple: (access_token, instance_url)
    """
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Get headers based on input type
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            header_value = request_or_scope.headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            header_value = headers.get(b'x-auth-data')
            if header_value:
                auth_data = base64.b64decode(header_value).decode('utf-8')

    if not auth_data:
        return "", ""
    
    try:
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', ''), auth_json.get('instance_url', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return "", ""

@click.command()
@click.option("--port", default=SALESFORCE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("salesforce-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Account Tools
            types.Tool(
                name="salesforce_get_accounts",
                description="Get accounts with flexible filtering options including name search, industry, and type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Maximum number of accounts to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"},
                        "name_contains": {"type": "string", "description": "Filter accounts by name containing this text (case-insensitive)"},
                        "industry": {"type": "string", "description": "Filter accounts by industry"},
                        "account_type": {"type": "string", "description": "Filter accounts by type"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_ACCOUNT", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_account",
                description="Create a new account in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["account_data"],
                    "properties": {
                        "account_data": {"type": "object", "description": "Account data including Name (required) and other fields"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_ACCOUNT"})
            ),
            types.Tool(
                name="salesforce_update_account",
                description="Update an existing account.",
                inputSchema={
                    "type": "object",
                    "required": ["account_id", "account_data"],
                    "properties": {
                        "account_id": {"type": "string", "description": "The ID of the account to update"},
                        "account_data": {"type": "object", "description": "Updated account data"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_ACCOUNT"})
            ),
            types.Tool(
                name="salesforce_delete_account",
                description="Delete an account.",
                inputSchema={
                    "type": "object",
                    "required": ["account_id"],
                    "properties": {
                        "account_id": {"type": "string", "description": "The ID of the account to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_ACCOUNT"})
            ),
            
            # Contact Tools
            types.Tool(
                name="salesforce_get_contacts",
                description="Get contacts with flexible filtering options including name, email, and title search.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter contacts by account ID"},
                        "limit": {"type": "integer", "description": "Maximum number of contacts to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"},
                        "name_contains": {"type": "string", "description": "Filter contacts by first or last name containing this text (case-insensitive)"},
                        "email_contains": {"type": "string", "description": "Filter contacts by email containing this text (case-insensitive)"},
                        "title_contains": {"type": "string", "description": "Filter contacts by title containing this text (case-insensitive)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CONTACT", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_contact",
                description="Create a new contact in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["contact_data"],
                    "properties": {
                        "contact_data": {"type": "object", "description": "Contact data including LastName (required) and other fields"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CONTACT"})
            ),
            types.Tool(
                name="salesforce_update_contact",
                description="Update an existing contact.",
                inputSchema={
                    "type": "object",
                    "required": ["contact_id", "contact_data"],
                    "properties": {
                        "contact_id": {"type": "string", "description": "The ID of the contact to update"},
                        "contact_data": {"type": "object", "description": "Updated contact data"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CONTACT"})
            ),
            types.Tool(
                name="salesforce_delete_contact",
                description="Delete a contact.",
                inputSchema={
                    "type": "object",
                    "required": ["contact_id"],
                    "properties": {
                        "contact_id": {"type": "string", "description": "The ID of the contact to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CONTACT"})
            ),
            
            # Opportunity Tools  
            types.Tool(
                name="salesforce_get_opportunities",
                description="Get opportunities, optionally filtered by account, stage, name, or account name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter opportunities by account ID"},
                        "stage": {"type": "string", "description": "Filter opportunities by stage"},
                        "name_contains": {"type": "string", "description": "Filter opportunities by name containing this text"},
                        "account_name_contains": {"type": "string", "description": "Filter opportunities by account name containing this text"},
                        "limit": {"type": "integer", "description": "Maximum number of opportunities to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_OPPORTUNITY", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_opportunity",
                description="Create a new opportunity in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_data"],
                    "properties": {
                        "opportunity_data": {"type": "object", "description": "Opportunity data including Name, StageName, and CloseDate (required)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_OPPORTUNITY"})
            ),
            types.Tool(
                name="salesforce_update_opportunity", 
                description="Update an existing opportunity.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {"type": "string", "description": "The ID of the opportunity to update"},
                        "closed_date": {"type": "string", "description": "The date the opportunity was closed"},
                        "stage": {"type": "string", "description": "The stage the opportunity is in"},
                        "amount": {"type": "number", "description": "The amount of the opportunity"},
                        "next_step": {"type": "string", "description": "The next step for the opportunity"},
                        "description": {"type": "string", "description": "The description of the opportunity"},
                        "owner_id": {"type": "string", "description": "The ID of the owner of the opportunity"},
                        "account_id": {"type": "string", "description": "The ID of the account associated with the opportunity"},
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_OPPORTUNITY"})
            ),
            types.Tool(
                name="salesforce_delete_opportunity",
                description="Delete an opportunity.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {"type": "string", "description": "The ID of the opportunity to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_OPPORTUNITY"})
            ),
            
            # Lead Tools
            types.Tool(
                name="salesforce_get_leads",
                description="Get leads with flexible filtering options including name, company, email, and industry search.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter leads by status"},
                        "limit": {"type": "integer", "description": "Maximum number of leads to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"},
                        "name_contains": {"type": "string", "description": "Filter leads by first or last name containing this text (case-insensitive)"},
                        "company_contains": {"type": "string", "description": "Filter leads by company name containing this text (case-insensitive)"},
                        "email_contains": {"type": "string", "description": "Filter leads by email containing this text (case-insensitive)"},
                        "industry": {"type": "string", "description": "Filter leads by industry"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_LEAD", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_lead",
                description="Create a new lead in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["lead_data"],
                    "properties": {
                        "lead_data": {"type": "object", "description": "Lead data including LastName and Company (required)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_LEAD"})
            ),
            types.Tool(
                name="salesforce_update_lead",
                description="Update an existing lead.",
                inputSchema={
                    "type": "object",
                    "required": ["lead_id", "lead_data"],
                    "properties": {
                        "lead_id": {"type": "string", "description": "The ID of the lead to update"},
                        "lead_data": {"type": "object", "description": "Updated lead data"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_LEAD"})
            ),
            types.Tool(
                name="salesforce_delete_lead",
                description="Delete a lead.",
                inputSchema={
                    "type": "object",
                    "required": ["lead_id"],
                    "properties": {
                        "lead_id": {"type": "string", "description": "The ID of the lead to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_LEAD"})
            ),
            types.Tool(
                name="salesforce_convert_lead",
                description="Convert a lead to account, contact, and optionally opportunity.",
                inputSchema={
                    "type": "object",
                    "required": ["lead_id"],
                    "properties": {
                        "lead_id": {"type": "string", "description": "The ID of the lead to convert"},
                        "conversion_data": {"type": "object", "description": "Optional conversion settings"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_LEAD"})
            ),
            
            # Case Tools
            types.Tool(
                name="salesforce_get_cases",
                description="Get cases with flexible filtering options including subject search, account, status, priority, and type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter cases by account ID"},
                        "status": {"type": "string", "description": "Filter cases by status"},
                        "priority": {"type": "string", "description": "Filter cases by priority"},
                        "limit": {"type": "integer", "description": "Maximum number of cases to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"},
                        "subject_contains": {"type": "string", "description": "Filter cases by subject containing this text (case-insensitive)"},
                        "case_type": {"type": "string", "description": "Filter cases by type"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CASE", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_case",
                description="Create a new case in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["case_data"],
                    "properties": {
                        "case_data": {"type": "object", "description": "Case data including Subject (required)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CASE"})
            ),
            types.Tool(
                name="salesforce_update_case",
                description="Update an existing case.",
                inputSchema={
                    "type": "object",
                    "required": ["case_id", "case_data"],
                    "properties": {
                        "case_id": {"type": "string", "description": "The ID of the case to update"},
                        "case_data": {"type": "object", "description": "Updated case data"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CASE"})
            ),
            types.Tool(
                name="salesforce_delete_case",
                description="Delete a case.",
                inputSchema={
                    "type": "object",
                    "required": ["case_id"],
                    "properties": {
                        "case_id": {"type": "string", "description": "The ID of the case to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CASE"})
            ),
            
            # Campaign Tools
            types.Tool(
                name="salesforce_get_campaigns",
                description="Get campaigns, optionally filtered by status or type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter campaigns by status"},
                        "type_filter": {"type": "string", "description": "Filter campaigns by type"},
                        "limit": {"type": "integer", "description": "Maximum number of campaigns to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CAMPAIGN", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_create_campaign",
                description="Create a new campaign in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_data"],
                    "properties": {
                        "campaign_data": {"type": "object", "description": "Campaign data including Name (required)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CAMPAIGN"})
            ),
            types.Tool(
                name="salesforce_update_campaign",
                description="Update an existing campaign.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id", "campaign_data"],
                    "properties": {
                        "campaign_id": {"type": "string", "description": "The ID of the campaign to update"},
                        "campaign_data": {"type": "object", "description": "Updated campaign data"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CAMPAIGN"})
            ),
            types.Tool(
                name="salesforce_delete_campaign",
                description="Delete a campaign.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {
                        "campaign_id": {"type": "string", "description": "The ID of the campaign to delete"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_CAMPAIGN"})
            ),
            
            # Query and Metadata Tools
            types.Tool(
                name="salesforce_query",
                description="Execute a SOQL query on Salesforce",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "SOQL query to execute"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_QUERY", "readOnlyHint": True})
            ),
            types.Tool(
                name="salesforce_describe_object",
                description="Get detailed schema and field information for any Salesforce object.",
                inputSchema={
                    "type": "object",
                    "required": ["object_name"],
                    "properties": {
                        "object_name": {"type": "string", "description": "API name of the object to describe"},
                        "detailed": {"type": "boolean", "description": "Whether to return additional metadata for custom objects", "default": False}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "SALESFORCE_METADATA", "readOnlyHint": True})
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            # Account tools
            if name == "salesforce_get_accounts":
                result = await get_accounts(
                    limit=arguments.get("limit", 50), 
                    fields=arguments.get("fields"),
                    name_contains=arguments.get("name_contains"),
                    industry=arguments.get("industry"),
                    account_type=arguments.get("account_type")
                )
            elif name == "salesforce_create_account":
                result = await create_account(arguments["account_data"])
            elif name == "salesforce_update_account":
                result = await update_account(arguments["account_id"], arguments["account_data"])
            elif name == "salesforce_delete_account":
                result = await delete_account(arguments["account_id"])
            
            # Contact tools
            elif name == "salesforce_get_contacts":
                result = await get_contacts(
                    account_id=arguments.get("account_id"), 
                    limit=arguments.get("limit", 50), 
                    fields=arguments.get("fields"),
                    name_contains=arguments.get("name_contains"),
                    email_contains=arguments.get("email_contains"),
                    title_contains=arguments.get("title_contains")
                )
            elif name == "salesforce_create_contact":
                result = await create_contact(arguments["contact_data"])
            elif name == "salesforce_update_contact":
                result = await update_contact(arguments["contact_id"], arguments["contact_data"])
            elif name == "salesforce_delete_contact":
                result = await delete_contact(arguments["contact_id"])
            
            # Opportunity tools
            elif name == "salesforce_get_opportunities":
                result = await get_opportunities(
                    arguments.get("account_id"), 
                    arguments.get("stage"), 
                    arguments.get("name_contains"),
                    arguments.get("account_name_contains"),
                    arguments.get("limit", 50), 
                    arguments.get("fields")
                )
            elif name == "salesforce_create_opportunity":
                result = await create_opportunity(arguments["opportunity_data"])
            elif name == "salesforce_update_opportunity":
                result = await update_opportunity(
                    opportunity_id=arguments["opportunity_id"],
                    closed_date=arguments.get("closed_date"),
                    stage=arguments.get("stage"),
                    amount=arguments.get("amount"),
                    next_step=arguments.get("next_step"),
                    description=arguments.get("description"),
                    owner_id=arguments.get("owner_id"),
                    account_id=arguments.get("account_id")
                )
            elif name == "salesforce_delete_opportunity":
                result = await delete_opportunity(arguments["opportunity_id"])
            
            # Lead tools
            elif name == "salesforce_get_leads":
                result = await get_leads(
                    status=arguments.get("status"), 
                    limit=arguments.get("limit", 50), 
                    fields=arguments.get("fields"),
                    name_contains=arguments.get("name_contains"),
                    company_contains=arguments.get("company_contains"),
                    email_contains=arguments.get("email_contains"),
                    industry=arguments.get("industry")
                )
            elif name == "salesforce_create_lead":
                result = await create_lead(arguments["lead_data"])
            elif name == "salesforce_update_lead":
                result = await update_lead(arguments["lead_id"], arguments["lead_data"])
            elif name == "salesforce_delete_lead":
                result = await delete_lead(arguments["lead_id"])
            elif name == "salesforce_convert_lead":
                result = await convert_lead(arguments["lead_id"], arguments.get("conversion_data"))
            
            # Case tools
            elif name == "salesforce_get_cases":
                result = await get_cases(
                    account_id=arguments.get("account_id"), 
                    status=arguments.get("status"), 
                    priority=arguments.get("priority"), 
                    limit=arguments.get("limit", 50), 
                    fields=arguments.get("fields"),
                    subject_contains=arguments.get("subject_contains"),
                    case_type=arguments.get("case_type")
                )
            elif name == "salesforce_create_case":
                result = await create_case(arguments["case_data"])
            elif name == "salesforce_update_case":
                result = await update_case(arguments["case_id"], arguments["case_data"])
            elif name == "salesforce_delete_case":
                result = await delete_case(arguments["case_id"])
            
            # Campaign tools
            elif name == "salesforce_get_campaigns":
                result = await get_campaigns(arguments.get("status"), arguments.get("type_filter"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_create_campaign":
                result = await create_campaign(arguments["campaign_data"])
            elif name == "salesforce_update_campaign":
                result = await update_campaign(arguments["campaign_id"], arguments["campaign_data"])
            elif name == "salesforce_delete_campaign":
                result = await delete_campaign(arguments["campaign_id"])


            
            # Query and metadata tools  
            elif name == "salesforce_query":
                result = await execute_soql_query(arguments["query"])
            elif name == "salesforce_describe_object":
                result = await describe_object(arguments["object_name"], arguments.get("detailed", False))
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth credentials from headers
        access_token, instance_url = extract_auth_credentials(request)
        
        # Set the access token and instance URL in context for this request
        access_token_token = access_token_context.set(access_token or "")
        instance_url_token = instance_url_context.set(instance_url or "")
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            access_token_context.reset(access_token_token)
            instance_url_context.reset(instance_url_token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth credentials from headers
        access_token, instance_url = extract_auth_credentials(scope)
        
        # Set the access token and instance URL in context for this request
        access_token_token = access_token_context.set(access_token or "")
        instance_url_token = instance_url_context.set(instance_url or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            access_token_context.reset(access_token_token)
            instance_url_context.reset(instance_url_token)

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
    return 0

if __name__ == "__main__":
    main() 