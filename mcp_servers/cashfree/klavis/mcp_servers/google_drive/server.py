import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar
from enum import Enum

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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils import convert_document_to_html, convert_document_to_markdown

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_DRIVE_MCP_SERVER_PORT = int(os.getenv("GOOGLE_DRIVE_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# Define enums that are referenced in context.py
class OrderBy(Enum):
    MODIFIED_TIME_DESC = "modifiedTime desc"
    MODIFIED_TIME = "modifiedTime"
    CREATED_TIME_DESC = "createdTime desc"
    CREATED_TIME = "createdTime"
    NAME = "name"
    NAME_DESC = "name desc"

class DocumentFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"

class Corpora(Enum):
    USER = "user"
    DRIVE = "drive"
    DOMAIN = "domain"

def get_drive_service(access_token: str):
    """Create Google Drive service with access token."""
    credentials = Credentials(token=access_token)
    return build('drive', 'v3', credentials=credentials)

def get_docs_service(access_token: str):
    """Create Google Docs service with access token."""
    credentials = Credentials(token=access_token)
    return build('docs', 'v1', credentials=credentials)

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

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def remove_none_values(params: dict) -> dict:
    """Remove None values from parameters dictionary."""
    return {k: v for k, v in params.items() if v is not None}

async def get_document_content_by_id(document_id: str) -> Dict[str, Any]:
    """Get the latest version of the specified Google Docs document."""
    logger.info(f"Executing tool: get_document_by_id with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        request = service.documents().get(documentId=document_id)
        response = request.execute()
        
        return dict(response)
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_document_by_id: {e}")
        raise e

def build_files_list_query(
    mime_type: str,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> str:
    query = [f"(mimeType = '{mime_type}' and trashed = false)"]

    if isinstance(document_contains, str):
        document_contains = [document_contains]

    if isinstance(document_not_contains, str):
        document_not_contains = [document_not_contains]

    if document_contains:
        for keyword in document_contains:
            name_contains = keyword.replace("'", "\\'")
            full_text_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name contains '{name_contains}' or fullText contains '{full_text_contains}')"
            )
            query.append(keyword_query)

    if document_not_contains:
        for keyword in document_not_contains:
            name_not_contains = keyword.replace("'", "\\'")
            full_text_not_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name not contains '{name_not_contains}' and "
                f"fullText not contains '{full_text_not_contains}')"
            )
            query.append(keyword_query)

    return " and ".join(query)

def build_files_list_params(
    mime_type: str,
    page_size: int,
    order_by: list[OrderBy],
    pagination_token: str | None,
    include_shared_drives: bool,
    search_only_in_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> dict[str, Any]:
    query = build_files_list_query(
        mime_type=mime_type,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
    )

    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": ",".join([item.value for item in order_by]),
        "pageToken": pagination_token,
    }

    if (
        include_shared_drives
        or search_only_in_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if search_only_in_shared_drive_id:
        params["driveId"] = search_only_in_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    params = remove_none_values(params)

    return params

def build_file_tree_request_params(
    order_by: list[OrderBy] | None,
    page_token: str | None,
    limit: int | None,
    include_shared_drives: bool,
    restrict_to_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
) -> dict[str, Any]:
    if order_by is None:
        order_by = [OrderBy.MODIFIED_TIME_DESC]
    elif isinstance(order_by, OrderBy):
        order_by = [order_by]

    params = {
        "q": "trashed = false",
        "corpora": Corpora.USER.value,
        "pageToken": page_token,
        "fields": (
            "files(id, name, parents, mimeType, driveId, size, createdTime, modifiedTime, owners)"
        ),
        "orderBy": ",".join([item.value for item in order_by]),
    }

    if limit:
        params["pageSize"] = str(limit)

    if (
        include_shared_drives
        or restrict_to_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if restrict_to_shared_drive_id:
        params["driveId"] = restrict_to_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    return params

def build_file_tree(files: dict[str, Any]) -> dict[str, Any]:
    file_tree: dict[str, Any] = {}

    for file in files.values():
        owners = file.get("owners", [])
        if owners:
            owners = [
                {"name": owner.get("displayName", ""), "email": owner.get("emailAddress", "")}
                for owner in owners
            ]
            file["owners"] = owners

        if "size" in file:
            file["size"] = {"value": int(file["size"]), "unit": "bytes"}

        # Although "parents" is a list, a file can only have one parent
        try:
            parent_id = file["parents"][0]
            del file["parents"]
        except (KeyError, IndexError):
            parent_id = None

        # Determine the file's Drive ID
        if "driveId" in file:
            drive_id = file["driveId"]
            del file["driveId"]
        # If a shared drive id is not present, the file is in "My Drive"
        else:
            drive_id = "My Drive"

        if drive_id not in file_tree:
            file_tree[drive_id] = []

        # Root files will have the Drive's id as the parent. If the parent id is not in the files
        # list, the file must be at drive's root
        if parent_id not in files:
            file_tree[drive_id].append(file)

        # Associate the file with its parent
        else:
            if "children" not in files[parent_id]:
                files[parent_id]["children"] = []
            files[parent_id]["children"].append(file)

    return file_tree

async def search_documents(
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
    search_only_in_shared_drive_id: str | None = None,
    include_shared_drives: bool = False,
    include_organization_domain_documents: bool = False,
    order_by: list[str] | None = None,
    limit: int = 50,
    pagination_token: str | None = None,
) -> Dict[str, Any]:
    """Search for documents in the user's Google Drive."""
    logger.info(f"Executing tool: search_documents")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        # Convert order_by strings to OrderBy enums
        order_by_enums = []
        if order_by:
            for order in order_by:
                try:
                    order_by_enums.append(OrderBy(order))
                except ValueError:
                    order_by_enums.append(OrderBy.MODIFIED_TIME_DESC)
        else:
            order_by_enums = [OrderBy.MODIFIED_TIME_DESC]

        page_size = min(10, limit)
        files: list[dict[str, Any]] = []

        params = build_files_list_params(
            mime_type="application/vnd.google-apps.document",
            document_contains=document_contains,
            document_not_contains=document_not_contains,
            page_size=page_size,
            order_by=order_by_enums,
            pagination_token=pagination_token,
            include_shared_drives=include_shared_drives,
            search_only_in_shared_drive_id=search_only_in_shared_drive_id,
            include_organization_domain_documents=include_organization_domain_documents,
        )

        while len(files) < limit:
            if pagination_token:
                params["pageToken"] = pagination_token
            else:
                params.pop("pageToken", None)

            results = service.files().list(**params).execute()
            batch = results.get("files", [])
            files.extend(batch[: limit - len(files)])

            pagination_token = results.get("nextPageToken")
            if not pagination_token or len(batch) < page_size:
                break

        return {"documents_count": len(files), "documents": files}
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool search_documents: {e}")
        raise e

async def search_and_retrieve_documents(
    return_format: str = "markdown",
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
    search_only_in_shared_drive_id: str | None = None,
    include_shared_drives: bool = False,
    include_organization_domain_documents: bool = False,
    order_by: list[str] | None = None,
    limit: int = 50,
    pagination_token: str | None = None,
) -> Dict[str, Any]:
    """Search and retrieve the contents of Google documents in the user's Google Drive."""
    logger.info(f"Executing tool: search_and_retrieve_documents")
    try:
        # First search for documents
        response = await search_documents(
            document_contains=document_contains,
            document_not_contains=document_not_contains,
            search_only_in_shared_drive_id=search_only_in_shared_drive_id,
            include_shared_drives=include_shared_drives,
            include_organization_domain_documents=include_organization_domain_documents,
            order_by=order_by,
            limit=limit,
            pagination_token=pagination_token,
        )

        documents = []
        for item in response["documents"]:
            document = await get_document_content_by_id(item["id"])

            # Convert document content to requested format
            if return_format == DocumentFormat.MARKDOWN.value:
                document_body = convert_document_to_markdown(document)
            elif return_format == DocumentFormat.HTML.value:
                document_body = convert_document_to_html(document)
            else:
                # Default to markdown if format is not recognized
                document_body = convert_document_to_markdown(document)

            # Extract only the useful fields. Otherwise prompt will be too long.
            filtered_document = {
                "title": document.get("title", ""),
                "body": document_body,
                "documentId": document.get("documentId", item["id"])
            }

            documents.append(filtered_document)

        return {"documents_count": len(documents), "documents": documents}
    except Exception as e:
        logger.exception(f"Error executing tool search_and_retrieve_documents: {e}")
        raise e

async def empty_trash(
    drive_id: str | None = None,
) -> Dict[str, Any]:
    """Permanently delete all of the user's trashed files."""
    logger.info(f"Executing tool: empty_trash with drive_id: {drive_id}")
    try:
        access_token = get_auth_token()
        
        # Use v2 API for empty trash operation
        credentials = Credentials(token=access_token)
        service = build('drive', 'v2', credentials=credentials)
        
        params = {}
        if drive_id:
            params['driveId'] = drive_id
            
        service.files().emptyTrash(**params).execute()
        
        return {"success": True, "message": "Trash emptied successfully"}
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool empty_trash: {e}")
        raise e

async def create_shared_drive(
    name: str,
    request_id: str,
) -> Dict[str, Any]:
    """Create a new shared drive."""
    logger.info(f"Executing tool: create_shared_drive with name: {name}, request_id: {request_id}")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        drive_metadata = {
            'name': name
        }
        
        result = service.drives().create(
            body=drive_metadata,
            requestId=request_id
        ).execute()
        
        return result
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_shared_drive: {e}")
        raise e

async def get_file_tree_structure(
    include_shared_drives: bool = False,
    restrict_to_shared_drive_id: str | None = None,
    include_organization_domain_documents: bool = False,
    order_by: list[str] | None = None,
    limit: int | None = None,
) -> Dict[str, Any]:
    """Get the file/folder tree structure of the user's Google Drive."""
    logger.info(f"Executing tool: get_file_tree_structure")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        # Convert order_by strings to OrderBy enums
        order_by_enums = []
        if order_by:
            for order in order_by:
                try:
                    order_by_enums.append(OrderBy(order))
                except ValueError:
                    order_by_enums.append(OrderBy.MODIFIED_TIME_DESC)
        else:
            order_by_enums = None

        keep_paginating = True
        page_token = None
        files = {}

        params = build_file_tree_request_params(
            order_by_enums,
            page_token,
            limit,
            include_shared_drives,
            restrict_to_shared_drive_id,
            include_organization_domain_documents,
        )

        while keep_paginating:
            # Get a list of files
            results = service.files().list(**params).execute()

            # Update page token
            page_token = results.get("nextPageToken")
            params["pageToken"] = page_token
            keep_paginating = page_token is not None

            for file in results.get("files", []):
                files[file["id"]] = file

        if not files:
            return {"drives": []}

        file_tree = build_file_tree(files)

        drives = []

        for drive_id, drive_files in file_tree.items():
            if drive_id == "My Drive":
                drive = {"name": "My Drive", "children": drive_files}
            else:
                try:
                    drive_details = service.drives().get(driveId=drive_id).execute()
                    drive_name = drive_details.get("name", "Shared Drive (name unavailable)")
                except HttpError as e:
                    drive_name = (
                        f"Shared Drive (name unavailable: 'HttpError {e.status_code}: {e.reason}')"
                    )

                drive = {"name": drive_name, "id": drive_id, "children": drive_files}

            drives.append(drive)

        return {"drives": drives}
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_file_tree_structure: {e}")
        raise e

@click.command()
@click.option("--port", default=GOOGLE_DRIVE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("google-drive-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_drive_search_documents",
                description="Search for documents in the user's Google Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_contains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords or phrases that must be in the document title or body.",
                        },
                        "document_not_contains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords or phrases that must NOT be in the document title or body.",
                        },
                        "search_only_in_shared_drive_id": {
                            "type": "string",
                            "description": "The ID of the shared drive to restrict the search to.",
                        },
                        "include_shared_drives": {
                            "type": "boolean",
                            "description": "Whether to include documents from shared drives.",
                            "default": False,
                        },
                        "include_organization_domain_documents": {
                            "type": "boolean",
                            "description": "Whether to include documents from the organization's domain.",
                            "default": False,
                        },
                        "order_by": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["modifiedTime desc", "modifiedTime", "createdTime desc", "createdTime", "name", "name desc"]
                            },
                            "description": "Sort order for the results.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The number of documents to list.",
                            "default": 50,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to continue a previous request.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DRIVE_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_drive_search_and_retrieve_documents",
                description="Search and retrieve the contents of Google documents in the user's Google Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "return_format": {
                            "type": "string",
                            "enum": ["markdown", "html"],
                            "description": "The format of the document to return.",
                            "default": "markdown",
                        },
                        "document_contains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords or phrases that must be in the document title or body.",
                        },
                        "document_not_contains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords or phrases that must NOT be in the document title or body.",
                        },
                        "search_only_in_shared_drive_id": {
                            "type": "string",
                            "description": "The ID of the shared drive to restrict the search to.",
                        },
                        "include_shared_drives": {
                            "type": "boolean",
                            "description": "Whether to include documents from shared drives.",
                            "default": False,
                        },
                        "include_organization_domain_documents": {
                            "type": "boolean",
                            "description": "Whether to include documents from the organization's domain.",
                            "default": False,
                        },
                        "order_by": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["modifiedTime desc", "modifiedTime", "createdTime desc", "createdTime", "name", "name desc"]
                            },
                            "description": "Sort order for the results.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The number of documents to list.",
                            "default": 50,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to continue a previous request.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DRIVE_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_drive_get_file_tree_structure",
                description="Get the file/folder tree structure of the user's Google Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_shared_drives": {
                            "type": "boolean",
                            "description": "Whether to include shared drives in the file tree structure.",
                            "default": False,
                        },
                        "restrict_to_shared_drive_id": {
                            "type": "string",
                            "description": "If provided, only include files from this shared drive in the file tree structure.",
                        },
                        "include_organization_domain_documents": {
                            "type": "boolean",
                            "description": "Whether to include documents from the organization's domain.",
                            "default": False,
                        },
                        "order_by": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["modifiedTime desc", "modifiedTime", "createdTime desc", "createdTime", "name", "name desc"]
                            },
                            "description": "Sort order for the results.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The number of files and folders to list.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DRIVE_FILE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_drive_empty_trash",
                description="Permanently delete all of the user's trashed files.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "drive_id": {
                            "type": "string",
                            "description": "If set, empties the trash of the provided shared drive.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DRIVE_FILE"}
                ),
            ),
            types.Tool(
                name="google_drive_create_shared_drive",
                description="Create a new shared drive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the shared drive to create.",
                        },
                        "request_id": {
                            "type": "string",
                            "description": "Required. An ID, such as a random UUID, which uniquely identifies this user's request for idempotent creation of a shared drive.",
                        },
                    },
                    "required": ["name", "request_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DRIVE_FILE"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:     
        if name == "google_drive_search_documents":
            try:
                result = await search_documents(
                    document_contains=arguments.get("document_contains"),
                    document_not_contains=arguments.get("document_not_contains"),
                    search_only_in_shared_drive_id=arguments.get("search_only_in_shared_drive_id"),
                    include_shared_drives=arguments.get("include_shared_drives", False),
                    include_organization_domain_documents=arguments.get("include_organization_domain_documents", False),
                    order_by=arguments.get("order_by"),
                    limit=arguments.get("limit", 50),
                    pagination_token=arguments.get("pagination_token"),
                )
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
        
        elif name == "google_drive_search_and_retrieve_documents":
            try:
                result = await search_and_retrieve_documents(
                    return_format=arguments.get("return_format", "markdown"),
                    document_contains=arguments.get("document_contains"),
                    document_not_contains=arguments.get("document_not_contains"),
                    search_only_in_shared_drive_id=arguments.get("search_only_in_shared_drive_id"),
                    include_shared_drives=arguments.get("include_shared_drives", False),
                    include_organization_domain_documents=arguments.get("include_organization_domain_documents", False),
                    order_by=arguments.get("order_by"),
                    limit=arguments.get("limit", 50),
                    pagination_token=arguments.get("pagination_token"),
                )
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
        
        elif name == "google_drive_get_file_tree_structure":
            try:
                result = await get_file_tree_structure(
                    include_shared_drives=arguments.get("include_shared_drives", False),
                    restrict_to_shared_drive_id=arguments.get("restrict_to_shared_drive_id"),
                    include_organization_domain_documents=arguments.get("include_organization_domain_documents", False),
                    order_by=arguments.get("order_by"),
                    limit=arguments.get("limit"),
                )
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

        elif name == "google_drive_empty_trash":
            try:
                result = await empty_trash(
                    drive_id=arguments.get("drive_id"),
                )
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

        elif name == "google_drive_create_shared_drive":
            try:
                name = arguments.get("name", "")
                if not name:
                    raise ValueError("The 'name' argument is required.")
                request_id = arguments.get("request_id")
                if not request_id:
                    raise ValueError("The 'request_id' argument is required.")
                result = await create_shared_drive(
                    name=name,
                    request_id=request_id
                )
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