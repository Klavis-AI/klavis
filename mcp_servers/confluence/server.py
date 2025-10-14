import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict

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

from errors import ToolExecutionError, AuthenticationError, TokenExpiredError, InvalidTokenError

# Import tools
from tools import (
    # Page tools
    create_page, get_page, get_pages_by_id, list_pages, rename_page, 
    update_page_content,
    # Space tools
    create_space, get_space, get_space_hierarchy, list_spaces,
    # Search tools
    search_content,
    # Attachment tools
    get_attachments_for_page, list_attachments, get_attachment,
)

from enums import (
    convert_sort_by_to_enum, convert_sort_order_to_enum, convert_update_mode_to_enum
)

# Import context for auth token
from client import auth_token_context


# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CONFLUENCE_MCP_SERVER_PORT = int(os.getenv("CONFLUENCE_MCP_SERVER_PORT", "5000"))

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
@click.option("--port", default=CONFLUENCE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = Server("confluence-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Page tools
            types.Tool(
                name="confluence_create_page",
                description="Create a new page in Confluence",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_identifier": {
                            "type": "string",
                            "description": "The ID or title of the space to create the page in",
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the page",
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the page. Only plain text is supported",
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "The ID of the parent. If not provided, the page will be created at the root of the space.",
                        },
                        "is_private": {
                            "type": "boolean",
                            "description": "If true, then only the user who creates this page will be able to see it. Defaults to False",
                        },
                        "is_draft": {
                            "type": "boolean",
                            "description": "If true, then the page will be created as a draft. Defaults to False",
                        },
                    },
                    "required": ["space_identifier", "title", "content"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE"}
                ),
            ),
            types.Tool(
                name="confluence_get_page",
                description="Retrieve a SINGLE page's content by its ID or title. For retrieving MULTIPLE pages, use confluence_get_pages_by_id instead",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_identifier": {
                            "type": "string",
                            "description": "Can be a page's ID or title. Numerical titles are NOT supported.",
                        },
                    },
                    "required": ["page_identifier"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_get_pages_by_id",
                description="Get the content of MULTIPLE pages by their ID in a single efficient request",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The IDs of the pages to get. IDs are numeric. Titles of pages are NOT supported. Maximum of 250 page ids supported.",
                        },
                    },
                    "required": ["page_ids"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_list_pages",
                description="Get the content of multiple pages with optional filtering and sorting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Restrict the response to only include pages in these spaces. Only space IDs are supported. Titles of spaces are NOT supported. Maximum of 100 space ids supported.",
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "The order of the pages to sort by. Defaults to created-date-newest-to-oldest",
                            "enum": ["id-ascending", "id-descending", "title-ascending", "title-descending", 
                                   "created-date-oldest-to-newest", "created-date-newest-to-oldest",
                                   "modified-date-oldest-to-newest", "modified-date-newest-to-oldest"],
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of pages to return. Defaults to 25. Max is 250",
                            "minimum": 1,
                            "maximum": 250,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to use for the next page of results",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_update_page_content",
                description="Update a page's content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_identifier": {
                            "type": "string",
                            "description": "The ID or title of the page to update. Numerical titles are NOT supported.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the page. Only plain text is supported",
                        },
                        "update_mode": {
                            "type": "string",
                            "description": "The mode of update. Defaults to 'append'.",
                            "enum": ["prepend", "append", "replace"],
                        },
                    },
                    "required": ["page_identifier", "content"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE"}
                ),
            ),
            types.Tool(
                name="confluence_rename_page",
                description="Rename a page by changing its title",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_identifier": {
                            "type": "string",
                            "description": "The ID or title of the page to rename. Numerical titles are NOT supported.",
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the page",
                        },
                    },
                    "required": ["page_identifier", "title"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_PAGE"}
                ),
            ),
            # Space tools
            types.Tool(
                name="confluence_create_space",
                description="Create a new space in Confluence",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the space",
                        },
                        "key": {
                            "type": "string",
                            "description": "The key of the space. If not provided, one will be generated automatically",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the space",
                        },
                        "is_private": {
                            "type": "boolean",
                            "description": "If true, the space will be private to the creator. Defaults to False",
                        },
                    },
                    "required": ["name"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_SPACE"}
                ),
            ),
            types.Tool(
                name="confluence_list_spaces",
                description="List all spaces sorted by name in ascending order",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of spaces to return. Defaults to 25. Max is 250",
                            "minimum": 1,
                            "maximum": 250,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to use for the next page of results",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_SPACE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_get_space",
                description="Get the details of a space by its ID or key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_identifier": {
                            "type": "string",
                            "description": "Can be a space's ID or key. Numerical keys are NOT supported",
                        },
                    },
                    "required": ["space_identifier"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_SPACE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_get_space_hierarchy",
                description="Retrieve the full hierarchical structure of a Confluence space as a tree structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "space_identifier": {
                            "type": "string",
                            "description": "Can be a space's ID or key. Numerical keys are NOT supported",
                        },
                    },
                    "required": ["space_identifier"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_SPACE", "readOnlyHint": True}
                ),
            ),
            # Search tools
            types.Tool(
                name="confluence_search_content",
                description="Search for content in Confluence. The search is performed across all content in the authenticated user's Confluence workspace. All search terms in Confluence are case insensitive.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "must_contain_all": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Words/phrases that content MUST contain (AND logic). Each item can be: single word or multi-word phrase. All items in this list must be present for content to match.",
                        },
                        "can_contain_any": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Words/phrases where content can contain ANY of these (OR logic). Content matching ANY item in this list will be included.",
                        },
                        "enable_fuzzy": {
                            "type": "boolean",
                            "description": "Enable fuzzy matching to find similar terms (e.g. 'roam' will find 'foam'). Defaults to True",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-100). Defaults to 25",
                            "minimum": 1,
                            "maximum": 100,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_SEARCH", "readOnlyHint": True}
                ),
            ),
            # Attachment tools
            types.Tool(
                name="confluence_list_attachments",
                description="List attachments in a workspace",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sort_order": {
                            "type": "string",
                            "description": "The order of the attachments to sort by. Defaults to created-date-newest-to-oldest",
                            "enum": ["created-date-oldest-to-newest", "created-date-newest-to-oldest",
                                   "modified-date-oldest-to-newest", "modified-date-newest-to-oldest"],
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of attachments to return. Defaults to 25. Max is 250",
                            "minimum": 1,
                            "maximum": 250,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to use for the next page of results",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_ATTACHMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_get_attachments_for_page",
                description="Get attachments for a page by its ID or title. If a page title is provided, then the first page with an exact matching title will be returned.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_identifier": {
                            "type": "string",
                            "description": "The ID or title of the page to get attachments for",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of attachments to return. Defaults to 25. Max is 250",
                            "minimum": 1,
                            "maximum": 250,
                        },
                        "pagination_token": {
                            "type": "string",
                            "description": "The pagination token to use for the next page of results",
                        },
                    },
                    "required": ["page_identifier"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_ATTACHMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="confluence_get_attachment",
                description="Get a specific attachment by its ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "attachment_id": {
                            "type": "string",
                            "description": "The ID of the attachment to get",
                        },
                    },
                    "required": ["attachment_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CONFLUENCE_ATTACHMENT", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        try:
            # Page tools
            if name == "confluence_create_page":
                result = await create_page(
                    space_identifier=arguments["space_identifier"],
                    title=arguments["title"],
                    content=arguments["content"],
                    parent_id=arguments.get("parent_id"),
                    is_private=arguments.get("is_private", False),
                    is_draft=arguments.get("is_draft", False),
                )
            elif name == "confluence_get_page":
                result = await get_page(
                    page_identifier=arguments["page_identifier"],
                )
            elif name == "confluence_get_pages_by_id":
                result = await get_pages_by_id(
                    page_ids=arguments["page_ids"],
                )
            elif name == "confluence_list_pages":
                result = await list_pages(
                    space_ids=arguments.get("space_ids"),
                    sort_by=convert_sort_by_to_enum(arguments.get("sort_by")),
                    limit=arguments.get("limit", 25),
                    pagination_token=arguments.get("pagination_token"),
                )
            elif name == "confluence_update_page_content":
                result = await update_page_content(
                    page_identifier=arguments["page_identifier"],
                    content=arguments["content"],
                    update_mode=convert_update_mode_to_enum(arguments.get("update_mode", "append")),
                )
            elif name == "confluence_rename_page":
                result = await rename_page(
                    page_identifier=arguments["page_identifier"],
                    title=arguments["title"],
                )
            # Space tools
            elif name == "confluence_create_space":
                result = await create_space(
                    name=arguments["name"],
                    key=arguments.get("key"),
                    description=arguments.get("description"),
                    is_private=arguments.get("is_private", False),
                )
            elif name == "confluence_list_spaces":
                result = await list_spaces(
                    limit=arguments.get("limit", 25),
                    pagination_token=arguments.get("pagination_token"),
                )
            elif name == "confluence_get_space":
                result = await get_space(
                    space_identifier=arguments["space_identifier"],
                )
            elif name == "confluence_get_space_hierarchy":
                result = await get_space_hierarchy(
                    space_identifier=arguments["space_identifier"],
                )
            # Search tools
            elif name == "confluence_search_content":
                result = await search_content(
                    must_contain_all=arguments.get("must_contain_all"),
                    can_contain_any=arguments.get("can_contain_any"),
                    enable_fuzzy=arguments.get("enable_fuzzy", True),
                    limit=arguments.get("limit", 25),
                )
            # Attachment tools
            elif name == "confluence_list_attachments":
                result = await list_attachments(
                    sort_order=convert_sort_order_to_enum(arguments.get("sort_order")),
                    limit=arguments.get("limit", 25),
                    pagination_token=arguments.get("pagination_token"),
                )
            elif name == "confluence_get_attachments_for_page":
                result = await get_attachments_for_page(
                    page_identifier=arguments["page_identifier"],
                    limit=arguments.get("limit", 25),
                    pagination_token=arguments.get("pagination_token"),
                )
            elif name == "confluence_get_attachment":
                result = await get_attachment(
                    attachment_id=arguments["attachment_id"],
                )
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except (AuthenticationError, TokenExpiredError, InvalidTokenError, ToolExecutionError) as e:
            logger.error(f"Confluence error in {name}: {e}")
            error_response = {
                "error": str(e),
                "developer_message": getattr(e, "developer_message", ""),
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        except Exception as e:
            logger.exception(f"Unexpected error in tool {name}")
            error_response = {
                "error": f"Unexpected error: {str(e)}",
                "developer_message": f"Unexpected error in tool {name}: {type(e).__name__}: {str(e)}",
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

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

    try:
        uvicorn.run(
            starlette_app,
            host="0.0.0.0",
            port=port,
            log_level=log_level.lower(),
        )
        return 0
    except Exception as e:
        logger.exception(f"Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 