import contextlib
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

from tools import (
    auth_token_context,
    get_tasks, get_task, create_task, update_task, delete_task, search_tasks,
    get_projects, get_project, create_project,
    get_comments, create_comment,
    get_users, get_my_user,
    get_workspaces
)

logger = logging.getLogger(__name__)

load_dotenv()

MOTION_MCP_SERVER_PORT = int(os.getenv("MOTION_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=MOTION_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("motion-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="motion_get_workspaces",
                description="Get all workspaces in the Motion account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="motion_get_users",
                description="Get all users, optionally filtered by workspace.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace ID to filter users by workspace.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_get_my_user",
                description="Get current user information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="motion_get_tasks",
                description="Get tasks, optionally filtered by workspace.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace ID to filter tasks by workspace.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_get_task",
                description="Get a specific task by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_create_task",
                description="Create a new task in Motion.",
                inputSchema={
                    "type": "object",
                    "required": ["name", "workspace_id"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the task.",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "The ID of the workspace to create the task in.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the task.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The status of the task.",
                        },
                        "priority": {
                            "type": "string",
                            "description": "The priority of the task.",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "The ID of the user to assign the task to.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to assign the task to.",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "The due date for the task (ISO date string).",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_update_task",
                description="Update an existing task in Motion.",
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
                            "type": "string",
                            "description": "The new priority of the task.",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "The ID of the user to assign the task to.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to assign the task to.",
                        },
                        "due_date": {
                            "type": "string",
                            "description": "The new due date for the task (ISO date string).",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_delete_task",
                description="Delete a task from Motion.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to delete.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_search_tasks",
                description="Search for tasks by name or description.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find tasks.",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace ID to limit search to specific workspace.",
                        },
                    },
                },
            ),

            types.Tool(
                name="motion_get_projects",
                description="Get projects, optionally filtered by workspace.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workspace_id": {
                            "type": "string",
                            "description": "Optional workspace ID to filter projects by workspace.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_get_project",
                description="Get a specific project by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_create_project",
                description="Create a new project in Motion.",
                inputSchema={
                    "type": "object",
                    "required": ["name", "workspace_id"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the project.",
                        },
                        "workspace_id": {
                            "type": "string",
                            "description": "The ID of the workspace to create the project in.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the project.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The status of the project.",
                        },
                    },
                },
            ),
            types.Tool(
                name="motion_get_comments",
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
            ),
            types.Tool(
                name="motion_create_comment",
                description="Create a comment on a task.",
                inputSchema={
                    "type": "object",
                    "required": ["task_id", "content"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to comment on.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The content of the comment.",
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "motion_get_workspaces":
            try:
                result = await get_workspaces()
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
        
        elif name == "motion_get_users":
            workspace_id = arguments.get("workspace_id")
            try:
                result = await get_users(workspace_id)
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
        
        elif name == "motion_get_my_user":
            try:
                result = await get_my_user()
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
        
        elif name == "motion_get_tasks":
            workspace_id = arguments.get("workspace_id")
            try:
                result = await get_tasks(workspace_id)
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
        
        elif name == "motion_get_task":
            task_id = arguments.get("task_id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: task_id parameter is required",
                    )
                ]
            try:
                result = await get_task(task_id)
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
        
        elif name == "motion_create_task":
            name_param = arguments.get("name")
            workspace_id = arguments.get("workspace_id")
            if not name_param or not workspace_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name and workspace_id parameters are required",
                    )
                ]
            
            description = arguments.get("description")
            status = arguments.get("status")
            priority = arguments.get("priority")
            assignee_id = arguments.get("assignee_id")
            project_id = arguments.get("project_id")
            due_date = arguments.get("due_date")
            
            try:
                result = await create_task(
                    name_param, workspace_id, description, status, 
                    priority, assignee_id, project_id, due_date
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
        
        elif name == "motion_update_task":
            task_id = arguments.get("task_id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: task_id parameter is required",
                    )
                ]
            
            name_param = arguments.get("name")
            description = arguments.get("description")
            status = arguments.get("status")
            priority = arguments.get("priority")
            assignee_id = arguments.get("assignee_id")
            project_id = arguments.get("project_id")
            due_date = arguments.get("due_date")
            
            try:
                result = await update_task(
                    task_id, name_param, description, status, 
                    priority, assignee_id, project_id, due_date
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
        
        elif name == "motion_delete_task":
            task_id = arguments.get("task_id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: task_id parameter is required",
                    )
                ]
            try:
                result = await delete_task(task_id)
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
        
        elif name == "motion_search_tasks":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            workspace_id = arguments.get("workspace_id")
            try:
                result = await search_tasks(query, workspace_id)
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
        

        elif name == "motion_get_projects":
            workspace_id = arguments.get("workspace_id")
            try:
                result = await get_projects(workspace_id)
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
        
        elif name == "motion_get_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
            try:
                result = await get_project(project_id)
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
        
        elif name == "motion_create_project":
            name_param = arguments.get("name")
            workspace_id = arguments.get("workspace_id")
            if not name_param or not workspace_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name and workspace_id parameters are required",
                    )
                ]
            
            description = arguments.get("description")
            status = arguments.get("status")
            
            try:
                result = await create_project(name_param, workspace_id, description, status)
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
        
        elif name == "motion_get_comments":
            task_id = arguments.get("task_id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: task_id parameter is required",
                    )
                ]
            try:
                result = await get_comments(task_id)
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
        
        elif name == "motion_create_comment":
            task_id = arguments.get("task_id")
            content = arguments.get("content")
            if not task_id or not content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: task_id and content parameters are required",
                    )
                ]
            try:
                result = await create_comment(task_id, content)
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
        
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    async def handle_sse(request):
        """Handle SSE-based MCP connections."""
        async with SseServerTransport("/message") as transport:
            try:
                # Set authentication token from Authorization header
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]  # Remove "Bearer " prefix
                    auth_token_context.set(token)
                else:
                    raise ValueError("Authorization header must be in format 'Bearer <token>'")
                
                await app.run(transport, types.RequestMessage, types.NotificationMessage, request)
            except Exception as e:
                logger.exception("Error in SSE handler: %s", e)
                raise

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle StreamableHTTP-based MCP connections."""
        manager = StreamableHTTPSessionManager()
        
        # Extract authentication token from Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            auth_token_context.set(token)
        else:
            # Return 401 Unauthorized if no valid token provided
            response = Response(
                content=json.dumps({"error": "Authorization header required"}),
                status_code=401,
                headers={"content-type": "application/json"}
            )
            await response(scope, receive, send)
            return

        async def _run_server():
            async with manager.create_session() as session:
                return await app.run(
                    session,
                    types.RequestMessage,
                    types.NotificationMessage,
                    json_response=json_response,
                )

        await manager.handle_request(scope, receive, send, _run_server)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        yield

    # Create the Starlette application
    starlette_app = Starlette(
        lifespan=lifespan,
        routes=[
            Route("/sse", handle_sse, methods=["GET"]),
            Mount("/", handle_streamable_http),
        ],
    )

    # Start the server
    import uvicorn
    logger.info(f"Starting Motion MCP Server on port {port}")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    exit(main()) 