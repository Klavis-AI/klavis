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
    get_teams,
    get_issues, get_issue_by_id, create_issue, update_issue, search_issues,
    get_projects, create_project, update_project,
    get_comments, create_comment, update_comment
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

LINEAR_MCP_SERVER_PORT = int(os.getenv("LINEAR_MCP_SERVER_PORT", "5000"))

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
@click.option("--port", default=LINEAR_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("linear-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="linear_get_teams",
                description="Get all teams in the Linear workspace including workflow states and team members.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_TEAM", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="linear_get_issues",
                description="Get issues, optionally filtering by team or timestamps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "Optional team ID to filter issues by team.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of issues to return (default: 10).",
                            "default": 10,
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filter object for issues",
                            "properties": {
                                "priority": {
                                    "type": "integer",
                                    "description": "Filter by priority (0=No Priority, 1=Urgent, 2=High, 3=Medium, 4=Low)"
                                },
                                "updatedAt": {
                                    "type": "object",
                                    "description": "Filter by update timestamp for issues.",
                                    "properties": {
                                        "gte": {"type": "string", "description": "Greater than or equal to timestamp (ISO 8601)"},
                                        "gt": {"type": "string", "description": "Greater than timestamp (ISO 8601)"},
                                        "lte": {"type": "string", "description": "Less than or equal to timestamp (ISO 8601)"},
                                        "lt": {"type": "string", "description": "Less than timestamp (ISO 8601)"},
                                        "eq": {"type": "string", "description": "Equal to timestamp (ISO 8601)"},
                                    },
                                },
                                "createdAt": {
                                    "type": "object",
                                    "description": "Filter by creation timestamp for issues.",
                                    "properties": {
                                        "gte": {"type": "string", "description": "Greater than or equal to timestamp (ISO 8601)"},
                                        "gt": {"type": "string", "description": "Greater than timestamp (ISO 8601)"},
                                        "lte": {"type": "string", "description": "Less than or equal to timestamp (ISO 8601)"},
                                        "lt": {"type": "string", "description": "Less than timestamp (ISO 8601)"},
                                        "eq": {"type": "string", "description": "Equal to timestamp (ISO 8601)"},
                                    },
                                },
                            },
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_ISSUE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="linear_get_issue_by_id",
                description="Get a specific issue by its ID.",
                inputSchema={
                    "type": "object",
                    "required": ["issue_id"],
                    "properties": {
                        "issue_id": {
                            "type": "string",
                            "description": "The ID of the issue to retrieve.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_ISSUE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="linear_create_issue",
                description="Create a new issue in Linear.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id", "title"],
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The ID of the team to create the issue in.",
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the issue.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the issue in markdown format.",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "The ID of the user to assign the issue to.",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "The priority of the issue (0=None, 1=Urgent, 2=High, 3=Normal, 4=Low).",
                        },
                        "state_id": {
                            "type": "string",
                            "description": "The ID of the workflow state to assign the issue to.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to assign the issue to.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_ISSUE"}
                ),
            ),
            types.Tool(
                name="linear_update_issue",
                description="Update an existing issue in Linear.",
                inputSchema={
                    "type": "object",
                    "required": ["issue_id"],
                    "properties": {
                        "issue_id": {
                            "type": "string",
                            "description": "The ID of the issue to update.",
                        },
                        "title": {
                            "type": "string",
                            "description": "The new title of the issue.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The new description of the issue in markdown format.",
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "The ID of the user to assign the issue to.",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "The priority of the issue (0=None, 1=Urgent, 2=High, 3=Normal, 4=Low).",
                        },
                        "state_id": {
                            "type": "string",
                            "description": "The ID of the workflow state to assign the issue to.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to assign the issue to.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_ISSUE"}
                ),
            ),
            types.Tool(
                name="linear_get_projects",
                description="Get projects, optionally filtering by team or timestamps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "Optional team ID to filter projects by team.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of projects to return (default: 50).",
                            "default": 50,
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filter object for projects.",
                            "properties": {
                                "updatedAt": {
                                    "type": "object",
                                    "description": "Filter by update timestamp for projects.",
                                    "properties": {
                                        "gte": {"type": "string", "description": "Greater than or equal to timestamp (ISO 8601)"},
                                        "gt": {"type": "string", "description": "Greater than timestamp (ISO 8601)"},
                                        "lte": {"type": "string", "description": "Less than or equal to timestamp (ISO 8601)"},
                                        "lt": {"type": "string", "description": "Less than timestamp (ISO 8601)"},
                                        "eq": {"type": "string", "description": "Equal to timestamp (ISO 8601)"},
                                    },
                                },
                                "createdAt": {
                                    "type": "object",
                                    "description": "Filter by creation timestamp for projects.",
                                    "properties": {
                                        "gte": {"type": "string", "description": "Greater than or equal to timestamp (ISO 8601)"},
                                        "gt": {"type": "string", "description": "Greater than timestamp (ISO 8601)"},
                                        "lte": {"type": "string", "description": "Less than or equal to timestamp (ISO 8601)"},
                                        "lt": {"type": "string", "description": "Less than timestamp (ISO 8601)"},
                                        "eq": {"type": "string", "description": "Equal to timestamp (ISO 8601)"},
                                    },
                                },
                            },
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_PROJECT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="linear_create_project",
                description="Create a new project in Linear.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the project.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the project.",
                        },
                        "team_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of team IDs to associate with the project.",
                        },
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the user to set as project lead.",
                        },
                        "target_date": {
                            "type": "string",
                            "description": "The target completion date for the project (ISO date string).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_PROJECT"}
                ),
            ),
            types.Tool(
                name="linear_update_project",
                description="Update an existing project in Linear.",
                inputSchema={
                    "type": "object",
                    "required": ["project_id"],
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID of the project to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the project.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The new description of the project.",
                        },
                        "state": {
                            "type": "string",
                            "description": "The new state of the project (planned, started, completed, canceled).",
                        },
                        "target_date": {
                            "type": "string",
                            "description": "The new target completion date (ISO date string).",
                        },
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the user to set as project lead.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_PROJECT"}
                ),
            ),
            types.Tool(
                name="linear_get_comments",
                description="Get comments for a specific issue.",
                inputSchema={
                    "type": "object",
                    "required": ["issue_id"],
                    "properties": {
                        "issue_id": {
                            "type": "string",
                            "description": "The ID of the issue to get comments for.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_COMMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="linear_create_comment",
                description="Create a comment on an issue.",
                inputSchema={
                    "type": "object",
                    "required": ["issue_id", "body"],
                    "properties": {
                        "issue_id": {
                            "type": "string",
                            "description": "The ID of the issue to comment on.",
                        },
                        "body": {
                            "type": "string",
                            "description": "The content of the comment in markdown format.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_COMMENT"}
                ),
            ),
            types.Tool(
                name="linear_update_comment",
                description="Update an existing comment.",
                inputSchema={
                    "type": "object",
                    "required": ["comment_id", "body"],
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "The ID of the comment to update.",
                        },
                        "body": {
                            "type": "string",
                            "description": "The new content of the comment in markdown format.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_COMMENT"}
                ),
            ),
            types.Tool(
                name="linear_search_issues",
                description="Search for issues by text query.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text to search for in issue titles.",
                        },
                        "team_id": {
                            "type": "string",
                            "description": "Optional team ID to limit search to specific team.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 20).",
                            "default": 20,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "LINEAR_ISSUE", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "linear_get_teams":
            try:
                result = await get_teams()
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

        elif name == "linear_get_issues":
            team_id = arguments.get("team_id")
            limit = arguments.get("limit", 10)
            filter_param = arguments.get("filter")
            try:
                result = await get_issues(team_id, limit, filter_param)
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
        
        elif name == "linear_get_issue_by_id":
            issue_id = arguments.get("issue_id")
            if not issue_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: issue_id parameter is required",
                    )
                ]
            try:
                result = await get_issue_by_id(issue_id)
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
        
        elif name == "linear_create_issue":
            team_id = arguments.get("team_id")
            title = arguments.get("title")
            if not team_id or not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: team_id and title parameters are required",
                    )
                ]
            
            description = arguments.get("description")
            assignee_id = arguments.get("assignee_id")
            priority = arguments.get("priority")
            state_id = arguments.get("state_id")
            project_id = arguments.get("project_id")
            
            try:
                result = await create_issue(team_id, title, description, assignee_id, priority, state_id, project_id)
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
        
        elif name == "linear_update_issue":
            issue_id = arguments.get("issue_id")
            if not issue_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: issue_id parameter is required",
                    )
                ]
            
            title = arguments.get("title")
            description = arguments.get("description")
            assignee_id = arguments.get("assignee_id")
            priority = arguments.get("priority")
            state_id = arguments.get("state_id")
            project_id = arguments.get("project_id")
            
            try:
                result = await update_issue(issue_id, title, description, assignee_id, priority, state_id, project_id)
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
        
        elif name == "linear_get_projects":
            team_id = arguments.get("team_id")
            limit = arguments.get("limit", 50)
            filter_param = arguments.get("filter")
            try:
                result = await get_projects(team_id, limit, filter_param)
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
        
        elif name == "linear_create_project":
            name = arguments.get("name")
            if not name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: name parameter is required",
                    )
                ]
            
            description = arguments.get("description")
            team_ids = arguments.get("team_ids")
            lead_id = arguments.get("lead_id")
            target_date = arguments.get("target_date")
            
            try:
                result = await create_project(name, description, team_ids, lead_id, target_date)
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
        
        elif name == "linear_update_project":
            project_id = arguments.get("project_id")
            if not project_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: project_id parameter is required",
                    )
                ]
            
            name = arguments.get("name")
            description = arguments.get("description")
            state = arguments.get("state")
            target_date = arguments.get("target_date")
            lead_id = arguments.get("lead_id")
            
            try:
                result = await update_project(project_id, name, description, state, target_date, lead_id)
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
        
        elif name == "linear_get_comments":
            issue_id = arguments.get("issue_id")
            if not issue_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: issue_id parameter is required",
                    )
                ]
            try:
                result = await get_comments(issue_id)
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
        
        elif name == "linear_create_comment":
            issue_id = arguments.get("issue_id")
            body = arguments.get("body")
            if not issue_id or not body:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: issue_id and body parameters are required",
                    )
                ]
            try:
                result = await create_comment(issue_id, body)
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
        
        elif name == "linear_update_comment":
            comment_id = arguments.get("comment_id")
            body = arguments.get("body")
            if not comment_id or not body:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: comment_id and body parameters are required",
                    )
                ]
            try:
                result = await update_comment(comment_id, body)
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
        
        elif name == "linear_search_issues":
            query_text = arguments.get("query")
            if not query_text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            team_id = arguments.get("team_id")
            limit = arguments.get("limit", 20)
            
            try:
                result = await search_issues(query_text, team_id, limit)
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