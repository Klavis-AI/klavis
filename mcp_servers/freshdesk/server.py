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

    # Context variables
    auth_token_context,
    domain_context,

    # Ticket tools
    create_ticket,
    update_ticket,
    delete_ticket,
    get_ticket_by_id,
    list_tickets,
    add_note_to_ticket,
    filter_tickets,
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
    reply_to_a_ticket,
    update_note,
    delete_note,
    
    # Contact tools

    create_contact,
    get_contact_by_id,
    list_contacts,
    update_contact,
    delete_contact,
    search_contacts_by_name,
    filter_contacts,
    make_contact_agent,
    restore_contact,
    send_contact_invite,
    merge_contacts,

    # Company tools
    create_company,
    get_company_by_id,
    list_companies,
    update_company,
    delete_company,
    filter_companies,
    search_companies_by_name,

    # Account tools
    get_current_account,
    
    # Agent tools
    list_agents,
    get_agent_by_id,
    get_current_agent,
    create_agent,
    update_agent,
    delete_agent,
    search_agents,
    bulk_create_agents,
    
    # Thread tools
    create_thread,
    get_thread_by_id,
    update_thread,
    delete_thread,
    create_thread_message,
    get_thread_message_by_id,
    update_thread_message,
    delete_thread_message
)

# Configure logging
logger = logging.getLogger(__name__)
load_dotenv()
FRESHDESK_MCP_SERVER_PORT = int(os.getenv("FRESHDESK_MCP_SERVER_PORT", "5000"))

def extract_credentials(request_or_scope) -> Dict[str, str]:
    """Extract API key and domain from headers or environment."""
    api_key = os.getenv("API_KEY")
    domain = os.getenv("DOMAIN")
    auth_data = None
    
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
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
    
    # If no API key from environment, try to parse from auth_data
    if not api_key and auth_data:
        try:
            # Parse the JSON auth data to extract token
            auth_json = json.loads(auth_data)
            api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            domain = auth_json.get('domain', '')
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse auth data JSON: {e}")
            api_key = ""
    
    return {
        'api_key': api_key or "",
        'domain': domain or "",
    }


attachment_schema = {
    "type": "array", 
    "items":{
        "type": "object" , 
        "properties": {
            "type": {
                "type": "string", 
                "enum": ["url", "file", "base64", "local"], 
                "default": "local",
                "description": "Type of the attachment (e.g., 'file')."
            }, 
            "content": {
                "type": "string", 
                "description": "Base64 encoded content of the attachment or URL of the attachment."
            },
            "name": {
                "type": "string",
                "description": "Name of the attachment."
            },
            "media_type": {
                "type": "string",
                "description": "Media type of the attachment. Example: 'image/png' or 'application/pdf' or 'text/plain'"
            },
            "encoding": {
                "type": "string",
                "default": "utf-8",
                "description": "Encoding of the attachment content. Default is 'utf-8'."
            }
        }
    }, 
    "description": "List of attachment objects with 'type' and 'content' fields."
}

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
            name="freshdesk_create_ticket",
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
                    "attachments": attachment_schema,
                    "responder_id": {
                        "type": "integer",
                        "description": "ID of the responder."
                    },
                    "parent_id": {
                        "type": "integer",
                        "description": "ID of the parent ticket. If provided, the ticket will be created as a child of the parent ticket."
                    },
                    "company_id": {
                        "type": "integer",
                        "description": "ID of the company to assign the ticket to."
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "ID of the product to assign the ticket to."
                    },
                    "ticket_type": {
                        "type": "string",
                        "description": "Type of the ticket. Helps categorize the ticket according to the different kinds of issues"
                    },
                    "group_id": {
                        "type": "integer",
                        "description": "ID of the group to assign the ticket to."
                    },
                    
                },
                "required": ["subject", "description", "email"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_get_ticket_by_id",
            description="Retrieve a ticket by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket to retrieve (required)."
                    },
                    "include": {
                        "type": "string",
                        "description": "Optional query parameter to include additional data (e.g., 'conversations', 'requester', 'company', 'stats')"
                    }
                },
                "required": ["ticket_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_update_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_delete_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_add_note_to_ticket",
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
                    "user_id": {
                        "type": "integer",
                        "description": "ID of the user adding the note (defaults to authenticated user)."
                    },
                    "incoming": {
                        "type": "boolean",
                        "description": "Whether the note is incoming. Default is false."
                    },
                    "notify_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of email addresses to notify"
                    },
                    "private": {
                        "type": "boolean",
                        "description": "Whether the note is private. Default is false."
                    },
                    "attachments": attachment_schema
                },
                "required": ["ticket_id", "body"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_NOTE"})
        ),
        types.Tool(
            name="freshdesk_reply_to_a_ticket",
            description="Reply to a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "integer",
                        "description": "ID of the ticket (required)."
                    },
                    "body": {
                        "type": "string",
                        "description": "Content of the reply (required)."
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "ID of the user replying (defaults to authenticated user)."
                    },
                    "cc_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of email addresses to CC"
                    },
                    "bcc_emails": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "List of email addresses to BCC"
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Email address to use as the sender"
                    },
                    "attachments": attachment_schema
                },
                "required": ["ticket_id", "body"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_update_note",
            description="Update a note or reply to a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "ID of the note (required)."
                    },
                    "body": {
                        "type": "string",
                        "description": "Content of the note (required)."
                    },
                    "attachments": attachment_schema
                },
                "required": ["note_id", "body"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_NOTE"})
        ),
        types.Tool(
            name="freshdesk_delete_note",
            description="Delete a note or reply to a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "integer",
                        "description": "ID of the note (required)."
                    }
                },
                "required": ["note_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_NOTE"})
        ),
        types.Tool(
            name="freshdesk_forward_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_get_archived_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_delete_archived_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_filter_tickets", 
            description="Use ticket fields to filter through tickets and get a list of tickets matching the specified ticket fields.", 
            inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query string to filter tickets (required). Format - (ticket_field:integer OR ticket_field:'string') AND ticket_field:boolean"
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
        },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_create_ticket_with_attachments",
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
                    "attachments": attachment_schema,
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_ATTACHMENT"})
        ),
        types.Tool(
            name="freshdesk_delete_multiple_tickets",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_delete_attachment",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_ATTACHMENT"})
        ),
        types.Tool(
            name="freshdesk_list_tickets",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_merge_tickets",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_restore_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_watch_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_unwatch_ticket",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_TICKET"})
        ),
        types.Tool(
            name="freshdesk_create_contact",
            description="Create a new contact in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string", 
                        "description": "Name of the contact"
                    },
                    "email": {
                        "type": "string", 
                        "format": "email", 
                        "description": "Primary email address"
                    },
                    "phone": {
                        "type": "string", 
                        "description": "Telephone number"
                    },
                    "company_id": {
                        "type": "integer", 
                        "description": "ID of the company"
                    },
                    "description": {
                        "type": "string", 
                        "description": "Description of the contact"
                    }
                },
                "required": ["name"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_get_contact_by_id",
            description="Retrieve a contact by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to retrieve"}
                },
                "required": ["contact_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_list_contacts",
            description="List all contacts, optionally filtered by parameters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string", 
                        "format": "email", 
                        "description": "Filter by email"
                    },
                    "phone": {
                        "type": "string", 
                        "description": "Filter by phone number"
                    },
                    "mobile": {
                        "type": "string", 
                        "description": "Filter by mobile number"
                    },
                    "company_id": {
                        "type": "integer", 
                        "description": "Filter by company ID"
                    },
                    "state": {
                        "type": "string", 
                        "description": "Filter by state (verified, unverified, blocked, deleted)"
                    },
                    "updated_since": {
                        "type": "string", 
                        "description": "Filter by last updated date (ISO 8601 format)"
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_update_contact",
            description="Update an existing contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "integer", 
                        "description": "ID of the contact to update"
                    },
                    "name": {
                        "type": "string", 
                        "description": "New name"
                    },
                    "email": {
                        "type": "string", 
                        "format": "email", 
                        "description": "New primary email"
                    },
                    "phone": {
                        "type": "string", 
                        "description": "New phone number"
                    },
                    "mobile": {
                        "type": "string", 
                        "description": "New mobile number"
                    },
                    "company_id": {
                        "type": "integer", 
                        "description": "New company ID"
                    },
                    "description": {
                        "type": "string", 
                        "description": "New description"
                    },
                    "job_title": {
                        "type": "string", 
                        "description": "New job title"
                    },
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"}, 
                        "description": "Updated list of tags"
                    },
                    "custom_fields": {
                        "type": "object", 
                        "description": "Updated custom fields"
                    },
                    "avatar_path": {
                        "type": "string", 
                        "description": "Path to new avatar image file"
                    },
                    "address": {
                        "type": "string", 
                        "description": "Address of the contact"
                    }
                },
                "required": ["contact_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_delete_contact",
            description="Delete a contact. Set hard_delete=True to permanently delete.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {
                        "type": "integer", 
                        "description": "ID of the contact to delete"
                    },
                    "hard_delete": {
                        "type": "boolean", 
                        "default": False, 
                        "description": "If true, permanently delete the contact"
                    },
                    "force": {
                        "type": "boolean", 
                        "default": False, 
                        "description": "If true, force hard delete even if not soft deleted first"
                    }
                },
                "required": ["contact_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_search_contacts_by_name",
            description="Search for contacts by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the contact to search for"}
                },
                "required": ["name"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_filter_contacts",
            description="Filter contacts by fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Filter query using this format - contact_field:integer OR contact_field:'string' AND contact_field:boolean e.g. {query: 'field_name:field_value'} - name:John Doe"
                    },
                    "page": {
                        "type": "integer", 
                        "description": "Page number (1-based)", 
                        "default": 1
                    },
                    "updated_since": {
                        "type": "string", 
                        "description": "Filter by last updated date (ISO 8601 format)"
                    }
                },
                "required": ["query"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT", "readOnlyHint": True})
        ),
        types.Tool(
            name="freshdesk_make_contact_agent",
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
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_restore_contact",
            description="Restore a deleted contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to restore"}
                },
                "required": ["contact_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_send_contact_invite",
            description="Send an invite to a contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer", "description": "ID of the contact to send an invite to"}
                },
                "required": ["contact_id"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_merge_contacts",
            description="Merge multiple contacts into a primary contact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_contact_id": {
                        "type": "integer", 
                        "description": "ID of the primary contact to merge into"
                    },
                    "secondary_contact_ids": {
                        "type": "array", 
                        "items": {"type": "integer"}, 
                        "description": "List of contact IDs to merge into the primary contact"
                    },
                    "contact_data": {
                        "type": "object", 
                        "description": "Optional dictionary of fields to update on the primary contact",
                        "properties": {
                            "email": {
                                "type": "string", 
                                "description": "Primary email address of the contact."
                            },
                            "phone": {
                                "type": "string", 
                                "description": "Phone number of the contact."
                            }, 
                            "mobile": {
                                "type": "string", 
                                "description": "Mobile number of the contact."
                            },
                            "company_ids": {
                                "type": "array", 
                                "items": {"type": "integer"}, 
                                "description": "IDs of the companies associated with the contact"
                            },
                            "other_emails": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "Additional emails associated with the contact"
                            },
                        }
                    }
                },
                "required": ["primary_contact_id", "secondary_contact_ids"]
            },
            annotations=types.ToolAnnotations(**{"category": "FRESHDESK_CONTACT"})
        ),
        types.Tool(
            name="freshdesk_create_company",
            description="Create a new company in Freshdesk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                            "type": "string",
                            "description": "Name of the company (required, unique)"
                        },
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of company domains"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the company"
                        },
                        "note": {
                            "type": "string",
                            "description": "Any specific note about the company"
                        },
                        "health_score": {
                            "type": "string",
                            "description": "Health score of the company"
                        },
                        "account_tier": {
                            "type": "string",
                            "description": "Account tier of the company"
                        },
                        "renewal_date": {
                            "type": "string",
                            "description": "Contract renewal date (YYYY-MM-DD)"
                        },
                        "industry": {
                            "type": "string",
                            "description": "Industry the company serves in"
                        },
                        "custom_fields": {
                            "type": "object",
                            "description": "Dictionary of custom field values"
                        },
                        "lookup_parameter": {
                            "type": "string",
                            "enum": ["display_id", "primary_field_value"],
                            "default": "display_id",
                            "description": "Lookup parameter type for custom objects"
                        }
                    },
                    "required": ["name"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY"})
            ),
            types.Tool(
                name="freshdesk_get_company_by_id",
                description="Retrieve a company by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "ID of the company to retrieve (required)."
                        }
                    },
                    "required": ["company_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_list_companies",
                description="List all companies with optional filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "updated_since": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Filter companies updated since this date (ISO 8601 format)"
                        },
                        "page": {
                            "type": "integer",
                            "minimum": 1,
                            "default": 1,
                            "description": "Page number (1-based)"
                        },
                        "per_page": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 30,
                            "description": "Number of records per page (max 100)"
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_update_company",
                description="Update an existing company.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "ID of the company to update (required)."
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the company"
                        },
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains (will replace existing domains if provided)"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description"
                        },
                        "note": {
                            "type": "string",
                            "description": "New note"
                        },
                        "health_score": {
                            "type": "string",
                            "description": "Updated health score"
                        },
                        "account_tier": {
                            "type": "string",
                            "description": "Updated account tier"
                        },
                        "renewal_date": {
                            "type": "string",
                            "description": "New renewal date (YYYY-MM-DD)"
                        },
                        "industry": {
                            "type": "string",
                            "description": "Updated industry"
                        },
                        "custom_fields": {
                            "type": "object",
                            "description": "Dictionary of custom field values to update"
                        },
                        "lookup_parameter": {
                            "type": "string",
                            "enum": ["display_id", "primary_field_value"],
                            "description": "Lookup parameter type for custom objects"
                        }
                    },
                    "required": ["company_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY"})
            ),
            types.Tool(
                name="freshdesk_delete_company",
                description="Delete a company from Freshdesk.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {
                            "type": "integer",
                            "description": "ID of the company to delete (required)."
                        }
                    },
                    "required": ["company_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY"})
            ),
            types.Tool(
                name="freshdesk_filter_companies",
                description="Filter companies using a query string. ",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query string to filter companies (domain, created_at, updated_at, custom fields) - company_field:integer OR company_field:'string' AND company_field:boolean e.g. {query: 'field_name:field_value'} - domain:Example"
                        },
                        "page": {
                            "type": "integer",
                            "minimum": 1,
                            "default": 1,
                            "description": "Page number (1-based)"
                        },
                        "per_page": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 30,
                            "default": 30,
                            "description": "Number of records per page (max 30)"
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY"})
            ),
            types.Tool(
                name="freshdesk_search_companies_by_name",
                description="Search for companies by name (autocomplete).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Search name (case-insensitive) (required)."
                        }
                    },
                    "required": ["name"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_COMPANY", "readOnlyHint": True})
            ),

            types.Tool(
                name="freshdesk_get_current_account",
                description="Retrieve the current account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_ACCOUNT", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_list_agents",
                description="List all agents with optional filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string", 
                            "description": "Filter by email address"
                        },
                        "mobile": {
                            "type": "string", 
                            "description": "Filter by mobile number"
                        },
                        "phone": {
                            "type": "string", 
                            "description": "Filter by phone number"
                        },
                        "state": {
                            "type": "string", 
                            "enum": ["fulltime", "occasional"], 
                            "description": "Filter by agent state"
                        },
                        "page": {
                            "type": "integer", 
                            "description": "Page number (1-based)", 
                            "default": 1
                        },
                        "per_page": {
                            "type": "integer", 
                            "description": "Number of results per page (max 100)", 
                            "default": 30
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_get_agent_by_id",
                description="Get details of a specific agent by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "integer", 
                            "description": "ID of the agent to retrieve"
                        },
                    },
                    "required": ["agent_id"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_get_current_agent",
                description="Get details of the currently authenticated agent",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_create_agent",
                description="Create a new agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string", 
                            "description": "Email address of the agent"
                        },
                        "name": {
                            "type": "string", 
                            "description": "Name of the agent"
                        },
                        "ticket_scope": {
                            "type": "integer", 
                            "enum": [1, 2, 3], 
                            "description": "Ticket permission (1=Global, 2=Group, 3=Restricted)"
                        },
                        "role_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "List of role IDs for the agent"
                        },
                        "group_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "List of group IDs the agent belongs to"
                        },
                        "skill_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "List of skill IDs for the agent"
                        },
                        "occasional": {
                            "type": "boolean", 
                            "description": "Whether the agent is occasional (True) or full-time (False)", 
                            "default": False
                        },
                        "signature": {
                            "type": "string", 
                            "description": "HTML signature for the agent"
                        },
                        "language": {
                            "type": "string", 
                            "description": "Language code (default: 'en')", 
                            "default": "en"
                        },
                        "time_zone": {
                            "type": "string", 
                            "description": "Time zone for the agent"
                        },
                        "agent_type": {
                            "type": "integer", 
                            "enum": [1, 2, 3], 
                            "description": "Type of agent (1=Support, 2=Field, 3=Collaborator)", 
                            "default": 1
                        },
                        "focus_mode": {
                            "type": "boolean", 
                            "description": "Whether focus mode is enabled", 
                            "default": True
                        },
                    },
                    "required": ["email", "name", "ticket_scope", "role_ids"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT"})
            ),
            types.Tool(
                name="freshdesk_update_agent",
                description="Update an existing agent",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "integer", 
                            "description": "ID of the agent to update"
                        },
                        "email": {
                            "type": "string", 
                            "description": "New email address"
                        },
                        "ticket_scope": {
                            "type": "integer", 
                            "enum": [1, 2, 3], 
                            "description": "New ticket permission (1=Global, 2=Group, 3=Restricted)"
                        },
                        "role_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "New list of role IDs"
                        },
                        "group_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "New list of group IDs"
                        },
                        "skill_ids": {
                            "type": "array", 
                            "items": {"type": "integer"}, 
                            "description": "New list of skill IDs"
                        },
                        "occasional": {
                            "type": "boolean", 
                            "description": "Whether the agent is occasional"
                        },
                        "signature": {
                            "type": "string", 
                            "description": "New HTML signature"
                        },
                        "language": {
                            "type": "string", 
                            "description": "New language code"
                        },
                        "time_zone": {
                            "type": "string", 
                            "description": "New time zone"
                        },
                        "focus_mode": {
                            "type": "boolean", 
                            "description": "Whether focus mode is enabled"
                        },
                    },
                    "required": ["agent_id"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT"})
            ),
            types.Tool(
                name="freshdesk_delete_agent",
                description="Delete an agent (downgrades to contact)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "integer", "description": "ID of the agent to delete"},
                    },
                    "required": ["agent_id"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT"})
            ),
            types.Tool(
                name="freshdesk_search_agents",
                description="Search for agents by name or email",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {"type": "string", "description": "Search term (name or email)"},
                    },
                    "required": ["term"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT", "readOnlyHint": True})
            ),
            types.Tool(
                name="freshdesk_bulk_create_agents",
                description="Create multiple agents in bulk",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agents_data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "email": {
                                        "type": "string", 
                                        "description": "Email address of the agent"
                                    },
                                    "name": {
                                        "type": "string", 
                                        "description": "Name of the agent"
                                    },
                                    "ticket_scope": {
                                        "type": "integer", 
                                        "enum": [1, 2, 3], 
                                        "description": "Ticket permission (1=Global, 2=Group, 3=Restricted)"
                                    },
                                    "role_ids": {
                                        "type": "array", 
                                        "items": {"type": "integer"}, 
                                        "description": "List of role IDs for the agent"
                                    },
                                    "group_ids": {
                                        "type": "array", 
                                        "items": {"type": "integer"}, 
                                        "description": "List of group IDs the agent belongs to"
                                    },
                                    "skill_ids": {
                                        "type": "array", 
                                        "items": {"type": "integer"}, 
                                        "description": "List of skill IDs for the agent"
                                    },
                                    "occasional": {
                                        "type": "boolean", 
                                        "description": "Whether the agent is occasional (True) or full-time (False)"
                                    },
                                    "signature": {
                                        "type": "string", 
                                        "description": "HTML signature for the agent"
                                    },
                                    "language": {
                                        "type": "string", 
                                        "description": "Language code (default: 'en')"
                                    },
                                    "time_zone": {
                                        "type": "string", 
                                        "description": "Time zone for the agent"
                                    },
                                    "agent_type": {
                                        "type": "integer", 
                                        "description": "Type of agent (1=Support, 2=Field, 3=Collaborator)"
                                    },
                                    "focus_mode": {
                                        "type": "boolean", 
                                        "description": "Whether focus mode is enabled (default: True)"
                                    },
                                },
                                "required": ["email", "name", "ticket_scope", "role_ids"],
                            },
                            "description": "List of agent data objects",
                        },
                    },
                    "required": ["agents_data"],
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_AGENT"})
            ),
            
            # Thread tools
            types.Tool(
                name="freshdesk_create_thread",
                description="Create a new thread in Freshdesk.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_type": {
                            "type": "string",
                            "enum": ["forward", "discussion", "private"],
                            "description": "Type of thread (forward, discussion, private)"
                        },
                        "parent_id": {
                            "type": "integer",
                            "description": "ID of the parent object (usually ticket)"
                        },
                        "parent_type": {
                            "type": "string",
                            "default": "ticket",
                            "description": "Type of parent object (default: ticket)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the thread"
                        },
                        "created_by": {
                            "type": "string",
                            "description": "ID of the user creating the thread"
                        },
                        "anchor_id": {
                            "type": "integer",
                            "description": "ID of the anchor object (e.g., conversation ID)"
                        },
                        "anchor_type": {
                            "type": "string",
                            "description": "Type of anchor object (e.g., conversation)"
                        },
                        "participants_emails": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses of participants"
                        },
                        "participants_agents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of agent IDs of participants"
                        },
                        "additional_info": {
                            "type": "object",
                            "description": "Additional information like email_config_id"
                        }
                    },
                    "required": ["thread_type", "parent_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_get_thread_by_id",
                description="Get a thread by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "integer",
                            "description": "ID of the thread to retrieve"
                        }
                    },
                    "required": ["thread_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_update_thread",
                description="Update a thread in Freshdesk.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "integer",
                            "description": "ID of the thread to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the thread"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the thread"
                        }
                    },
                    "required": ["thread_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_delete_thread",
                description="Delete a thread from Freshdesk. Note: This is an irreversible action!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "integer",
                            "description": "ID of the thread to delete"
                        }
                    },
                    "required": ["thread_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD", "readOnlyHint": True})
            ),
            
            types.Tool(
                name="freshdesk_create_thread_message",
                description="Create a new message for a thread.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "integer",
                            "description": "ID of the thread to add message to"
                        },
                        "body": {
                            "type": "string",
                            "description": "HTML content of the message"
                        },
                        "body_text": {
                            "type": "string",
                            "description": "Plain text content of the message"
                        },
                        "attachment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of attachment IDs to include"
                        },
                        "inline_attachment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of inline attachment IDs"
                        },
                        "participants_email_to": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses to send to"
                        },
                        "participants_email_cc": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses to CC"
                        },
                        "participants_email_bcc": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses to BCC"
                        },
                        "participants_email_from": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address to send from"
                        },
                        "additional_info": {
                            "type": "object",
                            "description": "Additional information like has_quoted_text, email_subject"
                        },
                        "full_message": {
                            "type": "string",
                            "description": "HTML content with original and quoted text"
                        },
                        "full_message_text": {
                            "type": "string",
                            "description": "Plain text with quoted text"
                        }
                    },
                    "required": ["thread_id", "body"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_get_thread_message_by_id",
                description="Get a thread message by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "integer",
                            "description": "ID of the message to retrieve"
                        }
                    },
                    "required": ["message_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_update_thread_message",
                description="Update a thread message.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "integer",
                            "description": "ID of the message to update"
                        },
                        "body": {
                            "type": "string",
                            "description": "New HTML content of the message"
                        },
                        "body_text": {
                            "type": "string",
                            "description": "New plain text content of the message"
                        },
                        "attachment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "New list of attachment IDs"
                        },
                        "inline_attachment_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "New list of inline attachment IDs"
                        },
                        "additional_info": {
                            "type": "object",
                            "description": "New additional information"
                        }
                    },
                    "required": ["message_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
            
            types.Tool(
                name="freshdesk_delete_thread_message",
                description="Delete a thread message. Note: This is an irreversible action!",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "integer",
                            "description": "ID of the message to delete"
                        }
                    },
                    "required": ["message_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "FRESHDESK_THREAD"})
            ),
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:

            if name == "freshdesk_create_ticket":
                result = await create_ticket(**arguments)
            elif name == "freshdesk_get_ticket_by_id":
                result = await get_ticket_by_id(**arguments)
            elif name == "freshdesk_list_tickets":
                result = await list_tickets(**arguments)
            elif name == "freshdesk_filter_tickets":
                result = await filter_tickets(**arguments)
            elif name == "freshdesk_add_note_to_ticket":
                result = await add_note_to_ticket(**arguments)
            elif name == "freshdesk_reply_to_a_ticket":
                result = await reply_to_a_ticket(**arguments)
            elif name == "freshdesk_update_note":
                result = await update_note(**arguments)
            elif name == "freshdesk_delete_note":
                result = await delete_note(**arguments)
            elif name == "freshdesk_merge_tickets":
                result = await merge_tickets(**arguments)
            elif name == "freshdesk_restore_ticket":
                result = await restore_ticket(**arguments)
            elif name == "freshdesk_watch_ticket":
                result = await watch_ticket(**arguments)
            elif name == "freshdesk_unwatch_ticket":
                result = await unwatch_ticket(**arguments)
            elif name == "freshdesk_forward_ticket":
                result = await forward_ticket(**arguments)
            elif name == "freshdesk_update_ticket":
                result = await update_ticket(**arguments)
            elif name == "freshdesk_create_ticket_with_attachments":
                result = await create_ticket_with_attachments(**arguments)
            elif name == "freshdesk_get_archived_ticket":
                result = await get_archived_ticket(**arguments)
            elif name == "freshdesk_delete_archived_ticket":
                result = await delete_archived_ticket(**arguments)
            elif name == "freshdesk_delete_ticket":
                result = await delete_ticket(**arguments)
            elif name == "freshdesk_delete_multiple_tickets":
                result = await delete_multiple_tickets(**arguments)
            elif name == "freshdesk_delete_attachment":
                result = await delete_attachment(**arguments)

            elif name == "freshdesk_create_contact":
                result = await create_contact(**arguments)
            elif name == "freshdesk_get_contact_by_id":
                result = await get_contact_by_id(**arguments)
            elif name == "freshdesk_list_contacts":
                result = await list_contacts(**arguments)
            elif name == "freshdesk_update_contact":
                result = await update_contact(**arguments)
            elif name == "freshdesk_delete_contact":
                result = await delete_contact(**arguments)
            elif name == "freshdesk_search_contacts_by_name":
                result = await search_contacts_by_name(**arguments)
            elif name == "freshdesk_merge_contacts":
                result = await merge_contacts(**arguments)
            elif name == "freshdesk_filter_contacts":
                result = await filter_contacts(**arguments)
            elif name == "freshdesk_make_contact_agent":
                result = await make_contact_agent(**arguments)
            elif name == "freshdesk_restore_contact":
                result = await restore_contact(**arguments)
            elif name == "freshdesk_send_contact_invite":
                result = await send_contact_invite(**arguments)

            elif name == "freshdesk_create_company":
                result = await create_company(**arguments)
            elif name == "freshdesk_get_company_by_id":
                result = await get_company_by_id(**arguments)
            elif name == "freshdesk_list_companies":
                result = await list_companies(**arguments)
            elif name == "freshdesk_update_company":
                result = await update_company(**arguments)
            elif name == "freshdesk_delete_company":
                result = await delete_company(**arguments)
            elif name == "freshdesk_filter_companies":
                result = await filter_companies(**arguments)
            elif name == "freshdesk_search_companies_by_name":
                result = await search_companies_by_name(**arguments)
                
            elif name == "freshdesk_get_current_account":
                result = await get_current_account()

            elif name == "freshdesk_get_current_agent":
                result = await get_current_agent()
            elif name == "freshdesk_get_agent_by_id":
                result = await get_agent_by_id(**arguments)
            elif name == "freshdesk_list_agents":
                result = await list_agents(**arguments)
            elif name == "freshdesk_create_agent":
                result = await create_agent(**arguments)
            elif name == "freshdesk_update_agent":
                result = await update_agent(**arguments)
            elif name == "freshdesk_delete_agent":
                result = await delete_agent(**arguments)
            elif name == "freshdesk_search_agents":
                result = await search_agents(**arguments)
            elif name == "freshdesk_bulk_create_agents":
                result = await bulk_create_agents(**arguments)
                
            # Thread tools
            elif name == "freshdesk_create_thread":
                result = await create_thread(**arguments)
            elif name == "freshdesk_get_thread_by_id":
                result = await get_thread_by_id(**arguments)
            elif name == "freshdesk_update_thread":
                result = await update_thread(**arguments)
            elif name == "freshdesk_delete_thread":
                result = await delete_thread(**arguments)
            elif name == "freshdesk_create_thread_message":
                result = await create_thread_message(**arguments)
            elif name == "freshdesk_get_thread_message_by_id":
                result = await get_thread_message_by_id(**arguments)
            elif name == "freshdesk_update_thread_message":
                result = await update_thread_message(**arguments)
            elif name == "freshdesk_delete_thread_message":
                result = await delete_thread_message(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            if isinstance(result, dict) and result.get("error") :
                logger.error(f"Error executing tool {name}: {result.get('error')}")
                return [types.TextContent(type="text", text=f"{result.get('error')}")]
            
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
        
        # Extract credentials (API key, domain, auth token) from headers
        credentials = extract_credentials(request)
        
        # Set the API key, auth token and domain in context for this request
        auth_token = auth_token_context.set(credentials['api_key'])
        domain_token = domain_context.set(credentials['domain'])
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            auth_token_context.reset(auth_token)
            domain_context.reset(domain_token)
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
        
        # Extract credentials (API key, domain, auth token) from headers
        credentials = extract_credentials(scope)
        
         # Set the API key, auth token and domain in context for this request
        auth_token = auth_token_context.set(credentials['api_key'])
        domain_token = domain_context.set(credentials['domain'])

        try:
            await session_manager.handle_request(scope, receive, send)
        except Exception as e:
            logger.exception(f"Error handling StreamableHTTP request: {e}")
        finally:
           auth_token_context.reset(auth_token)
           domain_context.reset(domain_token)

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