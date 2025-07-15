import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List
import asyncio

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
    outlookMail_get_attachment,
    outlookMail_download_attachment,
    outlookMail_delete_attachment,
    outlookMail_upload_large_attachment,

    # focusedInbox
    outlookMail_delete_inference_override,
    outlookMail_update_inference_override,
    outlookMail_list_inference_overrides,

    # mailFolder
    outlookMail_delete_folder,
    outlookMail_create_mail_folder,
    outlookMail_list_folders,
    outlookMail_permanent_delete_folder,
    outlookMail_copy_folder,
    outlookMail_move_folder,
    outlookMail_get_mail_folder,
    outlookMail_update_folder_display_name,
    outlookMail_get_folder_delta,
    outlookMail_create_child_folder,
    outlookMail_list_child_folders,

    # mailSearchFolder
    outlookMail_delete_mail_search_folder,
    outlookMail_create_mail_search_folder,
    outlookMail_update_mail_search_folder,
    outlookMail_get_mail_search_folder,
    outlookMail_permanent_delete_mail_search_folder,
    outlookMail_get_messages_from_folder,

    # messageRule
    outlookMail_list_inbox_rules,
    outlookMail_create_message_rule,
    outlookMail_delete_message_rule,
    outlookMail_update_message_rule,
    outlookMail_get_inbox_rule_by_id,

    # messages
    outlookMail_copy_message,
    outlookMail_reply_all,
    outlookMail_send_draft,
    outlookMail_send_reply_custom,
    outlookMail_move_message,
    outlookMail_permanent_delete,
    outlookMail_create_draft_in_folder,
    outlookMail_forward_message,
    outlookMail_create_reply_all_draft,
    outlookMail_list_messages,
    outlookMail_create_draft,
    outlookMail_create_reply_draft,
    outlookMail_delete_draft,
    outlookMail_update_draft,
    outlookMail_create_forward_draft,
    outlookMail_list_messages_from_folder
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
                name="outlookMail_get_attachment",
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

            # focusedinbox.py----------------------------------------------------------
            types.Tool(
                name="outlookMail_delete_inference_override",
                description="Delete an inference classification override by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "override_id": {
                            "type": "string",
                            "description": "ID of the override to delete"
                        }
                    },
                    "required": ["override_id"]
                }
            ),
            types.Tool(
                name="outlookMail_update_inference_override",
                description="Update an existing inference classification override by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "override_id": {
                            "type": "string",
                            "description": "ID of the override to update"
                        },
                        "classify_as": {
                            "type": "string",
                            "description": "Classification to apply ('focused' or 'other')",
                            "enum": ["focused", "other"],
                            "default": "focused"
                        }
                    },
                    "required": ["override_id"]
                }
            ),
            types.Tool(
                name="outlookMail_list_inference_overrides",
                description="List all Focused Inbox overrides (inferenceClassification overrides) for the signed-in user.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
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
                name="outlookMail_permanent_delete_folder",
                description="Permanently delete an Outlook mail folder for a user.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string",
                                    "description": "User's ID or userPrincipalName (e.g., 'user@domain.com')"},
                        "folder_id": {"type": "string", "description": "ID of the folder to permanently delete"}
                    },
                    "required": ["user_id", "folder_id"]
                }
            ),

            types.Tool(
                name="outlookMail_copy_folder",
                description="Copy an Outlook mail folder to another destination folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "ID of the folder you want to copy"},
                        "destination_id": {"type": "string", "description": "ID of the destination folder"}
                    },
                    "required": ["folder_id", "destination_id"]
                }
            ),

            types.Tool(
                name="outlookMail_move_folder",
                description="Move an Outlook mail folder to another folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "ID of the folder you want to move"},
                        "destination_id": {"type": "string", "description": "ID of the destination folder"}
                    },
                    "required": ["folder_id", "destination_id"]
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
            types.Tool(
                name="outlookMail_create_child_folder",
                description="Create a child mail folder inside a specified Outlook parent folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_folder_id": {
                            "type": "string",
                            "description": "ID of the parent mail folder"
                        },
                        "display_name": {
                            "type": "string",
                            "description": "Display name for the new folder"
                        },
                        "is_hidden": {
                            "type": "boolean",
                            "description": "Whether the new folder should be hidden",
                            "default": False
                        }
                    },
                    "required": ["parent_folder_id", "display_name"]
                }
            ),
            types.Tool(
                name="outlookMail_get_folder_delta",
                description="Get changes (delta) for all mail folders in the signed-in user's mailbox",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_pagesize": {
                            "type": "integer",
                            "description": "Max number of items per page",
                            "default": 2,
                            "minimum": 1,
                            "maximum": 1000
                        }
                    },
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="outlookMail_list_child_folders",
                description="List child folders of a specific Outlook mail folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "ID of the parent folder"
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Whether to include hidden folders",
                            "default": False
                        }
                    },
                    "required": ["folder_id"],
                    "additionalProperties": False
                }
            ),

            # mailSearchFolder---------------------------------------------------
            types.Tool(
                name="outlookMail_create_mail_search_folder",
                description="Create a new mail search folder under a specified parent folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_folder_id": {
                            "type": "string",
                            "description": "ID of the parent mail folder"
                        },
                        "display_name": {
                            "type": "string",
                            "description": "Display name for the search folder"
                        },
                        "include_nested_folders": {
                            "type": "boolean",
                            "description": "Whether to include subfolders in search"
                        },
                        "source_folder_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of folder IDs to search"
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "OData filter query (e.g., \"contains(subject, 'weekly digest')\")"
                        }
                    },
                    "required": ["parent_folder_id", "display_name", "include_nested_folders",
                                 "source_folder_ids", "filter_query"]
                }
            ),
            types.Tool(
                name="outlookMail_get_mail_search_folder",
                description="Retrieve details of a specific Outlook mail folder by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the mail folder"
                        }
                    },
                    "required": ["folder_id"]
                }
            ),
            types.Tool(
                name="outlookMail_update_mail_search_folder",
                description="Update a mail folder (typically a mailSearchFolder) in Outlook.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the folder to update"
                        },
                        "displayName": {
                            "type": "string",
                            "description": "New display name for the folder"
                        },
                        "includeNestedFolders": {
                            "type": "boolean",
                            "description": "Whether to do deep search (True) or shallow (False)"
                        },
                        "sourceFolderIds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "IDs of folders to be mined"
                        },
                        "filterQuery": {
                            "type": "string",
                            "description": "OData filter (e.g., \"contains(subject, 'weekly digest')\")"
                        }
                    },
                    "required": ["folder_id"]
                }
            ),
            types.Tool(
                name="outlookMail_delete_mail_search_folder",
                description="Delete a mail folder in Outlook by its folder ID (moves to Deleted Items).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the mail folder to delete"
                        }
                    },
                    "required": ["folder_id"]
                }
            ),
            types.Tool(
                name="outlookMail_permanent_delete_mail_search_folder",
                description="Permanently delete a mail folder (bypasses Deleted Items).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the mail folder to permanently delete"
                        }
                    },
                    "required": ["folder_id"]
                }
            ),
            types.Tool(
                name="outlookMail_get_messages_from_folder",
                description="Retrieve messages from a specific Outlook mail folder with filtering options.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The unique ID of the mail folder"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Max number of messages to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "filter_query": {
                            "type": "string",
                            "description": "OData $filter expression (e.g., \"contains(subject, 'weekly digest')\")"
                        },
                        "orderby": {
                            "type": "string",
                            "description": "OData $orderby expression (e.g., \"receivedDateTime desc\")"
                        },
                        "select": {
                            "type": "string",
                            "description": "Comma-separated list of properties to include"
                        }
                    },
                    "required": ["folder_id"]
                }
            ),



            #messageRule.py----------------------------------------------------------
            types.Tool(
                name="outlookMail_list_inbox_rules",
                description="List all message rules (inbox rules) from the user's Inbox folder.",
                inputSchema={
                    "type": "object",
                    "properties": {},  # No input parameters needed
                    "required": []
                }
            ),
            types.Tool(
                name="outlookMail_get_inbox_rule_by_id",
                description="Get a specific inbox message rule by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string",
                            "description": "The unique ID of the inbox rule to retrieve"
                        }
                    },
                    "required": ["rule_id"]
                }
            ),
            types.Tool(
                name="outlookMail_create_message_rule",
                description="Creates a new Outlook message rule using Microsoft Graph API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "displayName": {
                            "type": "string",
                            "description": "Rule display name"
                        },
                        "sequence": {
                            "type": "integer",
                            "description": "Execution order among other rules (lower values execute first)"
                        },
                        "isEnabled": {
                            "type": "boolean",
                            "description": "Whether the rule is active (default: True)"
                        },
                        "conditions": {
                            "type": "object",
                            "description": "Conditions triggering the rule (empty = all messages)",
                            "properties": {
                                "bodyContains": {"type": "array", "items": {"type": "string"}},
                                "bodyOrSubjectContains": {"type": "array", "items": {"type": "string"}},
                                "categories": {"type": "array", "items": {"type": "string"}},
                                "fromAddresses": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "hasAttachments": {"type": "boolean"},
                                "headerContains": {"type": "array", "items": {"type": "string"}},
                                "importance": {"type": "string", "enum": ["low", "normal", "high"]},
                                "isApprovalRequest": {"type": "boolean"},
                                "isAutomaticForward": {"type": "boolean"},
                                "isAutomaticReply": {"type": "boolean"},
                                "isEncrypted": {"type": "boolean"},
                                "isMeetingRequest": {"type": "boolean"},
                                "isMeetingResponse": {"type": "boolean"},
                                "isNonDeliveryReport": {"type": "boolean"},
                                "isPermissionControlled": {"type": "boolean"},
                                "isReadReceipt": {"type": "boolean"},
                                "isSigned": {"type": "boolean"},
                                "isVoicemail": {"type": "boolean"},
                                "messageActionFlag": {"type": "string"},
                                "notSentToMe": {"type": "boolean"},
                                "recipientContains": {"type": "array", "items": {"type": "string"}},
                                "senderContains": {"type": "array", "items": {"type": "string"}},
                                "sensitivity": {"type": "string", "enum": ["normal", "personal", "private"]},
                                "sentCcMe": {"type": "boolean"},
                                "sentOnlyToMe": {"type": "boolean"},
                                "sentToAddresses": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "sentToMe": {"type": "boolean"},
                                "sentToOrCcMe": {"type": "boolean"},
                                "subjectContains": {"type": "array", "items": {"type": "string"}},
                                "withinSizeRange": {
                                    "type": "object",
                                    "properties": {
                                        "minimumSize": {"type": "integer"},
                                        "maximumSize": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "actions": {
                            "type": "object",
                            "description": "Actions to apply when conditions are met",
                            "properties": {
                                "assignCategories": {"type": "array", "items": {"type": "string"}},
                                "copyToFolder": {"type": "string"},
                                "delete": {"type": "boolean"},
                                "forwardAsAttachmentTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "forwardTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "markAsRead": {"type": "boolean"},
                                "markImportance": {"type": "string", "enum": ["low", "normal", "high"]},
                                "moveToFolder": {"type": "string"},
                                "permanentDelete": {"type": "boolean"},
                                "redirectTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "stopProcessingRules": {"type": "boolean"}
                            },
                            "required": ["moveToFolder"]  # At least one action is required
                        },
                        "exceptions": {
                            "type": "object",
                            "description": "Exception conditions preventing rule execution",
                            "properties": {
                                # Same properties as conditions
                            }
                        }
                    },
                    "required": ["displayName", "sequence", "actions"]
                }
            ),
            types.Tool(
                name="outlookMail_update_message_rule",
                description="Updates an existing Outlook message rule using Microsoft Graph API (PATCH method)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string",
                            "description": "The ID of the message rule to update"
                        },
                        "displayName": {
                            "type": "string",
                            "description": "New display name for the rule"
                        },
                        "sequence": {
                            "type": "integer",
                            "description": "New execution order (lower values execute first)"
                        },
                        "isEnabled": {
                            "type": "boolean",
                            "description": "Enable/disable status of the rule"
                        },
                        "actions": {
                            "type": "object",
                            "description": "New actions to apply when conditions are met",
                            "properties": {
                                "assignCategories": {"type": "array", "items": {"type": "string"}},
                                "copyToFolder": {"type": "string"},
                                "delete": {"type": "boolean"},
                                "forwardAsAttachmentTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "forwardTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "markAsRead": {"type": "boolean"},
                                "markImportance": {"type": "string", "enum": ["low", "normal", "high"]},
                                "moveToFolder": {"type": "string"},
                                "permanentDelete": {"type": "boolean"},
                                "redirectTo": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "stopProcessingRules": {"type": "boolean"}
                            }
                        },
                        "conditions": {
                            "type": "object",
                            "description": "New triggering conditions (set empty dict to match all messages)",
                            "properties": {
                                "bodyContains": {"type": "array", "items": {"type": "string"}},
                                "bodyOrSubjectContains": {"type": "array", "items": {"type": "string"}},
                                "categories": {"type": "array", "items": {"type": "string"}},
                                "fromAddresses": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "hasAttachments": {"type": "boolean"},
                                "headerContains": {"type": "array", "items": {"type": "string"}},
                                "importance": {"type": "string", "enum": ["low", "normal", "high"]},
                                "isApprovalRequest": {"type": "boolean"},
                                "isAutomaticForward": {"type": "boolean"},
                                "isAutomaticReply": {"type": "boolean"},
                                "isEncrypted": {"type": "boolean"},
                                "isMeetingRequest": {"type": "boolean"},
                                "isMeetingResponse": {"type": "boolean"},
                                "isNonDeliveryReport": {"type": "boolean"},
                                "isPermissionControlled": {"type": "boolean"},
                                "isReadReceipt": {"type": "boolean"},
                                "isSigned": {"type": "boolean"},
                                "isVoicemail": {"type": "boolean"},
                                "messageActionFlag": {"type": "string"},
                                "notSentToMe": {"type": "boolean"},
                                "recipientContains": {"type": "array", "items": {"type": "string"}},
                                "senderContains": {"type": "array", "items": {"type": "string"}},
                                "sensitivity": {"type": "string", "enum": ["normal", "personal", "private"]},
                                "sentCcMe": {"type": "boolean"},
                                "sentOnlyToMe": {"type": "boolean"},
                                "sentToAddresses": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "emailAddress": {
                                                "type": "object",
                                                "properties": {
                                                    "address": {"type": "string"},
                                                    "name": {"type": "string"}
                                                },
                                                "required": ["address"]
                                            }
                                        }
                                    }
                                },
                                "sentToMe": {"type": "boolean"},
                                "sentToOrCcMe": {"type": "boolean"},
                                "subjectContains": {"type": "array", "items": {"type": "string"}},
                                "withinSizeRange": {
                                    "type": "object",
                                    "properties": {
                                        "minimumSize": {"type": "integer"},
                                        "maximumSize": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "exceptions": {
                            "type": "object",
                            "description": "New exception conditions",
                            "properties": {
                                # Same properties as conditions
                            }
                        }
                    },
                    "required": ["rule_id"],
                    "anyOf": [
                        {"required": ["displayName"]},
                        {"required": ["sequence"]},
                        {"required": ["isEnabled"]},
                        {"required": ["actions"]},
                        {"required": ["conditions"]},
                        {"required": ["exceptions"]}
                    ],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="outlookMail_delete_message_rule",
                description="Delete an Outlook message rule from the inbox using Microsoft Graph API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string",
                            "description": "ID of the message rule to delete"
                        }
                    },
                    "required": ["rule_id"],
                    "additionalProperties": False
                },
            ),

            #messages.py-----------------------------------------------------------
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
                name="outlookMail_create_draft_in_folder",
                description="Create a draft Outlook mail message in a specific folder using Microsoft Graph API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "ID of the target mail folder"
                        },
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
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses for the 'To' field"
                        },
                        "cc_recipients": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses for 'Cc'"
                        },
                        "bcc_recipients": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses for 'Bcc'"
                        },
                        "reply_to": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "List of email addresses for 'Reply-To'"
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["Low", "Normal", "High"],
                            "default": "Normal",
                            "description": "Message importance level"
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of category labels"
                        }
                    },
                    "required": ["folder_id", "subject", "body_content", "to_recipients"],
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
                        },
                        "reply_to": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "Email addresses for reply-to (only updatable in draft state)"
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["Low", "Normal", "High"],
                            "description": "Message importance level"
                        },
                        "internet_message_id": {
                            "type": "string",
                            "description": "RFC2822 message ID (only updatable in draft state)"
                        },
                        "is_delivery_receipt_requested": {
                            "type": "boolean",
                            "description": "Whether delivery receipt is requested"
                        },
                        "is_read": {
                            "type": "boolean",
                            "description": "Read status of the message"
                        },
                        "is_read_receipt_requested": {
                            "type": "boolean",
                            "description": "Whether read receipt is requested"
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Category strings (e.g., ['Urgent', 'FollowUp'])"
                        },
                        "inference_classification": {
                            "type": "string",
                            "enum": ["focused", "other"],
                            "description": "Inference classification"
                        },
                        "flag": {
                            "type": "object",
                            "description": "Follow-up flag settings",
                            "properties": {
                                "completedDateTime": {
                                    "type": "object",
                                    "properties": {
                                        "dateTime": {"type": "string", "format": "date-time"},
                                        "timeZone": {"type": "string"}
                                    }
                                },
                                "dueDateTime": {
                                    "type": "object",
                                    "properties": {
                                        "dateTime": {"type": "string", "format": "date-time"},
                                        "timeZone": {"type": "string"}
                                    }
                                },
                                "flagStatus": {
                                    "type": "string",
                                    "enum": ["notFlagged", "flagged", "complete"]
                                },
                                "startDateTime": {
                                    "type": "object",
                                    "properties": {
                                        "dateTime": {"type": "string", "format": "date-time"},
                                        "timeZone": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "from_sender": {
                            "type": "object",
                            "description": "Mailbox owner/sender (must match actual mailbox)",
                            "properties": {
                                "emailAddress": {
                                    "type": "object",
                                    "properties": {
                                        "address": {"type": "string", "format": "email"},
                                        "name": {"type": "string"}
                                    },
                                    "required": ["address"]
                                }
                            }
                        },
                        "sender": {
                            "type": "object",
                            "description": "Actual sending account (for shared mailboxes/delegates)",
                            "properties": {
                                "emailAddress": {
                                    "type": "object",
                                    "properties": {
                                        "address": {"type": "string", "format": "email"},
                                        "name": {"type": "string"}
                                    },
                                    "required": ["address"]
                                }
                            }
                        }
                    },
                    "required": ["message_id"],
                    "anyOf": [
                        {"required": ["subject"]},
                        {"required": ["body_content"]},
                        {"required": ["to_recipients"]},
                        {"required": ["cc_recipients"]},
                        {"required": ["bcc_recipients"]},
                        {"required": ["reply_to"]},
                        {"required": ["importance"]},
                        {"required": ["internet_message_id"]},
                        {"required": ["is_delivery_receipt_requested"]},
                        {"required": ["is_read"]},
                        {"required": ["is_read_receipt_requested"]},
                        {"required": ["categories"]},
                        {"required": ["inference_classification"]},
                        {"required": ["flag"]},
                        {"required": ["from_sender"]},
                        {"required": ["sender"]}
                    ],
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
                name="outlookMail_copy_message",
                description="Copy an existing Outlook message to another folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to copy"
                        },
                        "destination_folder_id": {
                            "type": "string",
                            "description": "The ID of the destination folder"
                        }
                    },
                    "required": ["message_id", "destination_folder_id"],
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
                name="outlookMail_forward_message",
                description="Forward an Outlook message by message ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "ID of the message to forward"
                        },
                        "to_recipients": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of email addresses to forward to"
                        },
                        "comment": {
                            "type": "string",
                            "description": "Comment to include above the forwarded message",
                            "default": ""
                        }
                    },
                    "required": ["message_id", "to_recipients"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="outlookMail_move_message",
                description="Move an Outlook mail message to another folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "ID of the message to move"},
                        "destination_folder_id": {"type": "string", "description": "ID of the target folder"}
                    },
                    "required": ["message_id", "destination_folder_id"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="outlookMail_send_reply_custom",
                description="Send a reply to an Outlook mail message with custom recipients",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "ID of the message to reply to"},
                        "comment": {"type": "string", "description": "Text to include in the reply"},
                        "to_recipients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "address": {"type": "string", "format": "email"}
                                },
                                "required": ["address"]
                            },
                            "description": "List of recipient objects with name and address"
                        }
                    },
                    "required": ["message_id", "comment", "to_recipients"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="outlookMail_reply_all",
                description="Reply all to a message by ID with a comment",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "The ID of the message"},
                        "comment": {"type": "string", "description": "Your reply comment"}
                    },
                    "required": ["message_id", "comment"],
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
                name="outlookMail_permanent_delete",
                description="Permanently delete a message by message ID for a specific user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "The ID or UPN (email) of the user"},
                        "message_id": {"type": "string", "description": "The ID of the message to delete"}
                    },
                    "required": ["user_id", "message_id"],
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
                        },
                        "reply_to": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "format": "email"
                            },
                            "description": "List of email addresses for 'Reply-To'"
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["Low", "Normal", "High"],
                            "default": "Normal",
                            "description": "Message importance level"
                        },
                        "categories": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of category strings (e.g., ['FollowUp', 'ProjectX'])"
                        }
                    },
                    "required": ["subject", "body_content", "to_recipients"],
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
                result = outlookMail_add_attachment(
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
                result = outlookMail_list_attachments(
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

        elif name == "outlookMail_get_attachment":
            try:
                result = outlookMail_get_attachment(
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

        elif name == "outlookMail_download_attachment":
            try:
                result = outlookMail_download_attachment(
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
                result = outlookMail_delete_attachment(
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
                result = outlookMail_upload_large_attachment(
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

        # Focused Inbox Operations
        elif name == "outlookMail_delete_inference_override":
            try:
                result = outlookMail_delete_inference_override(
                    override_id=arguments["override_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting inference override: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_inference_override":
            try:
                result = outlookMail_update_inference_override(
                    override_id=arguments["override_id"],
                    classify_as=arguments.get("classify_as", "focused")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating inference override: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_list_inference_overrides":
            try:
                result = outlookMail_list_inference_overrides()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing inference overrides: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Mail Folder Operations
        elif name == "outlookMail_delete_folder":
            try:
                result = outlookMail_delete_folder(
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
                result = outlookMail_create_mail_folder(
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
                result = outlookMail_list_folders(
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

        elif name == "outlookMail_permanent_delete_folder":
            try:
                result = outlookMail_permanent_delete_folder(
                    user_id=arguments["user_id"],
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error permanently deleting folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_copy_folder":
            try:
                result = outlookMail_copy_folder(
                    folder_id=arguments["folder_id"],
                    destination_id=arguments["destination_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error copying folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_move_folder":
            try:
                result = outlookMail_move_folder(
                    folder_id=arguments["folder_id"],
                    destination_id=arguments["destination_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error moving folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_mail_folder":
            try:
                result = outlookMail_get_mail_folder(
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
                result = outlookMail_update_folder_display_name(
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

        elif name == "outlookMail_create_child_folder":
            try:
                result = outlookMail_create_child_folder(
                    parent_folder_id=arguments["parent_folder_id"],
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
                logger.exception(f"Error creating child folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Folder Delta and Child Folders Operations
        elif name == "outlookMail_get_folder_delta":
            try:
                result = outlookMail_get_folder_delta(
                    max_pagesize=arguments.get("max_pagesize", 2)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting folder delta: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_list_child_folders":
            try:
                result = outlookMail_list_child_folders(
                    folder_id=arguments["folder_id"],
                    include_hidden=arguments.get("include_hidden", False)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing child folders: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]


        # Mail Search Folder Operations
        elif name == "outlookMail_create_mail_search_folder":
            try:
                result = outlookMail_create_mail_search_folder(
                    parent_folder_id=arguments["parent_folder_id"],
                    display_name=arguments["display_name"],
                    include_nested_folders=arguments["include_nested_folders"],
                    source_folder_ids=arguments["source_folder_ids"],
                    filter_query=arguments["filter_query"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating search folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_mail_search_folder":
            try:
                result = outlookMail_get_mail_search_folder(
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting search folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_mail_search_folder":
            try:
                result = outlookMail_update_mail_search_folder(
                    folder_id=arguments["folder_id"],
                    displayName=arguments.get("displayName"),
                    includeNestedFolders=arguments.get("includeNestedFolders"),
                    sourceFolderIds=arguments.get("sourceFolderIds"),
                    filterQuery=arguments.get("filterQuery")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating search folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_delete_mail_search_folder":
            try:
                result = outlookMail_delete_mail_search_folder(
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting search folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_permanent_delete_mail_search_folder":
            try:
                result = outlookMail_permanent_delete_mail_search_folder(
                    folder_id=arguments["folder_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error permanently deleting search folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_messages_from_folder":
            try:
                result = outlookMail_get_messages_from_folder(
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
                logger.exception(f"Error getting messages from folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Message Rule Operations
        elif name == "outlookMail_list_inbox_rules":
            try:
                result = outlookMail_list_inbox_rules()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing inbox rules: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_get_inbox_rule_by_id":
            try:
                result = outlookMail_get_inbox_rule_by_id(
                    rule_id=arguments["rule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting inbox rule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_message_rule":
            try:
                result = outlookMail_create_message_rule(
                    displayName=arguments["displayName"],
                    sequence=arguments["sequence"],
                    isEnabled=arguments.get("isEnabled", True),
                    conditions=arguments.get("conditions"),
                    actions=arguments["actions"],
                    exceptions=arguments.get("exceptions")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating message rule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_message_rule":
            try:
                result = outlookMail_update_message_rule(
                    rule_id=arguments["rule_id"],
                    displayName=arguments.get("displayName"),
                    sequence=arguments.get("sequence"),
                    isEnabled=arguments.get("isEnabled"),
                    actions=arguments.get("actions"),
                    conditions=arguments.get("conditions"),
                    exceptions=arguments.get("exceptions")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error updating message rule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_delete_message_rule":
            try:
                result = outlookMail_delete_message_rule(
                    rule_id=arguments["rule_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting message rule: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        # Message Operations
        elif name == "outlookMail_list_messages":
            try:
                result = outlookMail_list_messages(
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
                result = outlookMail_list_messages_from_folder(
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

        elif name == "outlookMail_create_draft_in_folder":
            try:
                result = outlookMail_create_draft_in_folder(
                    folder_id=arguments["folder_id"],
                    subject=arguments["subject"],
                    body_content=arguments["body_content"],
                    to_recipients=arguments["to_recipients"],
                    cc_recipients=arguments.get("cc_recipients"),
                    bcc_recipients=arguments.get("bcc_recipients"),
                    reply_to=arguments.get("reply_to"),
                    importance=arguments.get("importance", "Normal"),
                    categories=arguments.get("categories")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating draft in folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_update_draft":
            try:
                result = outlookMail_update_draft(
                    message_id=arguments["message_id"],
                    subject=arguments.get("subject"),
                    body_content=arguments.get("body_content"),
                    to_recipients=arguments.get("to_recipients"),
                    cc_recipients=arguments.get("cc_recipients"),
                    bcc_recipients=arguments.get("bcc_recipients"),
                    reply_to=arguments.get("reply_to"),
                    importance=arguments.get("importance"),
                    internet_message_id=arguments.get("internet_message_id"),
                    is_delivery_receipt_requested=arguments.get("is_delivery_receipt_requested"),
                    is_read=arguments.get("is_read"),
                    is_read_receipt_requested=arguments.get("is_read_receipt_requested"),
                    categories=arguments.get("categories"),
                    inference_classification=arguments.get("inference_classification"),
                    flag=arguments.get("flag"),
                    from_sender=arguments.get("from_sender"),
                    sender=arguments.get("sender")
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
                result = outlookMail_delete_draft(
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

        elif name == "outlookMail_copy_message":
            try:
                result = outlookMail_copy_message(
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
                logger.exception(f"Error copying message: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_create_forward_draft":
            try:
                result = outlookMail_create_forward_draft(
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
                result = outlookMail_create_reply_draft(
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
                result = outlookMail_create_reply_all_draft(
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

        elif name == "outlookMail_forward_message":
            try:
                result = outlookMail_forward_message(
                    message_id=arguments["message_id"],
                    to_recipients=arguments["to_recipients"],
                    comment=arguments.get("comment", "")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error forwarding message: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_move_message":
            try:
                result = outlookMail_move_message(
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

        elif name == "outlookMail_send_reply_custom":
            try:
                result = outlookMail_send_reply_custom(
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
                logger.exception(f"Error sending custom reply: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_reply_all":
            try:
                result = outlookMail_reply_all(
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
                logger.exception(f"Error replying to all: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "outlookMail_send_draft":
            try:
                result = outlookMail_send_draft(
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

        elif name == "outlookMail_permanent_delete":
            try:
                result = outlookMail_permanent_delete(
                    user_id=arguments["user_id"],
                    message_id=arguments["message_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error permanently deleting message: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        elif name == "outlookMail_create_draft":
            try:
                result = outlookMail_create_draft(
                    subject=arguments["subject"],
                    body_content=arguments["body_content"],
                    to_recipients=arguments["to_recipients"],
                    cc_recipients=arguments.get("cc_recipients"),
                    bcc_recipients=arguments.get("bcc_recipients"),
                    reply_to=arguments.get("reply_to"),
                    importance=arguments.get("importance", "Normal"),
                    categories=arguments.get("categories")
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