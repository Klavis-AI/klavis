import contextlib
import logging
import os
import json
import base64
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

from tools import (
    auth_token_context,
    get_teams, get_workspaces,
    get_spaces, create_space, update_space,
    get_folders, create_folder, update_folder,
    get_lists, create_list, update_list,
    get_tasks, get_task_by_id, create_task, update_task, search_tasks,
    get_comments, create_comment, update_comment,
    get_user, get_team_members
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CLICKUP_MCP_SERVER_PORT = int(os.getenv("CLICKUP_MCP_SERVER_PORT", "5000"))

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
@click.option("--port", default=CLICKUP_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("clickup-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Team/Workspace tools
            types.Tool(
                name="clickup_get_teams",
                description="Get all teams/workspaces the user has access to.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TEAM", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_get_workspaces",
                description="Get all workspaces (alias for get_teams).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_WORKSPACE", "readOnlyHint": True}
                ),
            ),
            
            # Space tools
            types.Tool(
                name="clickup_get_spaces",
                description="Get all spaces in a team.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id"],
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to get spaces from.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_SPACE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_create_space",
                description="Create a new space in a team.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id", "name"],
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to create the space in.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the space.",
                        },
                        "color": {
                            "type": "string",
                            "description": "The color for the space (optional).",
                        },
                        "private": {
                            "type": "boolean",
                            "description": "Whether the space should be private (default: false).",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_SPACE"}
                ),
            ),
            types.Tool(
                name="clickup_update_space",
                description="Update an existing space.",
                inputSchema={
                    "type": "object",
                    "required": ["space_id"],
                    "properties": {
                        "space_id": {
                            "type": "string",
                            "description": "The ID of the space to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the space.",
                        },
                        "color": {
                            "type": "string",
                            "description": "The new color for the space.",
                        },
                        "private": {
                            "type": "boolean",
                            "description": "Whether the space should be private.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_SPACE"}
                ),
            ),
            
            # Folder tools
            types.Tool(
                name="clickup_get_folders",
                description="Get all folders in a space.",
                inputSchema={
                    "type": "object",
                    "required": ["space_id"],
                    "properties": {
                        "space_id": {
                            "type": "string",
                            "description": "The ID of the space to get folders from.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_FOLDER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_create_folder",
                description="Create a new folder in a space.",
                inputSchema={
                    "type": "object",
                    "required": ["space_id", "name"],
                    "properties": {
                        "space_id": {
                            "type": "string",
                            "description": "The ID of the space to create the folder in.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the folder.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_FOLDER"}
                ),
            ),
            types.Tool(
                name="clickup_update_folder",
                description="Update an existing folder.",
                inputSchema={
                    "type": "object",
                    "required": ["folder_id", "name"],
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The ID of the folder to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the folder.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_FOLDER"}
                ),
            ),
            
            # List tools
            types.Tool(
                name="clickup_get_lists",
                description="Get all lists in a folder or space. Either folder_id or space_id must be provided.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The ID of the folder to get lists from.",
                        },
                        "space_id": {
                            "type": "string",
                            "description": "The ID of the space to get lists from.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_LIST", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_create_list",
                description="Create a new list in a folder or space. Either folder_id or space_id must be provided along with name.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "folder_id": {
                            "type": "string",
                            "description": "The ID of the folder to create the list in.",
                        },
                        "space_id": {
                            "type": "string",
                            "description": "The ID of the space to create the list in.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the list.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The description/content of the list.",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date for the list (ISO date string).",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority level (1=urgent, 2=high, 3=normal, 4=low).",
                        },
                        "assignee": {
                            "type": "string",
                            "description": "User ID to assign the list to.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Status of the list.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_LIST"}
                ),
            ),
            types.Tool(
                name="clickup_update_list",
                description="Update an existing list.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "The ID of the list to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the list.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The new description/content of the list.",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "New due date for the list (ISO date string).",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "New priority level (1=urgent, 2=high, 3=normal, 4=low).",
                        },
                        "assignee": {
                            "type": "string",
                            "description": "User ID to assign the list to.",
                        },
                        "unset_status": {
                            "type": "boolean",
                            "description": "Whether to unset the status.",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_LIST"}
                ),
            ),
            
            # Task tools - continuing from line 316
            types.Tool(
                name="clickup_get_tasks",
                description="Get tasks from a list with optional filtering.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id"],
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "The ID of the list to get tasks from.",
                        },
                        "archived": {
                            "type": "boolean",
                            "description": "Include archived tasks (default: false).",
                            "default": False,
                        },
                        "include_closed": {
                            "type": "boolean",
                            "description": "Include closed tasks (default: false).",
                            "default": False,
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (default: 0).",
                            "default": 0,
                        },
                        "subtasks": {
                            "type": "boolean",
                            "description": "Include subtasks (default: false).",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TASK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_get_task_by_id",
                description="Get a specific task by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to retrieve.",
                        },
                        "include_subtasks": {
                            "type": "boolean",
                            "description": "Include subtasks (default: false).",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TASK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_create_task",
                description="Create a new task in ClickUp.",
                inputSchema={
                    "type": "object",
                    "required": ["list_id", "name"],
                    "properties": {
                        "list_id": {
                            "type": "string",
                            "description": "The ID of the list to create the task in.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the task.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the task.",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of user IDs to assign the task to.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The status of the task.",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Priority level (1=urgent, 2=high, 3=normal, 4=low).",
                        },
                        "due_date": {
                            "type": "integer",
                            "description": "Due date as Unix timestamp in milliseconds.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TASK"}
                ),
            ),
            types.Tool(
                name="clickup_update_task",
                description="Update an existing task in ClickUp.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the task.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The new description of the task.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The new status of the task.",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "New priority level (1=urgent, 2=high, 3=normal, 4=low).",
                        },
                        "due_date": {
                            "type": "integer",
                            "description": "New due date as Unix timestamp in milliseconds.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TASK"}
                ),
            ),
            types.Tool(
                name="clickup_search_tasks",
                description="Search for tasks by text query.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id", "query"],
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to search in.",
                        },
                        "query": {
                            "type": "string",
                            "description": "The text to search for in task names and descriptions.",
                        },
                        "start": {
                            "type": "integer",
                            "description": "Starting position for pagination (default: 0).",
                            "default": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 20).",
                            "default": 20,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_TASK", "readOnlyHint": True}
                ),
            ),
            
            # Comment tools
            types.Tool(
                name="clickup_get_comments",
                description="Get comments for a specific task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to get comments for.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_COMMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_create_comment",
                description="Create a comment on a task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id", "comment_text"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to comment on.",
                        },
                        "comment_text": {
                            "type": "string",
                            "description": "The content of the comment.",
                        },
                        "notify_all": {
                            "type": "boolean",
                            "description": "Whether to notify all task watchers (default: true).",
                            "default": True,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_COMMENT"}
                ),
            ),
            types.Tool(
                name="clickup_update_comment",
                description="Update an existing comment.",
                inputSchema={
                    "type": "object",
                    "required": ["comment_id", "comment_text"],
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "The ID of the comment to update.",
                        },
                        "comment_text": {
                            "type": "string",
                            "description": "The new content of the comment.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_COMMENT"}
                ),
            ),
            
            # User tools
            types.Tool(
                name="clickup_get_user",
                description="Get the current user's information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_USER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="clickup_get_team_members",
                description="Get all team members.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id"],
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to get members from.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLICKUP_USER", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        try:
            if name == "clickup_get_teams":
                result = await get_teams()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_workspaces":
                result = await get_workspaces()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_spaces":
                team_id = arguments.get("team_id")
                if not team_id:
                    return [types.TextContent(type="text", text="Error: team_id parameter is required")]
                result = await get_spaces(team_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_create_space":
                team_id = arguments.get("team_id")
                name = arguments.get("name")
                if not team_id or not name:
                    return [types.TextContent(type="text", text="Error: team_id and name parameters are required")]
                color = arguments.get("color")
                private = arguments.get("private", False)
                result = await create_space(team_id, name, color, private)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_update_space":
                space_id = arguments.get("space_id")
                if not space_id:
                    return [types.TextContent(type="text", text="Error: space_id parameter is required")]
                name = arguments.get("name")
                color = arguments.get("color")
                private = arguments.get("private")
                result = await update_space(space_id, name, color, private)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_folders":
                space_id = arguments.get("space_id")
                if not space_id:
                    return [types.TextContent(type="text", text="Error: space_id parameter is required")]
                result = await get_folders(space_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_create_folder":
                space_id = arguments.get("space_id")
                name = arguments.get("name")
                if not space_id or not name:
                    return [types.TextContent(type="text", text="Error: space_id and name parameters are required")]
                result = await create_folder(space_id, name)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_update_folder":
                folder_id = arguments.get("folder_id")
                name = arguments.get("name")
                if not folder_id or not name:
                    return [types.TextContent(type="text", text="Error: folder_id and name parameters are required")]
                result = await update_folder(folder_id, name)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_lists":
                folder_id = arguments.get("folder_id")
                space_id = arguments.get("space_id")
                if not folder_id and not space_id:
                    return [types.TextContent(type="text", text="Error: either folder_id or space_id parameter is required")]
                result = await get_lists(folder_id, space_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_create_list":
                folder_id = arguments.get("folder_id")
                space_id = arguments.get("space_id")
                name = arguments.get("name")
                if not name:
                    return [types.TextContent(type="text", text="Error: name parameter is required")]
                if not folder_id and not space_id:
                    return [types.TextContent(type="text", text="Error: either folder_id or space_id parameter is required")]
                content = arguments.get("content")
                due_date = arguments.get("due_date")
                priority = arguments.get("priority")
                assignee = arguments.get("assignee")
                status = arguments.get("status")
                result = await create_list(folder_id, space_id, name, content, due_date, priority, assignee, status)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_update_list":
                list_id = arguments.get("list_id")
                if not list_id:
                    return [types.TextContent(type="text", text="Error: list_id parameter is required")]
                name = arguments.get("name")
                content = arguments.get("content")
                due_date = arguments.get("due_date")
                priority = arguments.get("priority")
                assignee = arguments.get("assignee")
                unset_status = arguments.get("unset_status", False)
                result = await update_list(list_id, name, content, due_date, priority, assignee, unset_status)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_tasks":
                list_id = arguments.get("list_id")
                if not list_id:
                    return [types.TextContent(type="text", text="Error: list_id parameter is required")]
                archived = arguments.get("archived", False)
                include_closed = arguments.get("include_closed", False)
                page = arguments.get("page", 0)
                subtasks = arguments.get("subtasks", False)
                result = await get_tasks(list_id, archived, include_closed, page, subtasks=subtasks)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_task_by_id":
                task_id = arguments.get("task_id")
                if not task_id:
                    return [types.TextContent(type="text", text="Error: task_id parameter is required")]
                include_subtasks = arguments.get("include_subtasks", False)
                result = await get_task_by_id(task_id, include_subtasks=include_subtasks)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_create_task":
                list_id = arguments.get("list_id")
                name = arguments.get("name")
                if not list_id or not name:
                    return [types.TextContent(type="text", text="Error: list_id and name parameters are required")]
                description = arguments.get("description")
                assignees = arguments.get("assignees")
                status = arguments.get("status")
                priority = arguments.get("priority")
                due_date = arguments.get("due_date")
                result = await create_task(list_id, name, description, assignees, None, status, priority, due_date)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_update_task":
                task_id = arguments.get("task_id")
                if not task_id:
                    return [types.TextContent(type="text", text="Error: task_id parameter is required")]
                name = arguments.get("name")
                description = arguments.get("description")
                status = arguments.get("status")
                priority = arguments.get("priority")
                due_date = arguments.get("due_date")
                result = await update_task(task_id, name, description, status, priority, due_date)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_search_tasks":
                team_id = arguments.get("team_id")
                query = arguments.get("query")
                if not team_id or not query:
                    return [types.TextContent(type="text", text="Error: team_id and query parameters are required")]
                start = arguments.get("start", 0)
                limit = arguments.get("limit", 20)
                result = await search_tasks(team_id, query, start, limit)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_comments":
                task_id = arguments.get("task_id")
                if not task_id:
                    return [types.TextContent(type="text", text="Error: task_id parameter is required")]
                result = await get_comments(task_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_create_comment":
                task_id = arguments.get("task_id")
                comment_text = arguments.get("comment_text")
                if not task_id or not comment_text:
                    return [types.TextContent(type="text", text="Error: task_id and comment_text parameters are required")]
                notify_all = arguments.get("notify_all", True)
                result = await create_comment(task_id, comment_text, notify_all=notify_all)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_update_comment":
                comment_id = arguments.get("comment_id")
                comment_text = arguments.get("comment_text")
                if not comment_id or not comment_text:
                    return [types.TextContent(type="text", text="Error: comment_id and comment_text parameters are required")]
                result = await update_comment(comment_id, comment_text)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_user":
                result = await get_user()
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            elif name == "clickup_get_team_members":
                team_id = arguments.get("team_id")
                if not team_id:
                    return [types.TextContent(type="text", text="Error: team_id parameter is required")]
                result = await get_team_members(team_id)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
                
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

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