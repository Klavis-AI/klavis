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
    get_current_user,
    get_all_list_entries_on_a_list, get_metadata_on_all_lists, get_metadata_on_a_single_list, get_metadata_on_a_single_list_fields, get_a_single_list_entry_on_a_list,
    get_all_persons, get_single_person, get_person_fields_metadata, get_person_lists, get_person_list_entries, search_persons,
    get_all_companies, get_single_company, get_company_fields_metadata, get_company_lists, get_company_list_entries, search_organizations,
    get_all_opportunities, get_single_opportunity, search_opportunities,
    get_all_notes, get_specific_note
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

AFFINITY_MCP_SERVER_PORT = int(os.getenv("AFFINITY_MCP_SERVER_PORT", "5000"))

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

@click.command()
@click.option("--port", default=AFFINITY_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("affinity-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Authentication
            types.Tool(
                name="affinity_get_current_user",
                description="Get current user information from Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_USER", "readOnlyHint": True}
                ),
            ),
            # Lists
            types.Tool(
                name="affinity_get_all_list_entries_on_a_list",
                description="Get all List Entries on a List.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, list, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_metadata_on_all_lists",
                description="Get metadata on all Lists.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_metadata_on_a_single_list",
                description="Get metadata on a single List.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_metadata_on_a_single_list_fields",
                description="Get metadata on a single List's Fields.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_a_single_list_entry_on_a_list",
                description="Get a single List Entry on a List.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "list_entry_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list.",
                        },
                        "list_entry_id": {
                            "type": "integer",
                            "description": "The ID of the list entry.",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, list, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_LIST", "readOnlyHint": True}
                ),
            ),
            # Persons
            types.Tool(
                name="affinity_get_all_persons",
                description="Get all Persons in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                        "ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Person IDs to filter by.",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True} 
                ),
            ),
            types.Tool(
                name="affinity_get_single_person",
                description="Get a single Person by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person to retrieve.",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_person_fields_metadata",
                description="Get metadata on Person Fields.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_person_lists",
                description="Get a Person's Lists.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_person_list_entries",
                description="Get a Person's List Entries.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True}
                ),
            ),
            # Companies
            types.Tool(
                name="affinity_get_all_companies",
                description="Get all Companies in Affinity with basic information and field data.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                        "ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Company IDs to filter by.",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_COMPANY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_single_company",
                description="Get a single Company by ID with basic information and field data.",
                inputSchema={
                    "type": "object",
                    "required": ["company_id"],
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "The ID of the company to retrieve.",
                        },
                        "field_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field IDs for field data.",
                        },
                        "field_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Field types (enriched, global, relationship-intelligence).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_COMPANY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_company_fields_metadata",
                description="Get metadata on Company Fields.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_COMPANY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_company_lists",
                description="Get all Lists that contain the specified Company.",
                inputSchema={
                    "type": "object",
                    "required": ["company_id"],
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "The ID of the company.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_COMPANY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_company_list_entries",
                description="Get List Entries for a Company across all Lists with field data.",
                inputSchema={
                    "type": "object",
                    "required": ["company_id"],
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "The ID of the company.",
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_COMPANY", "readOnlyHint": True}
                ),
            ),
            # Opportunities
            types.Tool(
                name="affinity_get_all_opportunities",
                description="Get all Opportunities in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Cursor for pagination.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items per page (1-100, default 100).",
                        },
                        "ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Opportunity IDs to filter by.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_OPPORTUNITY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_single_opportunity",
                description="Get a single Opportunity by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {
                            "type": "integer",
                            "description": "The ID of the opportunity to retrieve.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_OPPORTUNITY", "readOnlyHint": True}
                ),
            ),
            # Search Tools
            types.Tool(
                name="affinity_search_persons",
                description="Search for persons in Affinity. Search term can be part of an email address, first name, or last name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term for finding persons (email, first name, or last name).",
                        },
                        "with_interaction_dates": {
                            "type": "boolean",
                            "description": "Include interaction dates in the response.",
                        },
                        "with_interaction_persons": {
                            "type": "boolean",
                            "description": "Include persons for each interaction.",
                        },
                        "with_opportunities": {
                            "type": "boolean",
                            "description": "Include opportunity IDs for each person.",
                        },
                        "with_current_organizations": {
                            "type": "boolean",
                            "description": "Include current organization IDs for each person.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (default 500).",
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get next page of results.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_PERSON", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_search_organizations",
                description="Search for organizations / companies in Affinity. Search term can be part of organization name or domain.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term for finding organizations / companies (name or domain).",
                        },
                        "with_interaction_dates": {
                            "type": "boolean",
                            "description": "Include interaction dates in the response.",
                        },
                        "with_interaction_persons": {
                            "type": "boolean",
                            "description": "Include persons for each interaction.",
                        },
                        "with_opportunities": {
                            "type": "boolean",
                            "description": "Include opportunity IDs for each organization.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (default 500).",
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get next page of results.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_ORGANIZATION", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_search_opportunities",
                description="Search for opportunities in Affinity. Search term can be part of opportunity name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term for finding opportunities (name).",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results per page (default 500).",
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get next page of results.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_OPPORTUNITY", "readOnlyHint": True}
                ),
            ),
            # Notes
            types.Tool(
                name="affinity_get_all_notes",
                description="Get all Notes in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "Filter by person ID",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "Filter by organization ID",
                        },
                        "opportunity_id": {
                            "type": "integer",
                            "description": "Filter by opportunity ID",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of items per page",
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_NOTE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="affinity_get_specific_note",
                description="Get a specific note by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["note_id"],
                    "properties": {
                        "note_id": {
                            "type": "integer",
                            "description": "Note ID",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AFFINITY_NOTE", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # Auth
        if name == "affinity_get_current_user":
            try:
                result = await get_current_user()
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
        
        # Lists
        elif name == "affinity_get_all_list_entries_on_a_list":
            list_id = arguments.get("list_id")
            if not list_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_all_list_entries_on_a_list(list_id, cursor, limit, field_ids, field_types)
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
        
        elif name == "affinity_get_metadata_on_all_lists":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_metadata_on_all_lists(cursor, limit)
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
        
        elif name == "affinity_get_metadata_on_a_single_list":
            list_id = arguments.get("list_id")
            if not list_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id parameter is required",
                    )
                ]
            
            try:
                result = await get_metadata_on_a_single_list(list_id)
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
        
        elif name == "affinity_get_metadata_on_a_single_list_fields":
            list_id = arguments.get("list_id")
            if not list_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_metadata_on_a_single_list_fields(list_id, cursor, limit)
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
        
        elif name == "affinity_get_a_single_list_entry_on_a_list":
            list_id = arguments.get("list_id")
            list_entry_id = arguments.get("list_entry_id")
            if not list_id or not list_entry_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id and list_entry_id parameters are required",
                    )
                ]
            
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_a_single_list_entry_on_a_list(list_id, list_entry_id, field_ids, field_types)
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
        
        # Persons
        elif name == "affinity_get_all_persons":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            ids = arguments.get("ids")
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_all_persons(cursor, limit, ids, field_ids, field_types)
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
        
        elif name == "affinity_get_single_person":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_single_person(person_id, field_ids, field_types)
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
        
        elif name == "affinity_get_person_fields_metadata":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_person_fields_metadata(cursor, limit)
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
        
        elif name == "affinity_get_person_lists":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_person_lists(person_id, cursor, limit)
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
        
        elif name == "affinity_get_person_list_entries":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_person_list_entries(person_id, cursor, limit)
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
        
        # Companies
        elif name == "affinity_get_all_companies":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            ids = arguments.get("ids")
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_all_companies(cursor, limit, ids, field_ids, field_types)
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
        
        elif name == "affinity_get_single_company":
            company_id = arguments.get("company_id")
            if not company_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: company_id parameter is required",
                    )
                ]
            
            field_ids = arguments.get("field_ids")
            field_types = arguments.get("field_types")
            
            try:
                result = await get_single_company(company_id, field_ids, field_types)
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
        
        elif name == "affinity_get_company_fields_metadata":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_company_fields_metadata(cursor, limit)
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
        
        elif name == "affinity_get_company_lists":
            company_id = arguments.get("company_id")
            if not company_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: company_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_company_lists(company_id, cursor, limit)
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
        
        elif name == "affinity_get_company_list_entries":
            company_id = arguments.get("company_id")
            if not company_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: company_id parameter is required",
                    )
                ]
            
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            
            try:
                result = await get_company_list_entries(company_id, cursor, limit)
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

        
        # Opportunities
        elif name == "affinity_get_all_opportunities":
            cursor = arguments.get("cursor")
            limit = arguments.get("limit")
            ids = arguments.get("ids")
            
            try:
                result = await get_all_opportunities(cursor, limit, ids)
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
        
        elif name == "affinity_get_single_opportunity":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: opportunity_id parameter is required",
                    )
                ]
            try:
                result = await get_single_opportunity(opportunity_id)
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
        
        # Search Tools
        elif name == "affinity_search_persons":
            term = arguments.get("term")
            with_interaction_dates = arguments.get("with_interaction_dates")
            with_interaction_persons = arguments.get("with_interaction_persons")
            with_opportunities = arguments.get("with_opportunities")
            with_current_organizations = arguments.get("with_current_organizations")
            page_size = arguments.get("page_size")
            page_token = arguments.get("page_token")
            
            try:
                result = await search_persons(term, with_interaction_dates, with_interaction_persons, with_opportunities, with_current_organizations, page_size, page_token)
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
        
        elif name == "affinity_search_organizations":
            term = arguments.get("term")
            with_interaction_dates = arguments.get("with_interaction_dates")
            with_interaction_persons = arguments.get("with_interaction_persons")
            with_opportunities = arguments.get("with_opportunities")
            page_size = arguments.get("page_size")
            page_token = arguments.get("page_token")
            
            try:
                result = await search_organizations(term, with_interaction_dates, with_interaction_persons, with_opportunities, page_size, page_token)
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
        
        elif name == "affinity_search_opportunities":
            term = arguments.get("term")
            page_size = arguments.get("page_size")
            page_token = arguments.get("page_token")
            
            try:
                result = await search_opportunities(term, page_size, page_token)
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
        
        # Notes
        elif name == "affinity_get_all_notes":
            person_id = arguments.get("person_id")
            organization_id = arguments.get("organization_id")
            opportunity_id = arguments.get("opportunity_id")
            page_size = arguments.get("page_size")
            page_token = arguments.get("page_token")
            
            try:
                result = await get_all_notes(person_id, organization_id, opportunity_id, page_size, page_token)
                
                if isinstance(result, dict) and "error" in result:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"API Error: {result.get('error', 'Unknown error occurred')}",
                        )
                    ]
                
                if isinstance(result, dict) and "data" in result and result.get("data") is None:
                    return [
                        types.TextContent(
                            type="text",
                            text="No notes found for the specified criteria. The API returned an empty result.",
                        )
                    ]
                    
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
        
        elif name == "affinity_get_specific_note":
            note_id = arguments.get("note_id")
            if not note_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: note_id parameter is required",
                    )
                ]
            try:
                result = await get_specific_note(note_id)
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
        
        # Extract auth token from headers
        auth_token = extract_access_token(request)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
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
        
        # Extract auth token from headers
        auth_token = extract_access_token(scope)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
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