import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List

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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=result,
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
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
