import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import List
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

    # mailFolder
    outlookMail_delete_folder,
    outlookMail_create_mail_folder,
    outlookMail_list_folders,
    outlookMail_get_mail_folder_details,
    outlookMail_update_folder_display_name,

    # messages
    outlookMail_read_message,
    outlookMail_send_draft,
    outlookMail_create_reply_all_draft,
    outlookMail_list_messages,
    outlookMail_create_draft,
    outlookMail_create_reply_draft,
    outlookMail_delete_draft,
    outlookMail_update_draft,
    outlookMail_create_forward_draft,
    outlookMail_list_messages_from_folder,
    outlookMail_move_message
)



# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

OUTLOOK_MCP_SERVER_PORT = int(os.getenv("OUTLOOK_MCP_SERVER_PORT", "5000"))

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
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""

@click.command()
@click.option("--port", default=OUTLOOK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("outlookMail-mcp-server")
#-------------------------------------------------------------------
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # File Operations
            # mailfolder.py----------------------------------------------
            types.Tool(
                name="outlookMail_delete_folder",
                description="Delete an Outlook mail folder by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "The ID of the folder to delete"}
                    },
                    "required": ["folder_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_FOLDER"})
            ),
            types.Tool(
                name="outlookMail_create_mail_folder",
                description="Create a new mail folder in the signed-in user's mailbox.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "display_name": {"type": "string", "description": "The name of the new folder"},
                        "is_hidden": {"type": "boolean", "description": "Whether the folder is hidden (default False)"}
                    },
                    "required": ["display_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_FOLDER"})
            ),
            types.Tool(
                name="outlookMail_list_folders",
                description="List mail folders in the signed-in user's mailbox.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_hidden": {"type": "boolean",
                                           "description": "Whether to include hidden folders (default True)"}
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_FOLDER", "readOnlyHint": True})
            ),

            types.Tool(
                name="outlookMail_get_mail_folder_details",
                description="Get details of a specific mail folder by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Unique ID of the mail folder"}
                    },
                    "required": ["folder_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_FOLDER", "readOnlyHint": True})
            ),

            types.Tool(
                name="outlookMail_update_folder_display_name",
                description="Update the display name of an Outlook mail folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "ID of the mail folder to update"},
                        "display_name": {"type": "string", "description": "New display name"}
                    },
                    "required": ["folder_id", "display_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_FOLDER"})
            ),

            #messages.py-----------------------------------------------------------
            types.Tool(
                name="outlookMail_read_message",
                description="Get a specific Outlook mail message by its ID using Microsoft Graph API.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to retrieve"
                        }
                    },
                    "required": ["message_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE", "readOnlyHint": True})
            ),
            types.Tool(
                name="outlookMail_list_messages",
                description="Retrieve a list of Outlook mail messages from the signed-in user's mailbox",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "top": {
                            "type": "integer",
                            "description": "The maximum number of messages to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "OData $filter expression to filter messages",
                            "examples": [
                                "isRead eq false",
                                "importance eq 'high'",
                                "from/emailAddress/address eq 'example@example.com'",
                                "subject eq 'Welcome'",
                                "receivedDateTime ge 2025-07-01T00:00:00Z",
                                "hasAttachments eq true",
                                "isRead eq false and importance eq 'high'"
                            ]
                        },
                        "orderby": {
                            "type": "string",
                            "description": "OData $orderby expression to sort results",
                            "examples": [
                                "receivedDateTime desc",
                                "subject asc"
                            ]
                        },
                        "select": {
                            "type": "string",
                            "description": "Comma-separated list of fields to include in response",
                            "examples": [
                                "subject,from,receivedDateTime",
                                "id,subject,bodyPreview,isRead"
                            ]
                        }
                    },
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE", "readOnlyHint": True})
            ),
            types.Tool(
                name="outlookMail_list_messages_from_folder",
                description="Retrieve a list of Outlook mail messages from a specific folder in the signed-in user's mailbox",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the Outlook mail folder to retrieve messages from"
                        },
                        "top": {
                            "type": "integer",
                            "description": "The maximum number of messages to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "OData $filter expression to filter messages",
                            "examples": [
                                "isRead eq false",
                                "importance eq 'high'",
                                "from/emailAddress/address eq 'example@example.com'",
                                "subject eq 'Welcome'",
                                "receivedDateTime ge 2025-07-01T00:00:00Z",
                                "hasAttachments eq true",
                                "isRead eq false and importance eq 'high'"
                            ]
                        },
                        "orderby": {
                            "type": "string",
                            "description": "OData $orderby expression to sort results",
                            "examples": [
                                "receivedDateTime desc",
                                "subject asc"
                            ]
                        },
                        "select": {
                            "type": "string",
                            "description": "Comma-separated list of fields to include in response",
                            "examples": [
                                "subject,from,receivedDateTime",
                                "id,subject,bodyPreview,isRead"
                            ]
                        }
                    },
                    "required": ["folder_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE", "readOnlyHint": True})
            ),
            types.Tool(
                name="outlookMail_update_draft",
                description="Updates an existing Outlook draft message using Microsoft Graph API (PATCH method)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the draft message to update"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Message subject (only updatable in draft state)"
                        },
                        "body_content": {
                            "type": "string",
                            "description": "HTML content of the message body (only updatable in draft state)"
                        },
                        "to_recipients": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Recipient email addresses for 'To' (only updatable in draft state)"
                        },
                        "cc_recipients": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Recipient email addresses for 'Cc' (only updatable in draft state)"
                        },
                        "bcc_recipients": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Recipient email addresses for 'Bcc' (only updatable in draft state)"
                        }
                    },
                    "required": ["message_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),

            types.Tool(
                name="outlookMail_delete_draft",
                description="Delete an existing Outlook draft message by message ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the draft message to delete"
                        }
                    },
                    "required": ["message_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_create_forward_draft",
                description="Create a draft forward message for an existing Outlook message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the original message to forward"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Comment to include in the forwarded message"
                        },
                        "to_recipients": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of recipient email addresses"
                        }
                    },
                    "required": ["message_id", "comment", "to_recipients"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_create_reply_draft",
                description="Create a draft reply message to an existing Outlook message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the original message to reply to"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Comment to include in the reply"
                        }
                    },
                    "required": ["message_id", "comment"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_create_reply_all_draft",
                description="Create a reply-all draft to an existing Outlook message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to reply to"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Text to include in the reply body",
                            "default": ""
                        }
                    },
                    "required": ["message_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_send_draft",
                description="Send an existing draft Outlook mail message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "The ID of the draft message to send"}
                    },
                    "required": ["message_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_create_draft",
                description="Create a draft Outlook mail message using Microsoft Graph API (POST method)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Subject of the draft message"
                        },
                        "body_content": {
                            "type": "string",
                            "description": "HTML content of the message body"
                        },
                        "to_recipients": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of email addresses for the 'To' field"
                        },
                        "cc_recipients": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of email addresses for 'Cc'"
                        },
                        "bcc_recipients": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of email addresses for 'Bcc'"
                        }
                    },
                    "required": ["subject", "body_content", "to_recipients"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            ),
            types.Tool(
                name="outlookMail_move_message",
                description="Move an Outlook mail message to another folder by folder ID or well-known name like 'deleteditems'.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message to move"
                        },
                        "destination_folder_id": {
                            "type": "string",
                            "description": "ID of the destination folder (e.g. 'deleteditems' or a custom folder ID)"
                        }
                    },
                    "required": ["message_id", "destination_folder_id"],
                    "additionalProperties": False
                },
                annotations=types.ToolAnnotations(**{"category": "OUTLOOK_MESSAGE"})
            )

        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        # Mail Folder Operations
        if name == "outlookMail_delete_folder":
            try:
                result = await outlookMail_delete_folder(
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_mail_folder":
            try:
                result = await outlookMail_create_mail_folder(
                    display_name=arguments["display_name"],
                    is_hidden=arguments.get("is_hidden", False)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating mail folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_list_folders":
            try:
                result = await outlookMail_list_folders(
                    include_hidden=arguments.get("include_hidden", True)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing folders: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_mail_folder_details":
            try:
                result = await outlookMail_get_mail_folder_details(
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_folder_display_name":
            try:
                result = await outlookMail_update_folder_display_name(
                    folder_id=arguments["folder_id"],
                    display_name=arguments["display_name"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating folder display name: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Message Operations
        elif name == "outlookMail_read_message":
            try:
                result = await outlookMail_read_message(
                    message_id=arguments["message_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]

        elif name == "outlookMail_list_messages":
            try:
                result = await outlookMail_list_messages(
                    top=arguments.get("top", 10),
                    filter_query=arguments.get("filter_query"),
                    orderby=arguments.get("orderby"),
                    select=arguments.get("select")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing messages: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_list_messages_from_folder":
            try:
                result = await outlookMail_list_messages_from_folder(
                    folder_id=arguments["folder_id"],
                    top=arguments.get("top", 10),
                    filter_query=arguments.get("filter_query"),
                    orderby=arguments.get("orderby"),
                    select=arguments.get("select")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing messages from folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_draft":
            try:
                result = await outlookMail_update_draft(
                    message_id=arguments["message_id"],
                    subject=arguments.get("subject"),
                    body_content=arguments.get("body_content"),
                    to_recipients=arguments.get("to_recipients"),
                    cc_recipients=arguments.get("cc_recipients"),
                    bcc_recipients=arguments.get("bcc_recipients"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Message Operations
        elif name == "outlookMail_delete_draft":
            try:
                result = await outlookMail_delete_draft(
                    message_id=arguments["message_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_forward_draft":
            try:
                result = await outlookMail_create_forward_draft(
                    message_id=arguments["message_id"],
                    comment=arguments["comment"],
                    to_recipients=arguments["to_recipients"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating forward draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_reply_draft":
            try:
                result = await outlookMail_create_reply_draft(
                    message_id=arguments["message_id"],
                    comment=arguments["comment"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating reply draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_reply_all_draft":
            try:
                result = await outlookMail_create_reply_all_draft(
                    message_id=arguments["message_id"],
                    comment=arguments.get("comment", "")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating reply-all draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_send_draft":
            try:
                result = await outlookMail_send_draft(
                    message_id=arguments["message_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error sending draft: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_draft":
            try:
                result = await outlookMail_create_draft(
                    subject=arguments["subject"],
                    body_content=arguments["body_content"],
                    to_recipients=arguments["to_recipients"],
                    cc_recipients=arguments.get("cc_recipients"),
                    bcc_recipients=arguments.get("bcc_recipients"),
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating draft message: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "outlookMail_move_message":
            try:
                result = await outlookMail_move_message(
                    message_id=arguments["message_id"],
                    destination_folder_id=arguments["destination_folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error moving message: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
    #-------------------------------------------------------------------------

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        # Extract access token using standard method
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

        # Extract access token using standard method
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