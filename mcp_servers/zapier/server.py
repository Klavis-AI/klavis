#!/usr/bin/env python3
"""
Zapier MCP Server - Standard Python MCP Server Format.

This server implements the Model Context Protocol (MCP) for Zapier
following the standard format used by other Python MCP servers.
"""

import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict
from contextvars import ContextVar

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
    list_workflows,
    get_workflow,
    create_workflow,
    update_workflow,
    delete_workflow,
    trigger_workflow,
    list_tasks,
    get_task,
    list_webhooks,
    create_webhook,
    get_webhook,
    list_apps,
    get_app,
    connect_app,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

ZAPIER_MCP_SERVER_PORT = int(os.getenv("ZAPIER_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option(
    "--port", default=ZAPIER_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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
    app = Server("zapier-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="zapier_list_workflows",
                description="List all workflows in your Zapier account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of workflows to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of workflows to skip for pagination",
                            "default": 0,
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_get_workflow",
                description="Get details of a specific workflow",
                inputSchema={
                    "type": "object",
                    "required": ["workflow_id"],
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The ID of the workflow to retrieve",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_create_workflow",
                description="Create a new workflow in Zapier",
                inputSchema={
                    "type": "object",
                    "required": ["name", "description"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the workflow",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the workflow",
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of workflow steps",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_update_workflow",
                description="Update an existing workflow",
                inputSchema={
                    "type": "object",
                    "required": ["workflow_id"],
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The ID of the workflow to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the workflow",
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the workflow",
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Updated array of workflow steps",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_delete_workflow",
                description="Delete a workflow",
                inputSchema={
                    "type": "object",
                    "required": ["workflow_id"],
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The ID of the workflow to delete",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_trigger_workflow",
                description="Trigger a workflow manually",
                inputSchema={
                    "type": "object",
                    "required": ["workflow_id"],
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The ID of the workflow to trigger",
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to pass to the workflow trigger",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_list_tasks",
                description="List tasks for a workflow",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Optional workflow ID to filter tasks",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of tasks to skip for pagination",
                            "default": 0,
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_get_task",
                description="Get details of a specific task",
                inputSchema={
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to retrieve",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_list_webhooks",
                description="List webhooks in your Zapier account",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of webhooks to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of webhooks to skip for pagination",
                            "default": 0,
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_create_webhook",
                description="Create a new webhook",
                inputSchema={
                    "type": "object",
                    "required": ["name", "url"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the webhook",
                        },
                        "url": {
                            "type": "string",
                            "description": "URL for the webhook endpoint",
                        },
                        "events": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of events to listen for",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_get_webhook",
                description="Get details of a specific webhook",
                inputSchema={
                    "type": "object",
                    "required": ["webhook_id"],
                    "properties": {
                        "webhook_id": {
                            "type": "string",
                            "description": "The ID of the webhook to retrieve",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_list_apps",
                description="List available apps in Zapier",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of apps to return (default: 50)",
                            "default": 50,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of apps to skip for pagination",
                            "default": 0,
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_get_app",
                description="Get details of a specific app",
                inputSchema={
                    "type": "object",
                    "required": ["app_id"],
                    "properties": {
                        "app_id": {
                            "type": "string",
                            "description": "The ID of the app to retrieve",
                        },
                    },
                },
            ),
            types.Tool(
                name="zapier_connect_app",
                description="Connect an app to your Zapier account",
                inputSchema={
                    "type": "object",
                    "required": ["app_id"],
                    "properties": {
                        "app_id": {
                            "type": "string",
                            "description": "The ID of the app to connect",
                        },
                        "auth_data": {
                            "type": "object",
                            "description": "Authentication data for the app",
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # Log the tool call with name and arguments
        logger.info(f"Tool called: {name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
        
        if name == "zapier_list_workflows":
            try:
                result = await list_workflows(
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
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
        elif name == "zapier_get_workflow":
            try:
                result = await get_workflow(workflow_id=arguments.get("workflow_id"))
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
        elif name == "zapier_create_workflow":
            try:
                result = await create_workflow(
                    name=arguments.get("name"),
                    description=arguments.get("description"),
                    steps=arguments.get("steps"),
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
        elif name == "zapier_update_workflow":
            try:
                result = await update_workflow(
                    workflow_id=arguments.get("workflow_id"),
                    name=arguments.get("name"),
                    description=arguments.get("description"),
                    steps=arguments.get("steps"),
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
        elif name == "zapier_delete_workflow":
            try:
                result = await delete_workflow(workflow_id=arguments.get("workflow_id"))
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
        elif name == "zapier_trigger_workflow":
            try:
                result = await trigger_workflow(
                    workflow_id=arguments.get("workflow_id"),
                    data=arguments.get("data"),
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
        elif name == "zapier_list_tasks":
            try:
                result = await list_tasks(
                    workflow_id=arguments.get("workflow_id"),
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
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
        elif name == "zapier_get_task":
            try:
                result = await get_task(task_id=arguments.get("task_id"))
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
        elif name == "zapier_list_webhooks":
            try:
                result = await list_webhooks(
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
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
        elif name == "zapier_create_webhook":
            try:
                result = await create_webhook(
                    name=arguments.get("name"),
                    url=arguments.get("url"),
                    events=arguments.get("events"),
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
        elif name == "zapier_get_webhook":
            try:
                result = await get_webhook(webhook_id=arguments.get("webhook_id"))
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
        elif name == "zapier_list_apps":
            try:
                result = await list_apps(
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
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
        elif name == "zapier_get_app":
            try:
                result = await get_app(app_id=arguments.get("app_id"))
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
        elif name == "zapier_connect_app":
            try:
                result = await connect_app(
                    app_id=arguments.get("app_id"),
                    auth_data=arguments.get("auth_data"),
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
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = request.headers.get('x-auth-token')
        
        # Set the auth token in context for this request (can be None)
        token = auth_token_context.set(auth_token or "")
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
        
        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        if auth_token:
            auth_token = auth_token.decode('utf-8')
        
        # Set the auth token in context for this request (can be None/empty)
        token = auth_token_context.set(auth_token or "")
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