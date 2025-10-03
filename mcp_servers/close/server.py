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

from tools.base import CloseToolExecutionError

# Import tools
from tools import leads as lead_tools
from tools import contacts as contact_tools
from tools import opportunities as opportunity_tools
from tools import tasks as task_tools
from tools import users as user_tools
from tools.base import auth_token_context

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

CLOSE_MCP_SERVER_PORT = int(os.getenv("CLOSE_MCP_SERVER_PORT", "5000"))

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
@click.option("--port", default=CLOSE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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

    app = Server("close-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Lead Management Tools
            types.Tool(
                name="close_create_lead",
                description="Create a new lead in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the lead/company",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the lead",
                        },
                        "status_id": {
                            "type": "string",
                            "description": "The ID of the lead status",
                        },
                        "url": {
                            "type": "string",
                            "description": "Website URL of the lead",
                        },
                        "contacts": {
                            "type": "array",
                            "description": "Array of contact objects to create with the lead",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "title": {"type": "string"},
                                    "emails": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "email": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        }
                                    },
                                    "phones": {
                                        "type": "array", 
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "phone": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "addresses": {
                            "type": "array",
                            "description": "Array of address objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "address_1": {"type": "string"},
                                    "address_2": {"type": "string"},
                                    "city": {"type": "string"},
                                    "state": {"type": "string"},
                                    "zipcode": {"type": "string"},
                                    "country": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["name"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD"}
                ),
            ),
            types.Tool(
                name="close_get_lead",
                description="Get a lead by its ID from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead to get",
                        },
                        "fields": {
                            "type": "string",
                            "description": "Comma-separated list of fields to return",
                        },
                    },
                    "required": ["lead_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_search_leads",
                description="Search for leads in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-200, default 25)",
                            "minimum": 1,
                            "maximum": 200,
                        },
                        "status_id": {
                            "type": "string",
                            "description": "Filter by lead status ID",
                        },
                    },
                    "required": ["query"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_update_lead",
                description="Update an existing lead in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the lead/company",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the lead",
                        },
                        "status_id": {
                            "type": "string",
                            "description": "The ID of the lead status",
                        },
                        "url": {
                            "type": "string",
                            "description": "Website URL of the lead",
                        },
                    },
                    "required": ["lead_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD"}
                ),
            ),
            types.Tool(
                name="close_delete_lead",
                description="Delete a lead from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead to delete",
                        },
                    },
                    "required": ["lead_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD"}
                ),
            ),
            types.Tool(
                name="close_list_leads",
                description="List leads from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-200, default 100)",
                            "minimum": 1,
                            "maximum": 200,
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination",
                            "minimum": 0,
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "status_id": {
                            "type": "string",
                            "description": "Filter by lead status ID",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_LEAD", "readOnlyHint": True}
                ),
            ),
            
            # Contact Management Tools
            types.Tool(
                name="close_create_contact",
                description="Create a new contact in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead this contact belongs to",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the contact",
                        },
                        "title": {
                            "type": "string",
                            "description": "Job title of the contact",
                        },
                        "emails": {
                            "type": "array",
                            "description": "Array of email objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                        "phones": {
                            "type": "array",
                            "description": "Array of phone objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "phone": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                    },
                    "required": ["lead_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_CONTACT"}
                ),
            ),
            types.Tool(
                name="close_get_contact",
                description="Get a contact by its ID from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "The ID of the contact to get",
                        },
                    },
                    "required": ["contact_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_CONTACT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_search_contacts",
                description="Search for contacts in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-200, default 25)",
                            "minimum": 1,
                            "maximum": 200,
                        },
                        "lead_id": {
                            "type": "string",
                            "description": "Filter by lead ID",
                        },
                    },
                    "required": ["query"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_CONTACT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_update_contact",
                description="Update an existing contact in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "The ID of the contact to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the contact",
                        },
                        "title": {
                            "type": "string",
                            "description": "Job title of the contact",
                        },
                        "emails": {
                            "type": "array",
                            "description": "Array of email objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                        "phones": {
                            "type": "array",
                            "description": "Array of phone objects",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "phone": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                    },
                    "required": ["contact_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_CONTACT"}
                ),
            ),
            types.Tool(
                name="close_delete_contact",
                description="Delete a contact from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "The ID of the contact to delete",
                        },
                    },
                    "required": ["contact_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_CONTACT"}
                ),
            ),
            
            # Opportunity Management Tools
            types.Tool(
                name="close_create_opportunity",
                description="Create a new opportunity in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead this opportunity belongs to",
                        },
                        "note": {
                            "type": "string",
                            "description": "Notes about the opportunity",
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "Confidence percentage (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "value": {
                            "type": "number",
                            "description": "Monetary value of the opportunity",
                        },
                        "value_period": {
                            "type": "string",
                            "description": "Value period (one_time, monthly, annual, etc.)",
                        },
                        "status_id": {
                            "type": "string",
                            "description": "The ID of the opportunity status",
                        },
                        "expected_date": {
                            "type": "string",
                            "description": "Expected close date (YYYY-MM-DD format)",
                        },
                    },
                    "required": ["lead_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_OPPORTUNITY"}
                ),
            ),
            types.Tool(
                name="close_get_opportunity",
                description="Get an opportunity by its ID from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "opportunity_id": {
                            "type": "string",
                            "description": "The ID of the opportunity to get",
                        },
                    },
                    "required": ["opportunity_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_OPPORTUNITY", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_update_opportunity",
                description="Update an existing opportunity in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "opportunity_id": {
                            "type": "string",
                            "description": "The ID of the opportunity to update",
                        },
                        "note": {
                            "type": "string",
                            "description": "Notes about the opportunity",
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "Confidence percentage (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "value": {
                            "type": "number",
                            "description": "Monetary value of the opportunity",
                        },
                        "value_period": {
                            "type": "string",
                            "description": "Value period (one_time, monthly, annual, etc.)",
                        },
                        "status_id": {
                            "type": "string",
                            "description": "The ID of the opportunity status",
                        },
                        "expected_date": {
                            "type": "string",
                            "description": "Expected close date (YYYY-MM-DD format)",
                        },
                    },
                    "required": ["opportunity_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_OPPORTUNITY"}
                ),
            ),
            types.Tool(
                name="close_delete_opportunity",
                description="Delete an opportunity from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "opportunity_id": {
                            "type": "string",
                            "description": "The ID of the opportunity to delete",
                        },
                    },
                    "required": ["opportunity_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_OPPORTUNITY"}
                ),
            ),
            
            # Task Management Tools
            types.Tool(
                name="close_create_task",
                description="Create a new task in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "lead_id": {
                            "type": "string",
                            "description": "The ID of the lead this task belongs to",
                        },
                        "text": {
                            "type": "string",
                            "description": "Task description/text",
                        },
                        "assigned_to": {
                            "type": "string",
                            "description": "User ID to assign the task to",
                        },
                        "date": {
                            "type": "string",
                            "description": "Due date for the task (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format)",
                        },
                        "is_complete": {
                            "type": "boolean",
                            "description": "Whether the task is complete",
                        },
                    },
                    "required": ["lead_id", "text"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_TASK"}
                ),
            ),
            types.Tool(
                name="close_get_task",
                description="Get a task by its ID from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to get",
                        },
                    },
                    "required": ["task_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_TASK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_update_task",
                description="Update an existing task in Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to update",
                        },
                        "text": {
                            "type": "string",
                            "description": "Task description/text",
                        },
                        "assigned_to": {
                            "type": "string",
                            "description": "User ID to assign the task to",
                        },
                        "date": {
                            "type": "string",
                            "description": "Due date for the task (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format)",
                        },
                        "is_complete": {
                            "type": "boolean",
                            "description": "Whether the task is complete",
                        },
                    },
                    "required": ["task_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_TASK"}
                ),
            ),
            types.Tool(
                name="close_delete_task",
                description="Delete a task from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to delete",
                        },
                    },
                    "required": ["task_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_TASK"}
                ),
            ),
            types.Tool(
                name="close_list_tasks",
                description="List tasks from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-200, default 100)",
                            "minimum": 1,
                            "maximum": 200,
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination",
                            "minimum": 0,
                        },
                        "lead_id": {
                            "type": "string",
                            "description": "Filter by lead ID",
                        },
                        "assigned_to": {
                            "type": "string",
                            "description": "Filter by assigned user ID",
                        },
                        "is_complete": {
                            "type": "boolean",
                            "description": "Filter by completion status",
                        },
                        "task_type": {
                            "type": "string",
                            "description": "Filter by task type (lead, incoming_email, etc.)",
                        },
                        "view": {
                            "type": "string",
                            "description": "View filter (inbox, future, archive)",
                            "enum": ["inbox", "future", "archive"]
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_TASK", "readOnlyHint": True}
                ),
            ),
            
            # User Management Tools
            types.Tool(
                name="close_get_current_user",
                description="Get information about the current user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_USER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_list_users",
                description="List users from Close CRM",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (1-200, default 100)",
                            "minimum": 1,
                            "maximum": 200,
                        },
                        "skip": {
                            "type": "integer",
                            "description": "Number of results to skip for pagination",
                            "minimum": 0,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_USER", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="close_get_user",
                description="Get a user by their ID from Close CRM",
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
                annotations=types.ToolAnnotations(
                    **{"category": "CLOSE_USER", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        try:
            if name == "close_create_lead":
                result = await lead_tools.create_lead(**arguments)
            elif name == "close_get_lead":
                result = await lead_tools.get_lead(**arguments)
            elif name == "close_search_leads":
                result = await lead_tools.search_leads(**arguments)
            elif name == "close_update_lead":
                result = await lead_tools.update_lead(**arguments)
            elif name == "close_delete_lead":
                result = await lead_tools.delete_lead(**arguments)
            elif name == "close_list_leads":
                result = await lead_tools.list_leads(**arguments)
            
            elif name == "close_create_contact":
                result = await contact_tools.create_contact(**arguments)
            elif name == "close_get_contact":
                result = await contact_tools.get_contact(**arguments)
            elif name == "close_search_contacts":
                result = await contact_tools.search_contacts(**arguments)
            elif name == "close_update_contact":
                result = await contact_tools.update_contact(**arguments)
            elif name == "close_delete_contact":
                result = await contact_tools.delete_contact(**arguments)
            
            elif name == "close_create_opportunity":
                result = await opportunity_tools.create_opportunity(**arguments)
            elif name == "close_get_opportunity":
                result = await opportunity_tools.get_opportunity(**arguments)
            elif name == "close_update_opportunity":
                result = await opportunity_tools.update_opportunity(**arguments)
            elif name == "close_delete_opportunity":
                result = await opportunity_tools.delete_opportunity(**arguments)
                
            elif name == "close_create_task":
                result = await task_tools.create_task(**arguments)
            elif name == "close_get_task":
                result = await task_tools.get_task(**arguments)
            elif name == "close_update_task":
                result = await task_tools.update_task(**arguments)
            elif name == "close_delete_task":
                result = await task_tools.delete_task(**arguments)
            elif name == "close_list_tasks":
                result = await task_tools.list_tasks(**arguments)
                
            elif name == "close_get_current_user":
                result = await user_tools.get_current_user()
            elif name == "close_list_users":
                result = await user_tools.list_users(**arguments)
            elif name == "close_get_user":
                result = await user_tools.get_user(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except CloseToolExecutionError as e:
            logger.error(f"Close CRM error in {name}: {e}")
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