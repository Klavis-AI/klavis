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
    auth_token_context, auth_email_context,
    get_current_user,
    list_tickets, get_ticket, create_ticket, update_ticket, delete_ticket,
    add_ticket_comment, get_ticket_comments, assign_ticket, change_ticket_status, search_tickets,
    list_users, get_user, create_user, update_user, delete_user, search_users,
    get_user_tickets, get_user_organizations, suspend_user, reactivate_user,
    list_organizations, get_organization, create_organization, update_organization,
    delete_organization, search_organizations, get_organization_tickets, get_organization_users
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

ZENDESK_MCP_SERVER_PORT = int(os.getenv("ZENDESK_MCP_SERVER_PORT", "5000"))

@click.command()
@click.option("--port", default=ZENDESK_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    # Create the MCP server instance
    app = Server("zendesk-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Authentication
            types.Tool(
                name="zendesk_get_current_user",
                description="Get current user information from Zendesk.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            
            # Tickets
            types.Tool(
                name="zendesk_list_tickets",
                description="List tickets with optional filtering and pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (1 or greater).",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of tickets per page (1-100).",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by ticket status (new, open, pending, hold, solved, closed).",
                        },
                        "assignee_id": {
                            "type": "integer",
                            "description": "Filter by assignee ID.",
                        },
                        "requester_id": {
                            "type": "integer",
                            "description": "Filter by requester ID.",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "Filter by organization ID.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_ticket",
                description="Get a single ticket by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_create_ticket",
                description="Create a new ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["subject", "description"],
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "The subject of the ticket.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the ticket.",
                        },
                        "requester_id": {
                            "type": "integer",
                            "description": "The ID of the user requesting the ticket.",
                        },
                        "assignee_id": {
                            "type": "integer",
                            "description": "The ID of the user assigned to the ticket.",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization for the ticket.",
                        },
                        "priority": {
                            "type": "string",
                            "description": "The priority of the ticket (urgent, high, normal, low).",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for the ticket.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_update_ticket",
                description="Update an existing ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket to update.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "The new subject of the ticket.",
                        },
                        "description": {
                            "type": "string",
                            "description": "The new description of the ticket.",
                        },
                        "assignee_id": {
                            "type": "integer",
                            "description": "The new assignee ID.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The new status (new, open, pending, hold, solved, closed).",
                        },
                        "priority": {
                            "type": "string",
                            "description": "The new priority (urgent, high, normal, low).",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The new tags for the ticket.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_delete_ticket",
                description="Delete a ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket to delete.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_add_ticket_comment",
                description="Add a comment to a ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id", "comment_body"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket.",
                        },
                        "comment_body": {
                            "type": "string",
                            "description": "The comment text to add.",
                        },
                        "public": {
                            "type": "boolean",
                            "description": "Whether the comment is public (default: true).",
                        },
                        "author_id": {
                            "type": "integer",
                            "description": "The ID of the comment author.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_ticket_comments",
                description="Get comments for a specific ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of comments per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_assign_ticket",
                description="Assign a ticket to a specific agent.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id", "assignee_id"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket.",
                        },
                        "assignee_id": {
                            "type": "integer",
                            "description": "The ID of the user to assign the ticket to.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_change_ticket_status",
                description="Change the status of a ticket.",
                inputSchema={
                    "type": "object",
                    "required": ["ticket_id", "status"],
                    "properties": {
                        "ticket_id": {
                            "type": "integer",
                            "description": "The ID of the ticket.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The new status (new, open, pending, hold, solved, closed).",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_search_tickets",
                description="Search tickets using Zendesk search syntax.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query in Zendesk search syntax.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page.",
                        },
                    },
                },
            ),
            
            # Users
            types.Tool(
                name="zendesk_list_users",
                description="List users with optional filtering and pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of users per page.",
                        },
                        "role": {
                            "type": "string",
                            "description": "Filter by user role (end-user, agent, admin).",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "Filter by organization ID.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_user",
                description="Get a single user by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_create_user",
                description="Create a new user.",
                inputSchema={
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the user.",
                        },
                        "email": {
                            "type": "string",
                            "description": "The email address of the user.",
                        },
                        "role": {
                            "type": "string",
                            "description": "The role of the user (end-user, agent, admin).",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization for the user.",
                        },
                        "phone": {
                            "type": "string",
                            "description": "The phone number of the user.",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for the user.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_update_user",
                description="Update an existing user.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the user.",
                        },
                        "email": {
                            "type": "string",
                            "description": "The new email address of the user.",
                        },
                        "role": {
                            "type": "string",
                            "description": "The new role of the user.",
                        },
                        "organization_id": {
                            "type": "integer",
                            "description": "The new organization ID for the user.",
                        },
                        "phone": {
                            "type": "string",
                            "description": "The new phone number of the user.",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The new tags for the user.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_delete_user",
                description="Delete a user.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user to delete.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_search_users",
                description="Search users using Zendesk search syntax.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query in Zendesk search syntax.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_user_tickets",
                description="Get tickets requested by a specific user.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of tickets per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_user_organizations",
                description="Get organizations associated with a user.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_suspend_user",
                description="Suspend a user account.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user to suspend.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_reactivate_user",
                description="Reactivate a suspended user account.",
                inputSchema={
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user to reactivate.",
                        },
                    },
                },
            ),
            
            # Organizations
            types.Tool(
                name="zendesk_list_organizations",
                description="List organizations with pagination.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of organizations per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_organization",
                description="Get a single organization by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to retrieve.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_create_organization",
                description="Create a new organization.",
                inputSchema={
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the organization.",
                        },
                        "domain": {
                            "type": "string",
                            "description": "The domain of the organization.",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for the organization.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_update_organization",
                description="Update an existing organization.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to update.",
                        },
                        "name": {
                            "type": "string",
                            "description": "The new name of the organization.",
                        },
                        "domain": {
                            "type": "string",
                            "description": "The new domain of the organization.",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "The new tags for the organization.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_delete_organization",
                description="Delete an organization.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization to delete.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_search_organizations",
                description="Search organizations using Zendesk search syntax.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query in Zendesk search syntax.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of results per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_organization_tickets",
                description="Get tickets for a specific organization.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of tickets per page.",
                        },
                    },
                },
            ),
            types.Tool(
                name="zendesk_get_organization_users",
                description="Get users for a specific organization.",
                inputSchema={
                    "type": "object",
                    "required": ["organization_id"],
                    "properties": {
                        "organization_id": {
                            "type": "integer",
                            "description": "The ID of the organization.",
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination.",
                        },
                        "per_page": {
                            "type": "integer",
                            "description": "Number of users per page.",
                        },
                    },
                },
            ),
            

        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        try:
            # Authentication
            if name == "zendesk_get_current_user":
                result = await get_current_user()
            
            # Tickets
            elif name == "zendesk_list_tickets":
                result = await list_tickets(**arguments)
            elif name == "zendesk_get_ticket":
                result = await get_ticket(**arguments)
            elif name == "zendesk_create_ticket":
                result = await create_ticket(**arguments)
            elif name == "zendesk_update_ticket":
                result = await update_ticket(**arguments)
            elif name == "zendesk_delete_ticket":
                result = await delete_ticket(**arguments)
            elif name == "zendesk_add_ticket_comment":
                result = await add_ticket_comment(**arguments)
            elif name == "zendesk_get_ticket_comments":
                result = await get_ticket_comments(**arguments)
            elif name == "zendesk_assign_ticket":
                result = await assign_ticket(**arguments)
            elif name == "zendesk_change_ticket_status":
                result = await change_ticket_status(**arguments)
            elif name == "zendesk_search_tickets":
                result = await search_tickets(**arguments)
            
            # Users
            elif name == "zendesk_list_users":
                result = await list_users(**arguments)
            elif name == "zendesk_get_user":
                result = await get_user(**arguments)
            elif name == "zendesk_create_user":
                result = await create_user(**arguments)
            elif name == "zendesk_update_user":
                result = await update_user(**arguments)
            elif name == "zendesk_delete_user":
                result = await delete_user(**arguments)
            elif name == "zendesk_search_users":
                result = await search_users(**arguments)
            elif name == "zendesk_get_user_tickets":
                result = await get_user_tickets(**arguments)
            elif name == "zendesk_get_user_organizations":
                result = await get_user_organizations(**arguments)
            elif name == "zendesk_suspend_user":
                result = await suspend_user(**arguments)
            elif name == "zendesk_reactivate_user":
                result = await reactivate_user(**arguments)
            
            # Organizations
            elif name == "zendesk_list_organizations":
                result = await list_organizations(**arguments)
            elif name == "zendesk_get_organization":
                result = await get_organization(**arguments)
            elif name == "zendesk_create_organization":
                result = await create_organization(**arguments)
            elif name == "zendesk_update_organization":
                result = await update_organization(**arguments)
            elif name == "zendesk_delete_organization":
                result = await delete_organization(**arguments)
            elif name == "zendesk_search_organizations":
                result = await search_organizations(**arguments)
            elif name == "zendesk_get_organization_tickets":
                result = await get_organization_tickets(**arguments)
            elif name == "zendesk_get_organization_users":
                result = await get_organization_users(**arguments)

            
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error in {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token and email from headers (fallback to environment)
        auth_token = request.headers.get('x-auth-token')
        auth_email = request.headers.get('x-auth-email')
        
        if not auth_token:
            auth_token = os.getenv("ZENDESK_API_TOKEN")
            logger.info("SSE: Using authentication from environment variables (ZENDESK_API_TOKEN)")
        else:
            logger.info("SSE: Using authentication from HTTP headers")
            
        if not auth_email:
            auth_email = os.getenv("ZENDESK_EMAIL")
            logger.info("SSE: Using authentication from environment variables (ZENDESK_EMAIL)")
        else:
            logger.info("SSE: Using authentication from HTTP headers")
        
        # Set the auth credentials in context for this request
        token = auth_token_context.set(auth_token or "")
        email = auth_email_context.set(auth_email or "")
        
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
            auth_email_context.reset(email)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token and email from headers (fallback to environment)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b'x-auth-token')
        auth_email = headers.get(b'x-auth-email')
        
        if auth_token:
            auth_token = auth_token.decode('utf-8')
            logger.info("Using authentication from HTTP headers")
        else:
            auth_token = os.getenv("ZENDESK_API_TOKEN")
            logger.info("Using authentication from environment variables (ZENDESK_API_TOKEN)")
        
        if auth_email:
            auth_email = auth_email.decode('utf-8')
            logger.info("Using authentication from HTTP headers")
        else:
            auth_email = os.getenv("ZENDESK_EMAIL")
            logger.info("Using authentication from environment variables (ZENDESK_EMAIL)")
        
        # Set the auth credentials in context for this request
        token = auth_token_context.set(auth_token or "")
        email = auth_email_context.set(auth_email or "")
        
        logger.info(f"Context set - Token: {'*' * (len(auth_token) - 4) + auth_token[-4:] if auth_token else 'None'}, Email: {auth_email}")
        logger.info(f"Context variables - auth_token_context: {auth_token_context.get()}, auth_email_context: {auth_email_context.get()}")
        
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)
            auth_email_context.reset(email)

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
