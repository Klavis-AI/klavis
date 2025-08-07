import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import List

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

    # attachments
    outlookMail_add_attachment,
    outlookMail_list_attachments,
    outlookMail_get_attachment_details,
    outlookMail_download_attachment,
    outlookMail_delete_attachment,
    outlookMail_upload_large_attachment,

    # mailFolder
    outlookMail_delete_folder,
    outlookMail_create_mail_folder,
    outlookMail_list_folders,
    outlookMail_get_mail_folder,
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
            # attachment.py----------------------------------------------------------
            types.Tool(
                name="outlookMail_add_attachment",
                description="Add an attachment to a draft Outlook mail message by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the draft message to which the file will be attached"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the local file to attach"
                        },
                        "attachment_name": {
                            "type": "string",
                            "description": "Optional custom name for the attachment; defaults to the file's basename"
                        }
                    },
                    "required": ["message_id", "file_path"]
                }
            ),
            types.Tool(
                name="outlookMail_list_attachments",
                description="List attachments from an Outlook mail message by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message to list attachments from"
                        }
                    },
                    "required": ["message_id"]
                }
            ),
            types.Tool(
                name="outlookMail_get_attachment_details",
                description="Get a specific attachment from an Outlook mail message by message ID and attachment ID. Optionally expand related entities.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message that has the attachment"
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "ID of the attachment to retrieve"
                        },
                        "expand": {
                            "type": "string",
                            "description": "OData $expand expression to include related entities (e.g., 'microsoft.graph.itemattachment/item')"
                        }
                    },
                    "required": ["message_id", "attachment_id"]
                }
            ),
            types.Tool(
                name="outlookMail_download_attachment",
                description="Download an attachment from Outlook mail as raw binary using $value and save it locally.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message that has the attachment"
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "ID of the attachment to download"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Local file path to save the downloaded attachment"
                        }
                    },
                    "required": ["message_id", "attachment_id", "save_path"]
                }
            ),
            types.Tool(
                name="outlookMail_delete_attachment",
                description="Delete an attachment from a draft Outlook mail message.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message containing the attachment"
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "ID of the attachment to delete"
                        }
                    },
                    "required": ["message_id", "attachment_id"]
                }
            ),
            types.Tool(
                name="outlookMail_upload_large_attachment",
                description="Upload a large file attachment to a draft message using an upload session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the draft message to attach the file to"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Local path to the file"
                        },
                        "is_inline": {
                            "type": "boolean",
                            "description": "If True, marks the attachment as inline",
                            "default": False
                        },
                        "content_id": {
                            "type": "string",
                            "description": "Content-ID for inline images (optional)"
                        }
                    },
                    "required": ["message_id", "file_path"]
                }
            ),

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
                }
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
                }
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
                }
            ),

            types.Tool(
                name="outlookMail_get_mail_folder",
                description="Get details of a specific mail folder by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "Unique ID of the mail folder"}
                    },
                    "required": ["folder_id"]
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
            )

        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:



        # Attachment Operations
        if name == "outlookMail_add_attachment":
            try:
                result = await outlookMail_add_attachment(
                    message_id=arguments["message_id"],
                    file_path=arguments["file_path"],
                    attachment_name=arguments.get("attachment_name")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error adding attachment: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_list_attachments":
            try:
                result = await outlookMail_list_attachments(
                    message_id=arguments["message_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing attachments: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_attachment_details":
            try:
                result = await outlookMail_get_attachment_details(
                    message_id=arguments["message_id"],
                    attachment_id=arguments["attachment_id"],
                    expand=arguments.get("expand")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting attachment: {e}")
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

        elif name == "outlookMail_download_attachment":
            try:
                result = await outlookMail_download_attachment(
                    message_id=arguments["message_id"],
                    attachment_id=arguments["attachment_id"],
                    save_path=arguments["save_path"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error downloading attachment: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_delete_attachment":
            try:
                result = await outlookMail_delete_attachment(
                    message_id=arguments["message_id"],
                    attachment_id=arguments["attachment_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting attachment: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_upload_large_attachment":
            try:
                result = await outlookMail_upload_large_attachment(
                    message_id=arguments["message_id"],
                    file_path=arguments["file_path"],
                    is_inline=arguments.get("is_inline", False),
                    content_id=arguments.get("content_id")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error uploading large attachment: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Mail Folder Operations
        elif name == "outlookMail_delete_folder":
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

        elif name == "outlookMail_get_mail_folder":
            try:
                result = await outlookMail_get_mail_folder(
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
    #-------------------------------------------------------------------------

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