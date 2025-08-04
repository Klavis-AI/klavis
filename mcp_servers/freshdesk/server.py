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
    # Ticket tools
    create_ticket,
    update_ticket,
    delete_ticket,
    get_ticket,
    list_tickets,
    add_note_to_ticket,
    search_tickets,
    merge_tickets,
    restore_ticket,
    watch_ticket,
    unwatch_ticket,
    forward_ticket,
    get_archived_ticket,
    delete_archived_ticket,
    delete_attachment,
    create_ticket_with_attachments,
    delete_multiple_tickets,
    
    # Contact tools

    create_contact,
    get_contact,
    list_contacts,
    update_contact,
    delete_contact,
    search_contacts,
    filter_contacts,
    make_contact_agent,
    restore_contact,
    send_contact_invite,
    merge_contacts
    
    
)

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()
FRESHDESK_MCP_SERVER_PORT = int(os.getenv("FRESHDESK_MCP_SERVER_PORT", "5000"))
FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")

@click.command()
@click.option("--port", default=FRESHDESK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("freshdesk-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
            name="create_ticket",
            description="Create a new ticket in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "The subject of the ticket (required)."
                    },
                    "description": {
                        "type": "string",
                        "description": "The HTML content of the ticket (required)."
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Email address of the requester (required)."
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the requester."
                    },
                    "priority": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4],
                        "description": "Priority of the ticket (1=Low, 2=Medium, 3=High, 4=Urgent). Default is 2 (Medium)."
                    },
                    "status": {
                        "type": "integer",
                        "enum": [2, 3, 4, 5],
                        "description": "Status of the ticket (2=Open, 3=Pending, 4=Resolved, 5=Closed). Default is 2 (Open)."
                    },
                    "source": {
                        "type": "integer",
                        "enum": [1, 2, 3, 7, 9, 10],
                        "description": "Source of the ticket (1=Email, 2=Portal, 3=Phone, 7=Chat, 9=Feedback, 10=Outbound Email). Default is 2 (Portal)."
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags to associate with the ticket."
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Key-value pairs of custom fields."
                    },
                    "cc_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of email addresses to CC."
                    },
                    "due_by": {
                        "type": "string",
                        "description": "Due date for the ticket (format: YYYY-MM-DD)."
                    },
                    "fr_due_by": {
                        "type": "string",
                        "description": "Due date for the ticket (format: YYYY-MM-DD)."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of file paths to attach to the ticket."
                    },
                    "responder_id": {
                        "type": "integer",
                        "description": "ID of the responder."
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "ID of the parent ticket. If provided, the ticket will be created as a child of the parent ticket."
                    },
                    "group_id": {
                        "type": "integer",
                        "description": "ID of the group to assign the ticket to."
                    },
                    
                },
                "required": ["subject", "description", "email"]
            }
        ),
        types.Tool(
            name="get_ticket",
            description="Retrieve a ticket by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to retrieve (required)."
                    },
                    "include_conversations": {
                        "type": "boolean",
                        "description": "Whether to include conversation history. Default is false."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="update_ticket",
            description="Update an existing ticket in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to update (required)."
                    },
                    "subject": {
                        "type": "string",
                        "description": "New subject for the ticket."
                    },
                    "description": {
                        "type": "string",
                        "description": "New HTML content for the ticket."
                    },
                    "priority": {
                        "type": "integer",
                        "enum": [1, 2, 3, 4],
                        "description": "New priority (1=Low, 2=Medium, 3=High, 4=Urgent)."
                    },
                    "status": {
                        "type": "integer",
                        "enum": [2, 3, 4, 5],
                        "description": "New status (2=Open, 3=Pending, 4=Resolved, 5=Closed)."
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New list of tags (replaces existing tags)."
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Updated custom fields (merges with existing)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="delete_ticket",
            description="Delete a ticket by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to delete (required)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="add_note_to_ticket",
            description="Add a note to a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket (required)."
                    },
                    "body": {
                        "type": "string",
                        "description": "Content of the note (required)."
                    },
                    "private": {
                        "type": "boolean",
                        "description": "Whether the note is private. Default is false."
                    }
                },
                "required": ["ticket_id", "body"]
            }
        ),
        types.Tool(
            name="forward_ticket",
            description="Forward a ticket to additional email addresses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to forward (required)."
                    },
                    "to_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of email addresses to forward to (required)."
                    },
                    "cc_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of CC email addresses."
                    },
                    "bcc_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of BCC email addresses."
                    },
                    "body": {
                        "type": "string",
                        "description": "Custom message to include in the forward."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Custom subject for the forwarded email."
                    }
                },
                "required": ["ticket_id", "to_emails"]
            }
        ),
        types.Tool(
            name="get_archived_ticket",
            description="Retrieve an archived ticket by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the archived ticket to retrieve (required)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="delete_archived_ticket",
            description="Permanently delete an archived ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the archived ticket to delete (required)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="search_tickets", 
            description="Search for tickets.", 
            inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (required)."
                },
                "page": {
                    "type": "integer",
                    "description": "Page number (for pagination). Default is 1."
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results per page (max 30). Default is 30."
                }
            },
            "required": ["query"]
        }),
        types.Tool(
            name="create_ticket_with_attachments",
            description="Create a new ticket with attachments in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string", 
                        "description": "The subject of the ticket (required)."
                    },
                    "description": {
                        "type": "string", 
                        "description": "The HTML content of the ticket (required)."
                    },
                    "email": {
                        "type": "string", 
                        "format": "email", 
                        "description": "Email address of the requester (required)."
                    },
                    "name": {
                        "type": "string", 
                        "description": "Name of the requester."
                    },
                    "priority": {
                        "type": "integer", 
                        "enum": [1, 2, 3, 4], 
                        "description": "Priority of the ticket (1=Low, 2=Medium, 3=High, 4=Urgent). Default is 2 (Medium)."
                    },
                    "status": {
                        "type": "integer", 
                        "enum": [2, 3, 4, 5], 
                        "description": "Status of the ticket (2=Open, 3=Pending, 4=Resolved, 5=Closed). Default is 2 (Open)."
                    },
                    "source": {
                        "type": "integer", 
                        "enum": [1, 2, 3, 7, 9, 10], 
                        "description": "Source of the ticket (1=Email, 2=Portal, 3=Phone, 7=Chat, 9=Feedback, 10=Outbound Email). Default is 2 (Portal)."
                    },
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"}, 
                        "description": "List of tags to associate with the ticket."
                    },
                    "custom_fields": {  
                        "type": "object", 
                        "description": "Key-value pairs of custom fields."
                    },
                    "cc_emails": {
                        "type": "array", 
                        "items": {"type": "string", "format": "email"}, 
                        "description": "List of email addresses to CC."
                    },
                    "attachments": {
                        "type": "array", 
                        "items": {"type": "object"}, 
                        "description": "List of attachment objects with 'name' and 'content' fields (base64 encoded)."
                    },
                    "due_by": {
                        "type": "string", 
                        "description": "Due date for the ticket (ISO 8601 format)."
                    },
                    "fr_due_by": {
                        "type": "string", 
                        "description": "Due date for the ticket (ISO 8601 format)."
                    },
                    "group_id": {
                        "type": "integer", 
                        "description": "ID of the group."
                    },
                    "responder_id": {
                        "type": "integer", 
                        "description": "ID of the responder."
                    },
                    "parent_id": {
                        "type": "integer", 
                        "description": "ID of the parent ticket. If provided, the ticket will be created as a child of the parent ticket."
                    }
                },
                "required": ["subject", "description", "email"]
            }
        ),
        types.Tool(
            name="delete_multiple_tickets",
            description="Delete multiple tickets at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of ticket IDs to delete (required)."
                    }
                },
                "required": ["ticket_ids"]
            }
        ),
        types.Tool(
            name="delete_attachment",
            description="Delete an attachment from a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "attachment_id": {
                        "type": "integer",
                        "description": "ID of the attachment to delete (required)."
                    }
                },
                "required": ["attachment_id"]
            }
        ),
        types.Tool(
            name="list_tickets",
            description="List tickets with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "integer", 
                        "enum": [2, 3, 4, 5], 
                        "description": "Filter by status (2=Open, 3=Pending, 4=Resolved, 5=Closed)."
                    },
                    "priority": {
                        "type": "integer", 
                        "enum": [1, 2, 3, 4], 
                        "description": "Filter by priority (1=Low, 2=Medium, 3=High, 4=Urgent)."
                    },
                    "requester_id": {
                        "type": "integer", 
                        "description": "Filter by requester ID."
                    },
                    "email": {
                        "type": "string", 
                        "format": "email", 
                        "description": "Filter by email address."
                    },
                    "agent_id": {
                        "type": "integer", 
                        "description": "Filter by agent ID (ID of the agent to whom the ticket has been assigned)."
                    },
                    "company_id": {
                        "type": "integer", 
                        "description": "Filter by company ID."
                    },
                    "group_id": {
                        "type": "integer", 
                        "description": "Filter by group ID."
                    },
                    "ticket_type": {
                        "type": "string", 
                        "description": "Filter by ticket type."
                    },
                    "updated_since": {
                        "type": "string", 
                        "format": "date-time", 
                        "description": "Only return tickets updated since this date (ISO 8601 format)."
                    },
                    "created_since": {
                        "type": "string", 
                        "format": "date-time", 
                        "description": "Only return tickets created since this date (ISO 8601 format)."
                    },
                    "due_by": {
                        "type": "string", 
                        "format": "date-time", 
                        "description": "Only return tickets due by this date (ISO 8601 format)."
                    },
                    "order_by": {
                        "type": "string", 
                        "description": "Order by (created_at, updated_at, priority, status). Default is created_at."
                    },
                    "order_type": {
                        "type": "string", 
                        "enum": ["asc", "desc"], 
                        "description": "Order type (asc or desc). Default is desc."
                    },
                    "include": {
                        "type": "string", 
                        "description": "Include additional data (stats, requester, description)."
                    },
                    "page": {
                        "type": "integer", 
                        "description": "Page number for pagination. Default is 1."
                    },
                    "per_page": {
                        "type": "integer", 
                        "description": "Number of results per page (max 100). Default is 30."
                    }
                }
            }
        ),
        types.Tool(
            name="merge_tickets",
            description="Merge two tickets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to be merged (will be closed) (required)."
                    },
                    "ticket_ids": {
                        "type": "integer",
                        "description": "ID of the ticket to merge into (required)."
                    },
                    "convert_recepients_to_cc": {
                        "type": "boolean",
                        "description": "Convert recipients to CC (optional). Default is False."
                    }
                },
                "required": ["primary_ticket_id", "ticket_ids"]
            }
        ),
        types.Tool(
            name="restore_ticket",
            description="Restore a deleted ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to restore (required)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="watch_ticket",
            description="Watch a ticket for updates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to watch (required)."
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "ID of the user to watch the ticket (defaults to authenticated user)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="unwatch_ticket",
            description="Stop watching a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to unwatch (required)."
                    }
                },
                "required": ["ticket_id"]
            }
        ),
        types.Tool(
            name="create_contact",
            description="Create a new contact in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the contact"},
                    "email": {"type": "string", "format": "email", "description": "Primary email address"},
                    "phone": {"type": "string", "description": "Telephone number"},
                    "company_id": {"type": "integer", "description": "ID of the company"},
                    "description": {"type": "string", "description": "Description of the contact"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="get_contact",
            description="Retrieve a contact by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to retrieve"}
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="list_contacts",
            description="List all contacts, optionally filtered by parameters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email", "description": "Filter by email"},
                    "phone": {"type": "string", "description": "Filter by phone number"},
                    "mobile": {"type": "string", "description": "Filter by mobile number"},
                    "company_id": {"type": "integer", "description": "Filter by company ID"},
                    "state": {"type": "string", "description": "Filter by state (verified, unverified, blocked, deleted)"},
                    "updated_since": {"type": "string", "description": "Filter by last updated date (ISO 8601 format)"},
                    "page": {"type": "integer", "description": "Page number for pagination. Default is 1."},
                    "per_page": {"type": "integer", "description": "Number of results per page (max 100). Default is 30."}
                }
            }
        ),
        types.Tool(
            name="update_contact",
            description="Update an existing contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to update"},
                    "name": {"type": "string", "description": "New name"},
                    "email": {"type": "string", "format": "email", "description": "New primary email"},
                    "phone": {"type": "string", "description": "New phone number"},
                    "mobile": {"type": "string", "description": "New mobile number"},
                    "company_id": {"type": "integer", "description": "New company ID"},
                    "description": {"type": "string", "description": "New description"},
                    "job_title": {"type": "string", "description": "New job title"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Updated list of tags"},
                    "custom_fields": {"type": "object", "description": "Updated custom fields"},
                    "avatar_path": {"type": "string", "description": "Path to new avatar image file"},
                    "address": {"type": "string", "description": "Address of the contact"},
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="delete_contact",
            description="Delete a contact. Set hard_delete=True to permanently delete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to delete"},
                    "hard_delete": {"type": "boolean", "default": False, "description": "If true, permanently delete the contact"},
                    "force": {"type": "boolean", "default": False, "description": "If true, force hard delete even if not soft deleted first"}
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="search_contacts",
            description="Search for contacts by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Search term"}
                },
                "required": ["term"]
            }
        ),
        types.Tool(
            name="filter_contacts",
            description="Filter contacts by fields. using this format - contact_field:integer OR contact_field:'string' AND contact_field:boolean e.g. {query: 'field_name:field_value'} - name:John Doe",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Filter query"},
                    "page": {"type": "integer", "description": "Page number (1-based)", "default": 1},
                    "updated_since": {"type": "string", "description": "Filter by last updated date (ISO 8601 format)"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="make_contact_agent",
            description="Make a contact an agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to make an agent"},
                    "occasional": {"type": "boolean", "description": "Whether agent is occasional"},
                    "signature": {"type": "string", "description": "HTML signature for the agent"},
                    "ticket_scope": {"type": "integer", "description": "Ticket scope for the agent"},
                    "skill_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of skill IDs"},
                    "group_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of group IDs"},
                    "role_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of role IDs"},
                    "agent_type": {"type": "string", "description": "Agent type (support_agent or business_agent)"},
                    "focus_mode": {"type": "boolean", "description": "Whether agent is in focus mode"}
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="restore_contact",
            description="Restore a deleted contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to restore"}
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="send_contact_invite",
            description="Send an invite to a contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to send an invite to"}
                },
                "required": ["contact_id"]
            }
        ),
        types.Tool(
            name="merge_contacts",
            description="Merge multiple contacts into a primary contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_contact_id": {"type": "integer", "description": "ID of the primary contact to merge into"},
                    "secondary_contact_ids": {"type": "array", "items": {"type": "integer"}, "description": "List of contact IDs to merge into the primary contact"},
                    "contact_data": {"type": "object", "description": "Optional dictionary of fields to update on the primary contact"}
                },
                "required": ["primary_contact_id", "secondary_contact_ids"]
            }
        )
    ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:

            if name == "create_ticket":
                result = await create_ticket(**arguments)
            elif name == "get_ticket":
                result = await get_ticket(**arguments)
            elif name == "list_tickets":
                result = await list_tickets(**arguments)
            elif name == "search_tickets":
                result = await search_tickets(**arguments)
            elif name == "add_note_to_ticket":
                result = await add_note_to_ticket(**arguments)
            elif name == "merge_tickets":
                result = await merge_tickets(**arguments)
            elif name == "restore_ticket":
                result = await restore_ticket(**arguments)
            elif name == "watch_ticket":
                result = await watch_ticket(**arguments)
            elif name == "unwatch_ticket":
                result = await unwatch_ticket(**arguments)
            elif name == "forward_ticket":
                result = await forward_ticket(**arguments)
            elif name == "update_ticket":
                result = await update_ticket(**arguments)
            elif name == "create_ticket_with_attachments":
                result = await create_ticket_with_attachments(**arguments)
            elif name == "get_archived_ticket":
                result = await get_archived_ticket(**arguments)
            elif name == "delete_archived_ticket":
                result = await delete_archived_ticket(**arguments)
            elif name == "delete_ticket":
                result = await delete_ticket(**arguments)
            elif name == "delete_multiple_tickets":
                result = await delete_multiple_tickets(**arguments)
            elif name == "delete_attachment":
                result = await delete_attachment(**arguments)

            elif name == "create_contact":
                result = await create_contact(**arguments)
            elif name == "get_contact":
                result = await get_contact(**arguments)
            elif name == "list_contacts":
                result = await list_contacts(**arguments)
            elif name == "update_contact":
                result = await update_contact(**arguments)
            elif name == "delete_contact":
                result = await delete_contact(**arguments)
            elif name == "search_contacts":
                result = await search_contacts(**arguments)
            elif name == "merge_contacts":
                result = await merge_contacts(**arguments)
            elif name == "filter_contacts":
                result = await filter_contacts(**arguments)
            elif name == "make_contact_agent":
                result = await make_contact_agent(**arguments)
            elif name == "restore_contact":
                result = await restore_contact(**arguments)
            elif name == "send_contact_invite":
                result = await send_contact_invite(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            if(result.get("error")):
                logger.error(f"Error executing tool {name}: {result.get('error')}")
                return [types.TextContent(type="text", text=f"Error: {result.get('error')}")]
            
            logger.info(f"Tool {name} executed successfully with arguments: {arguments}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except ValueError as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
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
        try:
            await session_manager.handle_request(scope, receive, send)
        except Exception as e:
            logger.exception(f"Error handling StreamableHTTP request: {e}")

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