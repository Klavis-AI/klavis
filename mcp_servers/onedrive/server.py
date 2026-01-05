import contextlib
import base64
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


def get_path(data: dict, path: str) -> any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: dict, mapping: dict[str, any]) -> dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw vendor JSON.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# Mapping Rules for OneDrive Objects

ITEM_RULES = {
    "itemId": "id",
    "name": "name",
    "size": "size",
    "lastModified": "lastModifiedDateTime",
    "created": "createdDateTime",
    "webUrl": "webUrl",
    "downloadUrl": lambda x: x.get("@microsoft.graph.downloadUrl"),
    "isFolder": lambda x: bool(x.get('folder')),
    "isFile": lambda x: bool(x.get('file')),
    "parentId": "parentReference.id",
    "parentPath": "parentReference.path",
    "parentName": "parentReference.name",
    "driveId": "parentReference.driveId",
    "driveType": "parentReference.driveType",
    "siteId": "parentReference.siteId",
    "mimeType": "file.mimeType",
    "hashSha1": "file.hashes.sha1Hash",
    "hashSha256": "file.hashes.sha256Hash",
    "hashQuickXor": "file.hashes.quickXorHash",
    "folderChildCount": "folder.childCount",
    "createdBy": "createdBy.user.displayName",
    "createdBy": "createdBy.user.email",
    "modifiedBy": "lastModifiedBy.user.displayName",
    "modifiedBy": "lastModifiedBy.user.email",
    "shared": lambda x: bool(x.get('shared'))
}

FOLDER_RULES = {
    "folderId": "id",
    "name": "name",
    "childCount": "folder.childCount",
    "lastModified": "lastModifiedDateTime",
    "created": "createdDateTime",
    "webUrl": "webUrl",
    "parentId": "parentReference.id",
    "parentPath": "parentReference.path",
    "parentName": "parentReference.name",
    "driveId": "parentReference.driveId",
    "driveType": "parentReference.driveType",
    "siteId": "parentReference.siteId",
    "size": "size",
    "createdBy": "createdBy.user.displayName",
    "createdBy": "createdBy.user.email",
    "modifiedBy": "lastModifiedBy.user.displayName",
    "modifiedBy": "lastModifiedBy.user.email",
    "shared": lambda x: bool(x.get('shared'))
}

SHARED_ITEM_RULES = {
    "sharedItemId": "remoteItem.id",
    "name": "remoteItem.name",
    "size": "remoteItem.size",
    "lastModified": "remoteItem.lastModifiedDateTime",
    "created": "remoteItem.createdDateTime",
    "webUrl": "remoteItem.webUrl",
    "isFolder": lambda x: bool(get_path(x, 'remoteItem.folder')),
    "isFile": lambda x: bool(get_path(x, 'remoteItem.file')),
    "mimeType": "remoteItem.file.mimeType",
    "parentId": "remoteItem.parentReference.id",
    "driveId": "remoteItem.parentReference.driveId",
    "sharedBy": "remoteItem.shared.sharedBy.user.displayName",
    "sharedDateTime": "remoteItem.shared.sharedDateTime",
    "permissions": "remoteItem.shared.scope"
}


def normalize_item(raw_item: dict) -> dict:
    """Normalize a single item (file or folder) and add computed fields."""
    item = normalize(raw_item, ITEM_RULES)
    return item


def normalize_folder(raw_folder: dict) -> dict:
    """Normalize a single folder and add computed fields."""
    folder = normalize(raw_folder, FOLDER_RULES)
    return folder


def normalize_file(raw_file: dict) -> dict:
    """Normalize a single file and add computed fields."""
    file_item = normalize(raw_file, ITEM_RULES)
    return file_item


def normalize_shared_item(raw_shared_item: dict) -> dict:
    """Normalize a single shared item and add computed fields."""
    shared_item = normalize(raw_shared_item, SHARED_ITEM_RULES)
    return shared_item


def normalize_items_response(response_data: dict) -> dict:
    """Normalize a response containing multiple items (like list operations)."""
    if not isinstance(response_data, dict):
        return response_data
    
    normalized_response = {}
    
    # Handle pagination info
    if "@odata.nextLink" in response_data:
        normalized_response["nextPageToken"] = response_data["@odata.nextLink"]
    
    if "@odata.count" in response_data:
        normalized_response["totalCount"] = response_data["@odata.count"]
    
    # Normalize items
    if "value" in response_data and isinstance(response_data["value"], list):
        normalized_response["items"] = [
            normalize_item(item) for item in response_data["value"]
        ]
        normalized_response["count"] = len(normalized_response["items"])
    
    return normalized_response


from tools import (
    # Base
    auth_token_context,

    # Both Items (Files & Folders)
    onedrive_rename_item,
    onedrive_move_item,
    onedrive_delete_item,

    # Files
    onedrive_read_file_content,
    onedrive_create_file,

    # Folders
    onedrive_create_folder,

    # Search & List
    onedrive_list_root_files_folders,
    onedrive_list_inside_folder,
    onedrive_search_item_by_name,
    onedrive_search_folder_by_name,
    onedrive_get_item_by_id,

    #Sharing
    onedrive_list_shared_items,
)


# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

ONEDRIVE_MCP_SERVER_PORT = int(os.getenv("ONEDRIVE_MCP_SERVER_PORT", "5000"))

def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract access_token
                auth_json = json.loads(auth_data)
                return auth_json.get('access_token', '')
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                return ""
    
    return ""

@click.command()
@click.option("--port", default=ONEDRIVE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("onedrive-mcp-server")
#-------------------------------------------------------------------------------------


    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # File Operations
            types.Tool(
                name="onedrive_rename_item",
                description="Rename a file or folder in OneDrive by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "ID of the file/folder to rename"},
                        "new_name": {"type": "string", "description": "New name for the item"}
                    },
                    "required": ["file_id", "new_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM"})
            ),
            types.Tool(
                name="onedrive_move_item",
                description="Move an item to a different folder in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "ID of the item to move"},
                        "new_parent_id": {"type": "string", "description": "ID of the destination folder"}
                    },
                    "required": ["item_id", "new_parent_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM"})
            ),
            types.Tool(
                name="onedrive_delete_item",
                description="Delete an item from OneDrive by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "ID of the item to delete"}
                    },
                    "required": ["item_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM"})
            ),

            # File Content Operations
            types.Tool(
                name="onedrive_read_file_content",
                description="Read the content of a file from OneDrive by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string", "description": "ID of the file to read"}
                    },
                    "required": ["file_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FILE"})
            ),

            # File Creation
            types.Tool(
                name="onedrive_create_file",
                description="Create a new file in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_folder": {"type": "string", "description": "'root' to create in root or ID of the parent folder"},
                        "new_file_name": {"type": "string", "description": "Name for the new file"},
                        "data": {"type": "string", "description": "Content for the new file (optional)"},
                        "if_exists": {
                            "type": "string",
                            "enum": ["error", "rename", "replace"],
                            "default": "error",
                            "description": "Behavior when file exists: 'error' (abort), 'rename' (create unique name), 'replace' (overwrite)"
                        }
                    },
                    "required": ["parent_folder", "new_file_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FILE"})
            ),

            # Folder Operations
            types.Tool(
                name="onedrive_create_folder",
                description="Create a new folder in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_folder": {"type": "string", "description": "'root' to create in root or ID of the parent folder"},
                        "new_folder_name": {"type": "string", "description": "Name for the new folder"},
                        "behavior": {
                            "type": "string",
                            "enum": ["fail", "replace", "rename"],
                            "default": "fail",
                            "description": "Conflict resolution: 'fail' (return error), 'replace' (overwrite), 'rename' (unique name)"
                        }
                    },
                    "required": ["parent_folder", "new_folder_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FOLDER"})
            ),

            # Listing & Searching
            types.Tool(
                name="onedrive_list_root_files_folders",
                description="List all files and folders in the root of OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FOLDER", "readOnlyHint": True})
            ),
            types.Tool(
                name="onedrive_list_inside_folder",
                description="List all items inside a specific folder.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {"type": "string", "description": "ID of the folder to list"}
                    },
                    "required": ["folder_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FOLDER", "readOnlyHint": True})
            ),
            types.Tool(
                name="onedrive_search_item_by_name",
                description="Search for items by name in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "itemname": {"type": "string", "description": "Name or partial name to search for"}
                    },
                    "required": ["itemname"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM", "readOnlyHint": True})
            ),
            types.Tool(
                name="onedrive_search_folder_by_name",
                description="Search for folders by name in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_name": {"type": "string", "description": "Name or partial name to search for"}
                    },
                    "required": ["folder_name"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_FOLDER", "readOnlyHint": True})
            ),
            types.Tool(
                name="onedrive_get_item_by_id",
                description="Get item details by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "ID of the item to retrieve"}
                    },
                    "required": ["item_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM", "readOnlyHint": True})
            ),

            # Sharing & Permissions
            types.Tool(
                name="onedrive_list_shared_items",
                description="List all items shared with the current user in OneDrive.",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
                annotations=types.ToolAnnotations(**{"category": "ONEDRIVE_ITEM", "readOnlyHint": True})
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str, arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:

        # File Operations
        if name == "onedrive_rename_item":
            try:
                result = await onedrive_rename_item(
                    file_id=arguments["file_id"],
                    new_name=arguments["new_name"]
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_item(raw_data)
                    response = {"status": "success", "item": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error renaming item: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_move_item":
            try:
                result = await onedrive_move_item(
                    item_id=arguments["item_id"],
                    new_parent_id=arguments["new_parent_id"]
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_item(raw_data)
                    response = {"status": "success", "item": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error moving item: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_delete_item":
            try:
                result = await onedrive_delete_item(
                    item_id=arguments["item_id"]
                )
                # For delete operations, wrap in a normalized structure
                if isinstance(result, tuple) and len(result) == 1:
                    response = {
                        "status": "success",
                        "itemId": arguments["item_id"],
                        "message": result[0]
                    }
                else:
                    response = {"status": "error", "details": result}
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error deleting item: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # File Content Operations
        elif name == "onedrive_read_file_content":
            try:
                result = await onedrive_read_file_content(
                    file_id=arguments["file_id"]
                )
                return [
                    types.TextContent(
                        type="text",
                        text=result if isinstance(result, str) else json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error reading file content: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # File Creation
        elif name == "onedrive_create_file":
            try:
                result = await onedrive_create_file(
                    parent_folder=arguments["parent_folder"],
                    new_file_name=arguments["new_file_name"],
                    data=arguments.get("data"),
                    if_exists=arguments.get("if_exists", "error")
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_file(raw_data)
                    response = {"status": "success", "file": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating file: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Folder Operations
        elif name == "onedrive_create_folder":
            try:
                result = await onedrive_create_folder(
                    parent_folder=arguments["parent_folder"],
                    new_folder_name=arguments["new_folder_name"],
                    behavior=arguments.get("behavior", "fail")
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_folder(raw_data)
                    response = {"status": "success", "folder": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error creating folder: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Listing & Searching
        elif name == "onedrive_list_root_files_folders":
            try:
                result = await onedrive_list_root_files_folders()
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_items_response(raw_data)
                    response = {"status": "success", "data": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing root items: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_list_inside_folder":
            try:
                result = await onedrive_list_inside_folder(
                    folder_id=arguments["folder_id"]
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_items_response(raw_data)
                    response = {"status": "success", "data": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing folder contents: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_search_item_by_name":
            try:
                result = await onedrive_search_item_by_name(
                    itemname=arguments["itemname"]
                )
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    normalized_data = normalize_items_response(raw_data)
                    response = {"status": "success", "data": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error searching items: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_search_folder_by_name":
            try:
                result = await onedrive_search_folder_by_name(
                    folder_name=arguments["folder_name"]
                )
                # Normalize the response for folder search results
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], list):
                    _, raw_folders = result
                    normalized_folders = [normalize_folder(folder) for folder in raw_folders]
                    response = {"status": "success", "folders": normalized_folders, "count": len(normalized_folders)}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error searching folders: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "onedrive_get_item_by_id":
            try:
                result = await onedrive_get_item_by_id(
                    item_id=arguments["item_id"]
                )
                # Normalize the response
                if isinstance(result, dict) and "id" in result:
                    normalized_data = normalize_item(result)
                    response = {"status": "success", "item": normalized_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error getting item by ID: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        # Sharing & Permissions
        elif name == "onedrive_list_shared_items":
            try:
                result = await onedrive_list_shared_items()
                # Normalize the response
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
                    _, raw_data = result
                    if "value" in raw_data and isinstance(raw_data["value"], list):
                        normalized_items = [normalize_shared_item(item) for item in raw_data["value"]]
                        response = {
                            "status": "success", 
                            "sharedItems": normalized_items,
                            "count": len(normalized_items)
                        }
                    else:
                        response = {"status": "success", "data": raw_data}
                else:
                    response = result
                
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(response, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error listing shared items: {e}")
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
                    text=f"Unknown OneDrive tool: {name}",
                )
            ]



#---------------------------------------------------------------------------------------------

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        # Extract access token from headers
        access_token = extract_access_token(request)

        # Set the access token in context for this request
        token = auth_token_context.set(access_token)
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

        # Extract access token from headers
        access_token = extract_access_token(scope)

        # Set the access token in context for this request
        token = auth_token_context.set(access_token)
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
