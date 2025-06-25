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
    auth_token_context,
    get_lists, get_list_by_id, create_list,
    get_list_entries, get_list_entry_by_id, create_list_entry, delete_list_entry,
    search_persons, get_person_by_id, create_person, update_person, delete_person,
    search_organizations, get_organization_by_id, create_organization, update_organization, delete_organization,
    search_opportunities, get_opportunity_by_id, create_opportunity, update_opportunity, delete_opportunity,
    get_notes, get_note_by_id, create_note, update_note, delete_note,
    get_field_values, create_field_value, update_field_value, delete_field_value
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

AFFINITY_MCP_SERVER_PORT = int(os.getenv("AFFINITY_MCP_SERVER_PORT", "5000"))

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
            # Lists
            types.Tool(
                name="affinity_get_lists",
                description="Get all lists in the Affinity workspace.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="affinity_get_list_by_id",
                description="Get a specific list by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_list",
                description="Create a new list in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the list.",
                        },
                        "list_type": {
                            "type": "integer",
                            "description": "The type of the list (0=Person list, 1=Organization list, 2=Opportunity list).",
                            "default": 0,
                        },
                    },
                },
            ),
            # Persons
            types.Tool(
                name="affinity_search_persons",
                description="Search for persons in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term to find persons by name or email.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of persons to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_get_person_by_id",
                description="Get a specific person by their ID.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_person",
                description="Create a new person in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["first_name", "last_name"],
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "The first name of the person.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "The last name of the person.",
                        },
                        "emails": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of email addresses for the person.",
                        },
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of organization IDs to associate with the person.",
                        },
                    },
                },
            ),
            # List Entries
            types.Tool(
                name="affinity_get_list_entries",
                description="Get list entries for a specific list.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list to get entries for.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of entries to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_get_list_entry_by_id",
                description="Get a specific list entry by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["list_entry_id"],
                    "properties": {
                        "list_entry_id": {
                            "type": "integer",
                            "description": "The ID of the list entry to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_list_entry",
                description="Create a new list entry.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "entity_id"],
                    "properties": {
                        "list_id": {
                            "type": "integer",
                            "description": "The ID of the list to add the entry to.",
                        },
                        "entity_id": {
                            "type": "integer",
                            "description": "The ID of the entity (person, organization, or opportunity) to add to the list.",
                        },
                        "creator_id": {
                            "type": "integer",
                            "description": "The ID of the user creating the list entry.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_list_entry",
                description="Delete a specific list entry.",
                inputSchema={
                    "type": "object",
                    "required": ["list_entry_id"],
                    "properties": {
                        "list_entry_id": {
                            "type": "integer",
                            "description": "The ID of the list entry to delete.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_update_person",
                description="Update an existing person in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person to update.",
                        },
                        "first_name": {
                            "type": "string",
                            "description": "The new first name of the person.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "The new last name of the person.",
                        },
                        "emails": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of email addresses for the person.",
                        },
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of organization IDs to associate with the person.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_person",
                description="Delete a person from Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "The ID of the person to delete.",
                        },
                    },
                },
            ),
            # Organizations
            types.Tool(
                name="affinity_search_organizations",
                description="Search for organizations in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term to find organizations by name or domain.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of organizations to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_get_organization_by_id",
                description="Get a specific organization by their ID.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_organization",
                description="Create a new organization in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the organization.",
                        },
                        "domain": {
                            "type": "string",
                            "description": "The domain of the organization.",
                        },
                        "person_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of person IDs to associate with the organization.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_update_organization",
                description="Update an existing organization in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the organization.",
                        },
                        "domain": {
                            "type": "string",
                            "description": "The new domain of the organization.",
                        },
                        "person_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of person IDs to associate with the organization.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_organization",
                description="Delete an organization from Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to delete.",
                        },
                    },
                },
            ),
            # Opportunities
            types.Tool(
                name="affinity_search_opportunities",
                description="Search for opportunities in Affinity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Search term to find opportunities by name.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of opportunities to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_get_opportunity_by_id",
                description="Get a specific opportunity by their ID.",
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
            ),
            types.Tool(
                name="affinity_create_opportunity",
                description="Create a new opportunity in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the opportunity.",
                        },
                        "person_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of person IDs to associate with the opportunity.",
                        },
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of organization IDs to associate with the opportunity.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_update_opportunity",
                description="Update an existing opportunity in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {
                            "type": "integer",
                            "description": "The ID of the opportunity to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the opportunity.",
                        },
                        "person_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of person IDs to associate with the opportunity.",
                        },
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of organization IDs to associate with the opportunity.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_opportunity",
                description="Delete an opportunity from Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["opportunity_id"],
                    "properties": {
                        "opportunity_id": {
                            "type": "integer",
                            "description": "The ID of the opportunity to delete.",
                        },
                    },
                },
            ),
            # Notes
            types.Tool(
                name="affinity_get_notes",
                description="Get notes, optionally filtered by person, organization, or opportunity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "Optional person ID to filter notes by person.",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "Optional organization ID to filter notes by organization.",
                        },
                        "opportunity_id": {
                            "type": "integer",
                            "description": "Optional opportunity ID to filter notes by opportunity.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of notes to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_get_note_by_id",
                description="Get a specific note by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["note_id"],
                    "properties": {
                        "note_id": {
                            "type": "integer",
                            "description": "The ID of the note to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_note",
                description="Create a new note in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content of the note.",
                        },
                        "person_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of person IDs to associate with the note.",
                        },
                        "organization_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of organization IDs to associate with the note.",
                        },
                        "opportunity_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of opportunity IDs to associate with the note.",
                        },
                        "parent_id": {
                            "type": "integer",
                            "description": "The ID of the parent note (for threaded notes).",
                        },
                        "type": {
                            "type": "integer",
                            "description": "The type of the note (0=Text, 1=HTML).",
                            "default": 0,
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_update_note",
                description="Update an existing note in Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["note_id", "content"],
                    "properties": {
                        "note_id": {
                            "type": "integer",
                            "description": "The ID of the note to update.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The new content of the note.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_note",
                description="Delete a note from Affinity.",
                inputSchema={
                    "type": "object",
                    "required": ["note_id"],
                    "properties": {
                        "note_id": {
                            "type": "integer",
                            "description": "The ID of the note to delete.",
                        },
                    },
                },
            ),
            # Field Values
            types.Tool(
                name="affinity_get_field_values",
                description="Get field values for a specific entity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "Optional person ID to get field values for.",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "Optional organization ID to get field values for.",
                        },
                        "opportunity_id": {
                            "type": "integer",
                            "description": "Optional opportunity ID to get field values for.",
                        },
                        "list_entry_id": {
                            "type": "integer",
                            "description": "Optional list entry ID to get field values for.",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of field values to return per page (default: 10).",
                            "default": 10,
                        },
                        "page_token": {
                            "type": "string",
                            "description": "Token for pagination to get the next page of results.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_create_field_value",
                description="Create a new field value.",
                inputSchema={
                    "type": "object",
                    "required": ["field_id", "entity_id", "value"],
                    "properties": {
                        "field_id": {
                            "type": "integer",
                            "description": "The ID of the field.",
                        },
                        "entity_id": {
                            "type": "integer",
                            "description": "The ID of the entity (person, organization, or opportunity).",
                        },
                        "value": {
                            "description": "The value to set for the field.",
                        },
                        "list_entry_id": {
                            "type": "integer",
                            "description": "Optional list entry ID if this is a list-specific field value.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_update_field_value",
                description="Update an existing field value.",
                inputSchema={
                    "type": "object",
                    "required": ["field_value_id", "value"],
                    "properties": {
                        "field_value_id": {
                            "type": "integer",
                            "description": "The ID of the field value to update.",
                        },
                        "value": {
                            "description": "The new value for the field.",
                        },
                    },
                },
            ),
            types.Tool(
                name="affinity_delete_field_value",
                description="Delete a field value.",
                inputSchema={
                    "type": "object",
                    "required": ["field_value_id"],
                    "properties": {
                        "field_value_id": {
                            "type": "integer",
                            "description": "The ID of the field value to delete.",
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # Lists
        if name == "affinity_get_lists":
            try:
                result = await get_lists()
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
        
        elif name == "affinity_get_list_by_id":
            list_id = arguments.get("list_id")
            if not list_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id parameter is required",
                    )
                ]
            try:
                result = await get_list_by_id(list_id)
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
        
        elif name == "affinity_create_list":
            name_param = arguments.get("name")
            if not name_param:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            
            list_type = arguments.get("list_type", 0)
            
            try:
                result = await create_list(name_param, list_type)
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
        elif name == "affinity_search_persons":
            term = arguments.get("term")
            page_size = arguments.get("page_size", 10)
            page_token = arguments.get("page_token")
            
            try:
                result = await search_persons(term, page_size, page_token)
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
        
        elif name == "affinity_get_person_by_id":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            try:
                result = await get_person_by_id(person_id)
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
        
        elif name == "affinity_create_person":
            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")
            if not first_name or not last_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: first_name and last_name parameters are required",
                    )
                ]
            
            emails = arguments.get("emails")
            organization_ids = arguments.get("organization_ids")
            
            try:
                result = await create_person(first_name, last_name, emails, organization_ids)
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
        
        # List Entries
        elif name == "affinity_get_list_entries":
            list_id = arguments.get("list_id")
            if not list_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id parameter is required",
                    )
                ]
            
            page_size = arguments.get("page_size", 10)
            page_token = arguments.get("page_token")
            
            try:
                result = await get_list_entries(list_id, page_size, page_token)
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
        
        elif name == "affinity_get_list_entry_by_id":
            list_entry_id = arguments.get("list_entry_id")
            if not list_entry_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_entry_id parameter is required",
                    )
                ]
            try:
                result = await get_list_entry_by_id(list_entry_id)
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
        
        elif name == "affinity_create_list_entry":
            list_id = arguments.get("list_id")
            entity_id = arguments.get("entity_id")
            if not list_id or not entity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_id and entity_id parameters are required",
                    )
                ]
            
            creator_id = arguments.get("creator_id")
            
            try:
                result = await create_list_entry(list_id, entity_id, creator_id)
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
        
        elif name == "affinity_delete_list_entry":
            list_entry_id = arguments.get("list_entry_id")
            if not list_entry_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: list_entry_id parameter is required",
                    )
                ]
            try:
                result = await delete_list_entry(list_entry_id)
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
        
        elif name == "affinity_update_person":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            
            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")
            emails = arguments.get("emails")
            organization_ids = arguments.get("organization_ids")
            
            try:
                result = await update_person(person_id, first_name, last_name, emails, organization_ids)
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
        
        elif name == "affinity_delete_person":
            person_id = arguments.get("person_id")
            if not person_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: person_id parameter is required",
                    )
                ]
            try:
                result = await delete_person(person_id)
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
        
        # Organizations
        elif name == "affinity_search_organizations":
            term = arguments.get("term")
            page_size = arguments.get("page_size", 10)
            page_token = arguments.get("page_token")
            
            try:
                result = await search_organizations(term, page_size, page_token)
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
        
        elif name == "affinity_get_organization_by_id":
            organization_id = arguments.get("organization_id")
            if not organization_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: organization_id parameter is required",
                    )
                ]
            try:
                result = await get_organization_by_id(organization_id)
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
        
        elif name == "affinity_create_organization":
            name_param = arguments.get("name")
            if not name_param:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            
            domain = arguments.get("domain")
            person_ids = arguments.get("person_ids")
            
            try:
                result = await create_organization(name_param, domain, person_ids)
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
        
        elif name == "affinity_update_organization":
            organization_id = arguments.get("organization_id")
            if not organization_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: organization_id parameter is required",
                    )
                ]
            
            name_param = arguments.get("name")
            domain = arguments.get("domain")
            person_ids = arguments.get("person_ids")
            
            try:
                result = await update_organization(organization_id, name_param, domain, person_ids)
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
        
        elif name == "affinity_delete_organization":
            organization_id = arguments.get("organization_id")
            if not organization_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: organization_id parameter is required",
                    )
                ]
            try:
                result = await delete_organization(organization_id)
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
        elif name == "affinity_search_opportunities":
            term = arguments.get("term")
            page_size = arguments.get("page_size", 10)
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
        
        elif name == "affinity_get_opportunity_by_id":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: opportunity_id parameter is required",
                    )
                ]
            try:
                result = await get_opportunity_by_id(opportunity_id)
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
        
        elif name == "affinity_create_opportunity":
            name_param = arguments.get("name")
            if not name_param:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            
            person_ids = arguments.get("person_ids")
            organization_ids = arguments.get("organization_ids")
            
            try:
                result = await create_opportunity(name_param, person_ids, organization_ids)
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
        
        elif name == "affinity_update_opportunity":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: opportunity_id parameter is required",
                    )
                ]
            
            name_param = arguments.get("name")
            person_ids = arguments.get("person_ids")
            organization_ids = arguments.get("organization_ids")
            
            try:
                result = await update_opportunity(opportunity_id, name_param, person_ids, organization_ids)
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
        
        elif name == "affinity_delete_opportunity":
            opportunity_id = arguments.get("opportunity_id")
            if not opportunity_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: opportunity_id parameter is required",
                    )
                ]
            try:
                result = await delete_opportunity(opportunity_id)
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
        elif name == "affinity_get_notes":
            person_id = arguments.get("person_id")
            organization_id = arguments.get("organization_id")
            opportunity_id = arguments.get("opportunity_id")
            page_size = arguments.get("page_size", 10)
            page_token = arguments.get("page_token")
            
            try:
                result = await get_notes(person_id, organization_id, opportunity_id, page_size, page_token)
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
        
        elif name == "affinity_get_note_by_id":
            note_id = arguments.get("note_id")
            if not note_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: note_id parameter is required",
                    )
                ]
            try:
                result = await get_note_by_id(note_id)
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
        
        elif name == "affinity_create_note":
            content = arguments.get("content")
            if not content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: content parameter is required",
                    )
                ]
            
            person_ids = arguments.get("person_ids")
            organization_ids = arguments.get("organization_ids")
            opportunity_ids = arguments.get("opportunity_ids")
            parent_id = arguments.get("parent_id")
            note_type = arguments.get("type", 0)
            
            try:
                result = await create_note(content, person_ids, organization_ids, opportunity_ids, parent_id, note_type)
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
        
        elif name == "affinity_update_note":
            note_id = arguments.get("note_id")
            content = arguments.get("content")
            if not note_id or not content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: note_id and content parameters are required",
                    )
                ]
            try:
                result = await update_note(note_id, content)
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
        
        elif name == "affinity_delete_note":
            note_id = arguments.get("note_id")
            if not note_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: note_id parameter is required",
                    )
                ]
            try:
                result = await delete_note(note_id)
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
        
        # Field Values
        elif name == "affinity_get_field_values":
            person_id = arguments.get("person_id")
            organization_id = arguments.get("organization_id")
            opportunity_id = arguments.get("opportunity_id")
            list_entry_id = arguments.get("list_entry_id")
            page_size = arguments.get("page_size", 10)
            page_token = arguments.get("page_token")
            
            try:
                result = await get_field_values(person_id, organization_id, opportunity_id, list_entry_id, page_size, page_token)
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
        
        elif name == "affinity_create_field_value":
            field_id = arguments.get("field_id")
            entity_id = arguments.get("entity_id")
            value = arguments.get("value")
            if not field_id or not entity_id or value is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: field_id, entity_id, and value parameters are required",
                    )
                ]
            
            list_entry_id = arguments.get("list_entry_id")
            
            try:
                result = await create_field_value(field_id, entity_id, value, list_entry_id)
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
        
        elif name == "affinity_update_field_value":
            field_value_id = arguments.get("field_value_id")
            value = arguments.get("value")
            if not field_value_id or value is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: field_value_id and value parameters are required",
                    )
                ]
            try:
                result = await update_field_value(field_value_id, value)
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
        
        elif name == "affinity_delete_field_value":
            field_value_id = arguments.get("field_value_id")
            if not field_value_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: field_value_id parameter is required",
                    )
                ]
            try:
                result = await delete_field_value(field_value_id)
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
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = request.headers.get('x-auth-token')
        
        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(auth_token or "")
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
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        
        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
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