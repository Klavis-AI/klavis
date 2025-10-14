import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict
import base64

import click
import mcp.types as types
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    auth_token_context,
    create_page,
    get_page,
    update_page_properties,
    retrieve_page_property,
    query_database,
    get_database,
    create_database,
    update_database,
    create_database_item,
    search_notion,
    get_user,
    list_users,
    get_me,
    create_comment,
    get_comments,
    retrieve_block,
    update_block,
    delete_block,
    get_block_children,
    append_block_children,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

NOTION_MCP_SERVER_PORT = int(os.getenv("NOTION_MCP_SERVER_PORT", "5000"))

def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
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
@click.option(
    "--port", default=NOTION_MCP_SERVER_PORT, help="Port to listen on for HTTP"
)
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
    app = Server("notion-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="notion_create_page",
                description="Create a new page in Notion. If parent is not specified, a private page will be created in the workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "object",
                            "description": "Page configuration",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Markdown content for the page",
                                },
                                "properties": {
                                    "type": "object",
                                    "description": "Page properties",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Page title",
                                        }
                                    }
                                },
                            },
                        },
                        "parent": {
                            "type": "object",
                            "description": "Optional parent object with page_id, database_id, or workspace. If not specified, a private page will be created",
                            "properties": {
                                "page_id": {
                                    "type": "string",
                                    "description": "Parent page ID",
                                },
                                "database_id": {
                                    "type": "string",
                                    "description": "Parent database ID",
                                },
                                "workspace": {
                                    "type": "boolean",
                                    "description": "Whether parent is workspace",
                                },
                            },
                        },
                        "icon": {
                            "type": "object",
                            "description": "Optional page icon",
                        },
                        "cover": {
                            "type": "object",
                            "description": "Optional page cover",
                        },
                    },
                    "required": ["page"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_PAGE"}
                ),
            ),
            types.Tool(
                name="notion_get_page",
                description="Retrieve a page from Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to retrieve",
                        },
                        "filter_properties": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of property IDs to limit the response",
                        },
                    },
                    "required": ["page_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_PAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_update_page_properties",
                description="Update properties of a page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page to update",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Properties to update",
                        },
                        "icon": {
                            "type": "object",
                            "description": "Optional new icon",
                        },
                        "cover": {
                            "type": "object",
                            "description": "Optional new cover",
                        },
                        "archived": {
                            "type": "boolean",
                            "description": "Whether to archive the page",
                        },
                        "in_trash": {
                            "type": "boolean",
                            "description": "Whether to move the page to trash",
                        },
                    },
                    "required": ["page_id", "properties"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_PAGE"}
                ),
            ),
            types.Tool(
                name="notion_query_database",
                description="Query a database in Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to query",
                        },
                        "filter": {
                            "type": "object",
                            "description": "Optional filter conditions",
                        },
                        "sorts": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional sort conditions",
                        },
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                        "filter_properties": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of property IDs to limit the response",
                        },
                        "archived": {
                            "type": "boolean",
                            "description": "Whether to include archived pages",
                        },
                        "in_trash": {
                            "type": "boolean",
                            "description": "Whether to include pages in trash",
                        },
                    },
                    "required": ["database_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_DATABASE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_get_database",
                description="Retrieve a database from Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to retrieve",
                        },
                    },
                    "required": ["database_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_DATABASE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_create_database",
                description="Create a new database in Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent": {
                            "type": "object",
                            "description": "Parent page object",
                        },
                        "title": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Database title as rich text array",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Database properties schema",
                        },
                        "icon": {
                            "type": "object",
                            "description": "Optional database icon",
                        },
                        "cover": {
                            "type": "object",
                            "description": "Optional database cover",
                        },
                        "description": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional description as rich text array",
                        },
                    },
                    "required": ["parent", "title", "properties"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_DATABASE"}
                ),
            ),
            types.Tool(
                name="notion_update_database",
                description="Update a database in Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database to update",
                        },
                        "title": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional new title",
                        },
                        "description": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional new description",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Optional updated properties schema",
                        },
                        "icon": {
                            "type": "object",
                            "description": "Optional new icon",
                        },
                        "cover": {
                            "type": "object",
                            "description": "Optional new cover",
                        },
                        "archived": {
                            "type": "boolean",
                            "description": "Whether to archive the database",
                        },
                    },
                    "required": ["database_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_DATABASE"}
                ),
            ),
            types.Tool(
                name="notion_create_database_item",
                description="Create a new item (page) in a database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_id": {
                            "type": "string",
                            "description": "ID of the database",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Item properties",
                        },
                        "children": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional array of block objects",
                        },
                        "icon": {
                            "type": "object",
                            "description": "Optional item icon",
                        },
                        "cover": {
                            "type": "object",
                            "description": "Optional item cover",
                        },
                    },
                    "required": ["database_id", "properties"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_DATABASE"}
                ),
            ),

            types.Tool(
                name="notion_search",
                description="Search for pages and databases in Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "sort": {
                            "type": "object",
                            "description": "Optional sort criteria",
                        },
                        "filter": {
                            "type": "object",
                            "description": "Optional filter conditions",
                        },
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                    },
                    "required": [],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_get_user",
                description="Retrieve a user from Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "ID of the user to retrieve",
                        },
                    },
                    "required": ["user_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_USER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_list_users",
                description="List all users in the workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                    },
                    "required": [],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_USER", "readOnlyHint": True}
                ),
            ),

            types.Tool(
                name="notion_create_comment",
                description="Create a comment on a page or discussion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent": {
                            "type": "object",
                            "description": "Parent object (page_id)",
                        },
                        "rich_text": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Comment content as rich text array",
                        },
                        "discussion_id": {
                            "type": "string",
                            "description": "Optional discussion thread ID",
                        },
                    },
                    "required": ["rich_text"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_COMMENT"}
                ),
            ),
            types.Tool(
                name="notion_get_comments",
                description="Retrieve comments from a page or block",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block or page",
                        },
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                    },
                    "required": ["block_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_COMMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_get_me",
                description="Retrieve your token's bot user information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_USER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_retrieve_page_property",
                description="Retrieve a specific property from a page",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "ID of the page",
                        },
                        "property_id": {
                            "type": "string",
                            "description": "ID of the property to retrieve",
                        },
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                    },
                    "required": ["page_id", "property_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_PAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_retrieve_block",
                description="Retrieve a block from Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block to retrieve",
                        },
                    },
                    "required": ["block_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_BLOCK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_update_block",
                description="Update a block in Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block to update",
                        },
                        "block_type": {
                            "type": "object",
                            "description": "Block type and properties to update",
                        },
                        "archived": {
                            "type": "boolean",
                            "description": "Whether to archive the block",
                        },
                    },
                    "required": ["block_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_BLOCK"}
                ),
            ),
            types.Tool(
                name="notion_delete_block",
                description="Delete a block from Notion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the block to delete",
                        },
                    },
                    "required": ["block_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_BLOCK"}
                ),
            ),
            types.Tool(
                name="notion_get_block_children",
                description="Retrieve children of a block",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the parent block",
                        },
                        "start_cursor": {
                            "type": "string",
                            "description": "Cursor for pagination",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of results to return (max 100)",
                        },
                    },
                    "required": ["block_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_BLOCK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="notion_append_block_children",
                description="Append block children to a container block",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "block_id": {
                            "type": "string",
                            "description": "ID of the parent block",
                        },
                        "children": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of block objects to append",
                        },
                        "after": {
                            "type": "string",
                            "description": "ID of the existing block to append after",
                        },
                    },
                    "required": ["block_id", "children"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "NOTION_BLOCK"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Log the tool call with name and arguments
        logger.info(f"Tool called: {name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
        
        if name == "notion_create_page":
            try:
                result = await create_page(
                    page=arguments.get("page"),
                    parent=arguments.get("parent"),
                    properties=arguments.get("properties"),  # Support old format
                    children=arguments.get("children"),  # Support old format
                    icon=arguments.get("icon"),
                    cover=arguments.get("cover"),
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
        elif name == "notion_get_page":
            try:
                result = await get_page(
                    page_id=arguments.get("page_id"),
                    filter_properties=arguments.get("filter_properties"),
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
        elif name == "notion_update_page_properties":
            try:
                result = await update_page_properties(
                    page_id=arguments.get("page_id"),
                    properties=arguments.get("properties"),
                    icon=arguments.get("icon"),
                    cover=arguments.get("cover"),
                    archived=arguments.get("archived"),
                    in_trash=arguments.get("in_trash"),
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
        elif name == "notion_query_database":
            try:
                result = await query_database(
                    database_id=arguments.get("database_id"),
                    filter_conditions=arguments.get("filter"),
                    sorts=arguments.get("sorts"),
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
                    filter_properties=arguments.get("filter_properties"),
                    archived=arguments.get("archived"),
                    in_trash=arguments.get("in_trash"),
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
        elif name == "notion_get_database":
            try:
                result = await get_database(database_id=arguments.get("database_id"))
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
        elif name == "notion_create_database":
            try:
                result = await create_database(
                    parent=arguments.get("parent"),
                    title=arguments.get("title"),
                    properties=arguments.get("properties"),
                    icon=arguments.get("icon"),
                    cover=arguments.get("cover"),
                    description=arguments.get("description"),
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
        elif name == "notion_update_database":
            try:
                result = await update_database(
                    database_id=arguments.get("database_id"),
                    title=arguments.get("title"),
                    description=arguments.get("description"),
                    properties=arguments.get("properties"),
                    icon=arguments.get("icon"),
                    cover=arguments.get("cover"),
                    archived=arguments.get("archived"),
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
        elif name == "notion_create_database_item":
            try:
                result = await create_database_item(
                    database_id=arguments.get("database_id"),
                    properties=arguments.get("properties"),
                    children=arguments.get("children"),
                    icon=arguments.get("icon"),
                    cover=arguments.get("cover"),
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

        elif name == "notion_search":
            try:
                result = await search_notion(
                    query=arguments.get("query"),
                    sort=arguments.get("sort"),
                    filter_conditions=arguments.get("filter"),
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
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
        elif name == "notion_get_user":
            try:
                result = await get_user(user_id=arguments.get("user_id"))
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
        elif name == "notion_list_users":
            try:
                result = await list_users(
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
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

        elif name == "notion_create_comment":
            try:
                result = await create_comment(
                    parent=arguments.get("parent"),
                    rich_text=arguments.get("rich_text"),
                    discussion_id=arguments.get("discussion_id"),
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
        elif name == "notion_get_comments":
            try:
                result = await get_comments(
                    block_id=arguments.get("block_id"),
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
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
        elif name == "notion_get_me":
            try:
                result = await get_me()
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
        elif name == "notion_retrieve_page_property":
            try:
                result = await retrieve_page_property(
                    page_id=arguments.get("page_id"),
                    property_id=arguments.get("property_id"),
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
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
        elif name == "notion_retrieve_block":
            try:
                result = await retrieve_block(block_id=arguments.get("block_id"))
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
        elif name == "notion_update_block":
            try:
                result = await update_block(
                    block_id=arguments.get("block_id"),
                    block_type=arguments.get("block_type"),
                    archived=arguments.get("archived"),
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
        elif name == "notion_delete_block":
            try:
                result = await delete_block(block_id=arguments.get("block_id"))
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
        elif name == "notion_get_block_children":
            try:
                result = await get_block_children(
                    block_id=arguments.get("block_id"),
                    start_cursor=arguments.get("start_cursor"),
                    page_size=arguments.get("page_size"),
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
        elif name == "notion_append_block_children":
            try:
                result = await append_block_children(
                    block_id=arguments.get("block_id"),
                    children=arguments.get("children"),
                    after=arguments.get("after"),
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