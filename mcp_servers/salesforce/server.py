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
    access_token_context, instance_url_context,
    # Accounts
    get_accounts, get_account_by_id, create_account, update_account, delete_account,
    # Contacts
    get_contacts, get_contact_by_id, create_contact, update_contact, delete_contact,
    # Opportunities
    get_opportunities, get_opportunity_by_id, create_opportunity, update_opportunity, delete_opportunity,
    # Leads
    get_leads, get_lead_by_id, create_lead, update_lead, delete_lead, convert_lead,
    # Cases
    get_cases, get_case_by_id, create_case, update_case, delete_case,
    # Campaigns
    get_campaigns, get_campaign_by_id, create_campaign, update_campaign, delete_campaign,
    # Activities
    get_tasks, get_task_by_id, create_task, update_task, delete_task,
    get_events, get_event_by_id, create_event, update_event, delete_event,
    # Reports
    get_reports, run_report, get_report_by_id,
    # Metadata & Queries
    describe_object, get_component_source, execute_soql_query, execute_tooling_query
)

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()
SALESFORCE_MCP_SERVER_PORT = int(os.getenv("SALESFORCE_MCP_SERVER_PORT", "5000"))

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
                description="Get accounts with optional field selection and filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Maximum number of accounts to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_account_by_id",
                description="Get a specific account by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["account_id"],
                    "properties": {
                        "account_id": {"type": "string", "description": "The ID of the account to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
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
                }
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
                }
            ),
            
            # Contact Tools
            types.Tool(
                name="salesforce_get_contacts",
                description="Get contacts, optionally filtered by account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter contacts by account ID"},
                        "limit": {"type": "integer", "description": "Maximum number of contacts to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_contact_by_id",
                description="Get a specific contact by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["contact_id"],
                    "properties": {
                        "contact_id": {"type": "string", "description": "The ID of the contact to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
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
                }
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
                }
            ),
            
            # Opportunity Tools  
            types.Tool(
                name="salesforce_get_opportunities",
                description="Get opportunities, optionally filtered by account or stage.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter opportunities by account ID"},
                        "stage": {"type": "string", "description": "Filter opportunities by stage"},
                        "limit": {"type": "integer", "description": "Maximum number of opportunities to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_opportunity_by_id",
                description="Get a specific opportunity by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {"type": "string", "description": "The ID of the opportunity to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
            ),
            types.Tool(
                name="salesforce_update_opportunity", 
                description="Update an existing opportunity.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id", "opportunity_data"],
                    "properties": {
                        "opportunity_id": {"type": "string", "description": "The ID of the opportunity to update"},
                        "opportunity_data": {"type": "object", "description": "Updated opportunity data"}
                    }
                }
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
                }
            ),
            
            # Lead Tools
            types.Tool(
                name="salesforce_get_leads",
                description="Get leads, optionally filtered by status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Filter leads by status"},
                        "limit": {"type": "integer", "description": "Maximum number of leads to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_lead_by_id",
                description="Get a specific lead by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["lead_id"],
                    "properties": {
                        "lead_id": {"type": "string", "description": "The ID of the lead to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
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
                }
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
                }
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
                }
            ),
            
            # Case Tools
            types.Tool(
                name="salesforce_get_cases",
                description="Get cases, optionally filtered by account, status, or priority.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Filter cases by account ID"},
                        "status": {"type": "string", "description": "Filter cases by status"},
                        "priority": {"type": "string", "description": "Filter cases by priority"},
                        "limit": {"type": "integer", "description": "Maximum number of cases to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_case_by_id",
                description="Get a specific case by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["case_id"],
                    "properties": {
                        "case_id": {"type": "string", "description": "The ID of the case to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
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
                }
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
                }
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
                }
            ),
            types.Tool(
                name="salesforce_get_campaign_by_id",
                description="Get a specific campaign by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["campaign_id"],
                    "properties": {
                        "campaign_id": {"type": "string", "description": "The ID of the campaign to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
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
                }
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
                }
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
                }
            ),
            
            # Task Tools
            types.Tool(
                name="salesforce_get_tasks",
                description="Get tasks, optionally filtered by assignee or status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "assigned_to": {"type": "string", "description": "Filter tasks by assignee ID"},
                        "status": {"type": "string", "description": "Filter tasks by status"},
                        "limit": {"type": "integer", "description": "Maximum number of tasks to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_task_by_id",
                description="Get a specific task by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {"type": "string", "description": "The ID of the task to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_create_task",
                description="Create a new task in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["task_data"],
                    "properties": {
                        "task_data": {"type": "object", "description": "Task data including Subject (required)"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_update_task",
                description="Update an existing task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id", "task_data"],
                    "properties": {
                        "task_id": {"type": "string", "description": "The ID of the task to update"},
                        "task_data": {"type": "object", "description": "Updated task data"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_delete_task",
                description="Delete a task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {"type": "string", "description": "The ID of the task to delete"}
                    }
                }
            ),
            
            # Event Tools
            types.Tool(
                name="salesforce_get_events",
                description="Get events, optionally filtered by assignee.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "assigned_to": {"type": "string", "description": "Filter events by assignee ID"},
                        "limit": {"type": "integer", "description": "Maximum number of events to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_event_by_id",
                description="Get a specific event by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The ID of the event to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_create_event",
                description="Create a new event in Salesforce.",
                inputSchema={
                    "type": "object",
                    "required": ["event_data"],
                    "properties": {
                        "event_data": {"type": "object", "description": "Event data including Subject, StartDateTime, and EndDateTime (required)"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_update_event",
                description="Update an existing event.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id", "event_data"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The ID of the event to update"},
                        "event_data": {"type": "object", "description": "Updated event data"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_delete_event",
                description="Delete an event.",
                inputSchema={
                    "type": "object",
                    "required": ["event_id"],
                    "properties": {
                        "event_id": {"type": "string", "description": "The ID of the event to delete"}
                    }
                }
            ),
            
            # Report Tools
            types.Tool(
                name="salesforce_get_reports",
                description="Get reports, optionally filtered by folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Filter reports by folder ID"},
                        "limit": {"type": "integer", "description": "Maximum number of reports to return (default: 50)", "default": 50},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_get_report_by_id",
                description="Get a specific report by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["report_id"],
                    "properties": {
                        "report_id": {"type": "string", "description": "The ID of the report to retrieve"},
                        "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to retrieve"}
                    }
                }
            ),
            types.Tool(
                name="salesforce_run_report",
                description="Run a report and get its results.",
                inputSchema={
                    "type": "object",
                    "required": ["report_id"],
                    "properties": {
                        "report_id": {"type": "string", "description": "The ID of the report to run"},
                        "include_details": {"type": "boolean", "description": "Whether to include detailed results", "default": True}
                    }
                }
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
                }
            ),
            types.Tool(
                name="salesforce_tooling_query",
                description="Execute a query against the Salesforce Tooling API",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Tooling API query to execute"}
                    }
                }
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
                }
            ),
            types.Tool(
                name="salesforce_get_component_source",
                description="Retrieve the source code and definitions of Salesforce components.",
                inputSchema={
                    "type": "object",
                    "required": ["metadata_type", "component_names"],
                    "properties": {
                        "metadata_type": {
                            "type": "string",
                            "description": "Type of component to retrieve",
                            "enum": ["CustomObject", "Flow", "FlowDefinition", "CustomField", "ValidationRule", "ApexClass", "ApexTrigger", "WorkflowRule", "Layout"]
                        },
                        "component_names": {"type": "array", "items": {"type": "string"}, "description": "Array of component names to retrieve"}
                    }
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            # Account tools
            if name == "salesforce_get_accounts":
                result = await get_accounts(arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_account_by_id":
                result = await get_account_by_id(arguments["account_id"], arguments.get("fields"))
            elif name == "salesforce_create_account":
                result = await create_account(arguments["account_data"])
            elif name == "salesforce_update_account":
                result = await update_account(arguments["account_id"], arguments["account_data"])
            elif name == "salesforce_delete_account":
                result = await delete_account(arguments["account_id"])
            
            # Contact tools
            elif name == "salesforce_get_contacts":
                result = await get_contacts(arguments.get("account_id"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_contact_by_id":
                result = await get_contact_by_id(arguments["contact_id"], arguments.get("fields"))
            elif name == "salesforce_create_contact":
                result = await create_contact(arguments["contact_data"])
            elif name == "salesforce_update_contact":
                result = await update_contact(arguments["contact_id"], arguments["contact_data"])
            elif name == "salesforce_delete_contact":
                result = await delete_contact(arguments["contact_id"])
            
            # Opportunity tools
            elif name == "salesforce_get_opportunities":
                result = await get_opportunities(arguments.get("account_id"), arguments.get("stage"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_opportunity_by_id":
                result = await get_opportunity_by_id(arguments["opportunity_id"], arguments.get("fields"))
            elif name == "salesforce_create_opportunity":
                result = await create_opportunity(arguments["opportunity_data"])
            elif name == "salesforce_update_opportunity":
                result = await update_opportunity(arguments["opportunity_id"], arguments["opportunity_data"])
            elif name == "salesforce_delete_opportunity":
                result = await delete_opportunity(arguments["opportunity_id"])
            
            # Lead tools
            elif name == "salesforce_get_leads":
                result = await get_leads(arguments.get("status"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_lead_by_id":
                result = await get_lead_by_id(arguments["lead_id"], arguments.get("fields"))
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
                result = await get_cases(arguments.get("account_id"), arguments.get("status"), arguments.get("priority"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_case_by_id":
                result = await get_case_by_id(arguments["case_id"], arguments.get("fields"))
            elif name == "salesforce_create_case":
                result = await create_case(arguments["case_data"])
            elif name == "salesforce_update_case":
                result = await update_case(arguments["case_id"], arguments["case_data"])
            elif name == "salesforce_delete_case":
                result = await delete_case(arguments["case_id"])
            
            # Campaign tools
            elif name == "salesforce_get_campaigns":
                result = await get_campaigns(arguments.get("status"), arguments.get("type_filter"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_campaign_by_id":
                result = await get_campaign_by_id(arguments["campaign_id"], arguments.get("fields"))
            elif name == "salesforce_create_campaign":
                result = await create_campaign(arguments["campaign_data"])
            elif name == "salesforce_update_campaign":
                result = await update_campaign(arguments["campaign_id"], arguments["campaign_data"])
            elif name == "salesforce_delete_campaign":
                result = await delete_campaign(arguments["campaign_id"])
            
            # Task tools
            elif name == "salesforce_get_tasks":
                result = await get_tasks(arguments.get("assigned_to"), arguments.get("status"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_task_by_id":
                result = await get_task_by_id(arguments["task_id"], arguments.get("fields"))
            elif name == "salesforce_create_task":
                result = await create_task(arguments["task_data"])
            elif name == "salesforce_update_task":
                result = await update_task(arguments["task_id"], arguments["task_data"])
            elif name == "salesforce_delete_task":
                result = await delete_task(arguments["task_id"])
            
            # Event tools
            elif name == "salesforce_get_events":
                result = await get_events(arguments.get("assigned_to"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_event_by_id":
                result = await get_event_by_id(arguments["event_id"], arguments.get("fields"))
            elif name == "salesforce_create_event":
                result = await create_event(arguments["event_data"])
            elif name == "salesforce_update_event":
                result = await update_event(arguments["event_id"], arguments["event_data"])
            elif name == "salesforce_delete_event":
                result = await delete_event(arguments["event_id"])
            
            # Report tools
            elif name == "salesforce_get_reports":
                result = await get_reports(arguments.get("folder_id"), arguments.get("limit", 50), arguments.get("fields"))
            elif name == "salesforce_get_report_by_id":
                result = await get_report_by_id(arguments["report_id"], arguments.get("fields"))
            elif name == "salesforce_run_report":
                result = await run_report(arguments["report_id"], arguments.get("include_details", True))
            
            # Query and metadata tools  
            elif name == "salesforce_query":
                result = await execute_soql_query(arguments["query"])
            elif name == "salesforce_tooling_query":
                result = await execute_tooling_query(arguments["query"])
            elif name == "salesforce_describe_object":
                result = await describe_object(arguments["object_name"], arguments.get("detailed", False))
            elif name == "salesforce_get_component_source":
                result = await get_component_source(arguments["metadata_type"], arguments["component_names"])
            
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
        access_token = request.headers.get('x-auth-token')
        instance_url = request.headers.get('x-instance-url')
        
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
        headers = dict(scope.get("headers", []))
        access_token = headers.get(b'x-auth-token')
        instance_url = headers.get(b'x-instance-url')
        
        if access_token:
            access_token = access_token.decode('utf-8')
        if instance_url:
            instance_url = instance_url.decode('utf-8')
        
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