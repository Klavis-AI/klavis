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

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
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
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""

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
                annotations=types.ToolAnnotations(**{"category": "MOTION_WORKSPACE", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_WORKSPACE", "readOnlyHint": True}),
            ),
            types.Tool(
                name="motion_get_my_user",
                description="Get current user information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "MOTION_USER", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK"}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK"}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK"}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_TASK"}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_PROJECT", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_PROJECT", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_PROJECT"}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_COMMENT", "readOnlyHint": True}),
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
                annotations=types.ToolAnnotations(**{"category": "MOTION_COMMENT"}),
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

    # Set up SSE transport
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        """Handle SSE-based MCP connections."""
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        # Set the API key in context for this request
        token = auth_token_context.set(api_key or "")
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
        """Handle StreamableHTTP-based MCP connections."""
        logger.info("Handling StreamableHTTP request")
        
        # Extract API key from headers
        api_key = extract_api_key(scope)
        
        # Fallback to Authorization header for compatibility
        if not api_key:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Set the API key in context for this request
        token = auth_token_context.set(api_key or "")
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
    exit(main()) 