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

from models import AsanaClient
from utils import RetryableToolError
from constants import (
    TaskSortBy,
    SortOrder,
    TagColor,
)

# Import tools
from tools import tasks as task_tools
from tools import projects as project_tools
from tools import workspaces as workspace_tools
from tools import users as user_tools
from tools import teams as team_tools
from tools import tags as tag_tools

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ASANA_MCP_SERVER_PORT = int(os.getenv("ASANA_MCP_SERVER_PORT", "5001"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_asana_client(access_token: str) -> AsanaClient:
    """Create Asana client with access token."""
    return AsanaClient(auth_token=access_token)

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def get_auth_token_or_empty() -> str:
    """Get the authentication token from context or return empty string."""
    try:
        return auth_token_context.get()
    except LookupError:
        return ""

# Context class to mock the context.get_auth_token_or_empty() calls
class Context:
    def get_auth_token_or_empty(self) -> str:
        return get_auth_token_or_empty()

context = Context()

@click.command()
@click.option("--port", default=ASANA_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    app = Server("asana")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="asana_create_task",
                description="Create a new task in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the task",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date of the task in YYYY-MM-DD format",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "The due date of the task in YYYY-MM-DD format",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the task",
                        },
                        "parent_task_id": {
                            "type": "string",
                            "description": "The ID of the parent task",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "The ID of the workspace",
                        },
                        "project": {
                            "type": "string",
                            "description": "The ID or name of the project",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "The ID of the assignee (defaults to 'me')",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tag names or IDs",
                        },
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="asana_get_task",
                description="Get a task by its ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to get",
                        },
                        "max_subtasks": {
                            "type": "integer",
                            "description": "Maximum number of subtasks to return (0-100, default 100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            types.Tool(
                name="asana_search_tasks",
                description="Search for tasks in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search for in task names and descriptions",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to search in",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "Filter by assignee ID",
                        },
                        "project": {
                            "type": "string",
                            "description": "Project ID or name to filter by",
                        },
                        "team_id": {
                            "type": "string",
                            "description": "Team ID to filter by",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tag names or IDs to filter by",
                        },
                        "due_on": {
                            "type": "string",
                            "description": "Filter tasks due on this date (YYYY-MM-DD)",
                        },
                        "due_on_or_after": {
                            "type": "string",
                            "description": "Filter tasks due on or after this date (YYYY-MM-DD)",
                        },
                        "due_on_or_before": {
                            "type": "string",
                            "description": "Filter tasks due on or before this date (YYYY-MM-DD)",
                        },
                        "start_on": {
                            "type": "string",
                            "description": "Filter tasks starting on this date (YYYY-MM-DD)",
                        },
                        "start_on_or_after": {
                            "type": "string",
                            "description": "Filter tasks starting on or after this date (YYYY-MM-DD)",
                        },
                        "start_on_or_before": {
                            "type": "string",
                            "description": "Filter tasks starting on or before this date (YYYY-MM-DD)",
                        },
                        "completed": {
                            "type": "boolean",
                            "description": "Filter by completion status",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["created_at", "modified_at", "due_date"],
                            "description": "Sort tasks by this field (default: modified_at)",
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["ascending", "descending"],
                            "description": "Sort order (default: descending)",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_update_task",
                description="Update a task in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the task",
                        },
                        "completed": {
                            "type": "boolean",
                            "description": "Mark task as completed (true) or incomplete (false)",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "New start date in YYYY-MM-DD format",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "New due date in YYYY-MM-DD format",
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the task",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "New assignee ID",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            types.Tool(
                name="asana_mark_task_completed",
                description="Mark a task as completed in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to mark as completed",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            types.Tool(
                name="asana_get_subtasks",
                description="Get subtasks from a task in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to get subtasks from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of subtasks to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            types.Tool(
                name="asana_attach_file_to_task",
                description="Attach a file to a task in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to attach the file to",
                        },
                        "file_name": {
                            "type": "string",
                            "description": "The name of the file with extension",
                        },
                        "file_content_str": {
                            "type": "string",
                            "description": "String content of the file (for text files)",
                        },
                        "file_content_base64": {
                            "type": "string",
                            "description": "Base64-encoded binary content (for binary files)",
                        },
                        "file_content_url": {
                            "type": "string",
                            "description": "URL of the file to attach",
                        },
                        "file_encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                        },
                    },
                    "required": ["task_id", "file_name"],
                },
            ),
            types.Tool(
                name="asana_get_projects",
                description="Get projects from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to get projects from",
                        },
                        "team_id": {
                            "type": "string",
                            "description": "The team ID to get projects from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of projects to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_project",
                description="Get a project by its ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to get",
                        },
                    },
                    "required": ["project_id"],
                },
            ),
            types.Tool(
                name="asana_get_workspaces",
                description="Get user's workspaces from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of workspaces to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_workspace",
                description="Get a workspace by its ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The ID of the workspace to get",
                        },
                    },
                    "required": ["workspace_id"],
                },
            ),
            types.Tool(
                name="asana_get_users",
                description="Get users from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to get users from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of users to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_user",
                description="Get a user by their ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user to get",
                        },
                    },
                    "required": ["user_id"],
                },
            ),
            types.Tool(
                name="asana_get_teams",
                description="Get teams from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to get teams from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of teams to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_team",
                description="Get a team by its ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to get",
                        },
                    },
                    "required": ["team_id"],
                },
            ),
            types.Tool(
                name="asana_get_user_teams",
                description="Get teams that the current user is a member of in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to get teams from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of teams to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_tags",
                description="Get tags from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to get tags from",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tags to return (1-100, default 100)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
            ),
            types.Tool(
                name="asana_get_tag",
                description="Get a tag by its ID from Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tag_id": {
                            "type": "string",
                            "description": "The ID of the tag to get",
                        },
                    },
                    "required": ["tag_id"],
                },
            ),
            types.Tool(
                name="asana_create_tag",
                description="Create a tag in Asana",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the tag",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the tag",
                        },
                        "color": {
                            "type": "string",
                            "enum": ["dark-pink", "dark-green", "dark-blue", "dark-red", "dark-teal", "dark-brown", "dark-orange", "dark-purple", "dark-warm-gray", "light-pink", "light-green", "light-blue", "light-red", "light-teal", "light-brown", "light-orange", "light-purple", "light-warm-gray"],
                            "description": "The color of the tag",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "The workspace ID to create the tag in",
                        },
                    },
                    "required": ["name"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        try:
            access_token = get_auth_token()
            
            if name == "asana_create_task":
                result = await task_tools.create_task(access_token, **arguments)
            elif name == "asana_get_task":
                result = await task_tools.get_task_by_id(access_token, **arguments)
            elif name == "asana_search_tasks":
                # Convert string enums to proper enum types
                sort_by = arguments.get("sort_by", "modified_at")
                sort_order = arguments.get("sort_order", "descending")
                
                # Map string values to enum values
                sort_by_map = {
                    "created_at": TaskSortBy.CREATED_AT,
                    "modified_at": TaskSortBy.MODIFIED_AT,
                    "due_date": TaskSortBy.DUE_DATE,
                }
                sort_order_map = {
                    "ascending": SortOrder.ASCENDING,
                    "descending": SortOrder.DESCENDING,
                }
                
                arguments["sort_by"] = sort_by_map.get(sort_by, TaskSortBy.MODIFIED_AT)
                arguments["sort_order"] = sort_order_map.get(sort_order, SortOrder.DESCENDING)
                
                result = await task_tools.search_tasks(access_token, **arguments)
            elif name == "asana_update_task":
                result = await task_tools.update_task(access_token, **arguments)
            elif name == "asana_mark_task_completed":
                result = await task_tools.mark_task_as_completed(access_token, **arguments)
            elif name == "asana_get_subtasks":
                result = await task_tools.get_subtasks_from_a_task(access_token, **arguments)
            elif name == "asana_attach_file_to_task":
                result = await task_tools.attach_file_to_task(access_token, **arguments)
            elif name == "asana_get_projects":
                result = await project_tools.list_projects(access_token, **arguments)
            elif name == "asana_get_project":
                result = await project_tools.get_project_by_id(access_token, **arguments)
            elif name == "asana_get_workspaces":
                result = await workspace_tools.list_workspaces(access_token, **arguments)
            elif name == "asana_get_workspace":
                result = await workspace_tools.get_workspace_by_id(access_token, **arguments)
            elif name == "asana_get_users":
                result = await user_tools.list_users(access_token, **arguments)
            elif name == "asana_get_user":
                result = await user_tools.get_user_by_id(access_token, **arguments)
            elif name == "asana_get_teams":
                result = await team_tools.list_teams(access_token, **arguments)
            elif name == "asana_get_team":
                result = await team_tools.get_team_by_id(access_token, **arguments)
            elif name == "asana_get_user_teams":
                result = await team_tools.list_teams_the_current_user_is_a_member_of(access_token, **arguments)
            elif name == "asana_get_tags":
                result = await tag_tools.list_tags(access_token, **arguments)
            elif name == "asana_get_tag":
                result = await tag_tools.get_tag_by_id(access_token, **arguments)
            elif name == "asana_create_tag":
                # Convert string color to enum if provided
                if "color" in arguments and arguments["color"]:
                    color_map = {
                        "dark-pink": TagColor.DARK_PINK,
                        "dark-green": TagColor.DARK_GREEN,
                        "dark-blue": TagColor.DARK_BLUE,
                        "dark-red": TagColor.DARK_RED,
                        "dark-teal": TagColor.DARK_TEAL,
                        "dark-brown": TagColor.DARK_BROWN,
                        "dark-orange": TagColor.DARK_ORANGE,
                        "dark-purple": TagColor.DARK_PURPLE,
                        "dark-warm-gray": TagColor.DARK_WARM_GRAY,
                        "light-pink": TagColor.LIGHT_PINK,
                        "light-green": TagColor.LIGHT_GREEN,
                        "light-blue": TagColor.LIGHT_BLUE,
                        "light-red": TagColor.LIGHT_RED,
                        "light-teal": TagColor.LIGHT_TEAL,
                        "light-brown": TagColor.LIGHT_BROWN,
                        "light-orange": TagColor.LIGHT_ORANGE,
                        "light-purple": TagColor.LIGHT_PURPLE,
                        "light-warm-gray": TagColor.LIGHT_WARM_GRAY,
                    }
                    arguments["color"] = color_map.get(arguments["color"])
                result = await tag_tools.create_tag(access_token, **arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except RetryableToolError as e:
            logger.error(f"Retryable error in {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "retry_after_ms": e.retry_after_ms,
                        "additional_prompt_content": e.additional_prompt_content,
                        "developer_message": e.developer_message,
                    }, indent=2)
                )
            ]
        except Exception as e:
            logger.exception(f"Error in {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )
            ]

    async def handle_sse(request):
        transport = SseServerTransport("/message")

        # Parse auth token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            auth_token = auth_header[7:]  # Remove "Bearer " prefix
            auth_token_context.set(auth_token)
        else:
            logger.warning("No valid authorization header found")

        async with transport.connect_sse(request) as streams:
            await app.run(
                read_stream=streams[0],
                write_stream=streams[1],
                initialization_options={},
            )

        return Response("", status_code=200)

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        session_manager = StreamableHTTPSessionManager(
            app,
            json_response=json_response,
        )

        # Parse auth token from headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header.startswith("Bearer "):
            auth_token = auth_header[7:]  # Remove "Bearer " prefix
            auth_token_context.set(auth_token)
        else:
            logger.warning("No valid authorization header found")

        await session_manager(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        logger.info(f"Asana MCP Server starting on port {port}")
        yield
        logger.info("Asana MCP Server shutting down")

    routes = [
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/", handle_streamable_http),
    ]

    starlette_app = Starlette(
        debug=True,
        routes=routes,
        lifespan=lifespan,
    )

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