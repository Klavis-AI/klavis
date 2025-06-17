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
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceError

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

SALESFORCE_MCP_SERVER_PORT = int(os.getenv("SALESFORCE_MCP_SERVER_PORT", "5000"))

# Context variables to store the access token and instance URL for each request
access_token_context: ContextVar[str] = ContextVar('access_token')
instance_url_context: ContextVar[str] = ContextVar('instance_url')

def get_salesforce_connection(access_token: str, instance_url: str) -> Salesforce:
    """Create Salesforce connection with access token."""
    return Salesforce(instance_url=instance_url, session_id=access_token)

def get_salesforce_conn() -> Salesforce:
    """Get the Salesforce connection from context - created fresh each time."""
    try:
        access_token = access_token_context.get()
        instance_url = instance_url_context.get()
        
        if not access_token or not instance_url:
            raise RuntimeError("Salesforce access token and instance URL are required. Provide them via x-auth-token and x-instance-url headers.")
        
        return get_salesforce_connection(access_token, instance_url)
    except LookupError:
        raise RuntimeError("Salesforce credentials not found in request context")

async def execute_soql_query(query: str) -> Dict[str, Any]:
    """Execute a SOQL query on Salesforce."""
    logger.info(f"Executing tool: execute_soql_query with query: {query}")
    try:
        sf = get_salesforce_conn()
        result = sf.query(query)
        return dict(result)
    except SalesforceError as e:
        logger.error(f"Salesforce API error: {e}")
        raise RuntimeError(f"Salesforce API Error: {str(e)}")
    except Exception as e:
        logger.exception(f"Error executing SOQL query: {e}")
        raise e

async def execute_tooling_query(query: str) -> Dict[str, Any]:
    """Execute a query against the Salesforce Tooling API."""
    logger.info(f"Executing tool: execute_tooling_query with query: {query}")
    try:
        sf = get_salesforce_conn()
        result = sf.toolingexecute(f"query/?q={query}")
        return dict(result)
    except SalesforceError as e:
        logger.error(f"Salesforce Tooling API error: {e}")
        raise RuntimeError(f"Salesforce Tooling API Error: {str(e)}")
    except Exception as e:
        logger.exception(f"Error executing tooling query: {e}")
        raise e

async def describe_object(object_name: str, detailed: bool = False) -> Dict[str, Any]:
    """Get detailed metadata about a Salesforce object."""
    logger.info(f"Executing tool: describe_object with object_name: {object_name}")
    try:
        sf = get_salesforce_conn()
        sobject = getattr(sf, object_name)
        result = sobject.describe()
        
        if detailed and object_name.endswith('__c'):
            # For custom objects, get additional metadata if requested
            metadata_result = sf.restful(f"sobjects/{object_name}/describe/")
            return {
                "describe": dict(result),
                "metadata": metadata_result
            }
        
        return dict(result)
    except SalesforceError as e:
        logger.error(f"Salesforce API error: {e}")
        raise RuntimeError(f"Salesforce API Error: {str(e)}")
    except Exception as e:
        logger.exception(f"Error describing object: {e}")
        raise e

async def create_record(object_type: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new record in Salesforce for any object type."""
    logger.info(f"Executing tool: create_record with object_type: {object_type}")
    try:
        sf = get_salesforce_conn()
        
        # Get the SObject type dynamically
        sobject = getattr(sf, object_type)
        
        # Create the record
        result = sobject.create(record_data)
        
        if result.get('success'):
            return {
                "success": True,
                "id": result.get('id'),
                "message": f"{object_type} record created successfully",
                "created_record": {
                    "id": result.get('id'),
                    "object_type": object_type,
                    "data": record_data
                }
            }
        else:
            return {
                "success": False,
                "errors": result.get('errors', []),
                "message": f"Failed to create {object_type} record"
            }
            
    except SalesforceError as e:
        logger.error(f"Salesforce API error: {e}")
        error_msg = str(e)
        # Try to extract more meaningful error information
        if hasattr(e, 'content') and e.content:
            try:
                error_content = json.loads(e.content[0]['message']) if isinstance(e.content, list) else e.content
                if isinstance(error_content, dict) and 'message' in error_content:
                    error_msg = error_content['message']
            except:
                pass
        return {
            "success": False,
            "error": f"Salesforce API Error: {error_msg}",
            "message": f"Failed to create {object_type} record"
        }
    except AttributeError as e:
        logger.error(f"Invalid object type: {object_type}")
        return {
            "success": False,
            "error": f"Invalid object type: {object_type}. Please check the object API name.",
            "message": f"Object type '{object_type}' not found"
        }
    except Exception as e:
        logger.exception(f"Error creating record: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create {object_type} record"
        }

async def retrieve_metadata(metadata_type: str, full_names: list) -> Dict[str, Any]:
    """Retrieve metadata components from Salesforce."""
    logger.info(f"Executing tool: retrieve_metadata with type: {metadata_type}")
    try:
        sf = get_salesforce_conn()
        
        # Valid metadata types
        valid_types = [
            'CustomObject', 'Flow', 'FlowDefinition', 'CustomField',
            'ValidationRule', 'ApexClass', 'ApexTrigger', 'WorkflowRule', 'Layout'
        ]
        
        if metadata_type not in valid_types:
            raise ValueError(f"Invalid metadata type: {metadata_type}")
        
        # Use Tooling API for metadata queries
        results = []
        for name in full_names:
            try:
                if metadata_type == 'ApexClass':
                    query = f"SELECT Id, Name, Body FROM ApexClass WHERE Name = '{name}'"
                elif metadata_type == 'ApexTrigger':
                    query = f"SELECT Id, Name, Body FROM ApexTrigger WHERE Name = '{name}'"
                elif metadata_type == 'Flow':
                    query = f"SELECT Id, MasterLabel, Definition FROM Flow WHERE MasterLabel = '{name}'"
                else:
                    # For other types, use general metadata query
                    query = f"SELECT Id, DeveloperName FROM {metadata_type} WHERE DeveloperName = '{name}'"
                
                result = sf.toolingexecute(f"query/?q={query}")
                results.append({
                    "name": name,
                    "type": metadata_type,
                    "data": dict(result)
                })
            except Exception as e:
                results.append({
                    "name": name,
                    "type": metadata_type,
                    "error": str(e)
                })
        
        return {"results": results}
    except SalesforceError as e:
        logger.error(f"Salesforce API error: {e}")
        raise RuntimeError(f"Salesforce API Error: {str(e)}")
    except Exception as e:
        logger.exception(f"Error retrieving metadata: {e}")
        raise e

@click.command()
@click.option("--port", default=SALESFORCE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("salesforce-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="salesforce_query",
                description="Execute a SOQL query on Salesforce",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SOQL query to execute",
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_tooling_query",
                description="Execute a query against the Salesforce Tooling API",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Tooling API query to execute",
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_describe_object",
                description="Get detailed schema and field information for any Salesforce object (standard or custom). Returns field types, relationships, permissions, and object properties.",
                inputSchema={
                    "type": "object",
                    "required": ["object_name"],
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "API name of the object to describe (e.g., 'Account', 'Contact', 'MyCustomObject__c')",
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Whether to return additional metadata for custom objects (optional)",
                            "default": False,
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_get_component_source",
                description="Retrieve the actual source code and definitions of Salesforce components like Apex classes, triggers, flows, and other metadata. This gets the implementation details, not just schema.",
                inputSchema={
                    "type": "object",
                    "required": ["metadata_type", "component_names"],
                    "properties": {
                        "metadata_type": {
                            "type": "string",
                            "description": "Type of component to retrieve (e.g., 'ApexClass' for classes, 'ApexTrigger' for triggers, 'Flow' for flows)",
                            "enum": [
                                "CustomObject",
                                "Flow",
                                "FlowDefinition",
                                "CustomField",
                                "ValidationRule",
                                "ApexClass",
                                "ApexTrigger",
                                "WorkflowRule",
                                "Layout"
                            ],
                        },
                        "component_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Array of component names to retrieve (e.g., ['AccountTrigger', 'ContactUtils'] for Apex components)",
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_create_record",
                description="Create a new record in Salesforce for any object type (Lead, Contact, Account, Opportunity, Task, Event, Case, Campaign, etc.). This tool handles all standard and custom objects.",
                inputSchema={
                    "type": "object",
                    "required": ["object_type", "record_data"],
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "API name of the Salesforce object type to create (e.g., 'Lead', 'Contact', 'Account', 'Opportunity', 'Task', 'Event', 'Case', 'Campaign', 'MyCustomObject__c')",
                        },
                        "record_data": {
                            "type": "object",
                            "description": "Field values for the new record as key-value pairs. Required fields vary by object type. Common examples: Lead needs LastName and Company; Contact needs LastName; Account needs Name; Opportunity needs Name, StageName, and CloseDate.",
                            "additionalProperties": True,
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:     
        if name == "salesforce_query":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await execute_soql_query(query)
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
        
        elif name == "salesforce_tooling_query":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await execute_tooling_query(query)
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
        
        elif name == "salesforce_describe_object":
            object_name = arguments.get("object_name")
            detailed = arguments.get("detailed", False)
            if not object_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: object_name parameter is required",
                    )
                ]
            
            try:
                result = await describe_object(object_name, detailed)
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
        
        elif name == "salesforce_get_component_source":
            metadata_type = arguments.get("metadata_type")
            component_names = arguments.get("component_names")
            if not metadata_type or not component_names:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: metadata_type and component_names parameters are required",
                    )
                ]
            
            try:
                result = await retrieve_metadata(metadata_type, component_names)
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
        
        elif name == "salesforce_create_record":
            object_type = arguments.get("object_type")
            record_data = arguments.get("record_data")
            if not object_type or not record_data:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: object_type and record_data parameters are required",
                    )
                ]
            
            try:
                result = await create_record(object_type, record_data)
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
        
        # Extract auth credentials from headers (allow None - will be handled at tool level)
        access_token = request.headers.get('x-auth-token')
        instance_url = request.headers.get('x-instance-url')
        
        # Set the access token and instance URL in context for this request (can be None)
        access_token_token = access_token_context.set(access_token or "")
        instance_url_token = instance_url_context.set(instance_url or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            access_token_context.reset(access_token_token)
            instance_url_context.reset(instance_url_token)
        
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
        
        # Extract auth credentials from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        access_token = headers.get(b'x-auth-token')
        instance_url = headers.get(b'x-instance-url')
        
        if access_token:
            access_token = access_token.decode('utf-8')
        if instance_url:
            instance_url = instance_url.decode('utf-8')
        
        # Set the access token and instance URL in context for this request (can be None/empty)
        access_token_token = access_token_context.set(access_token or "")
        instance_url_token = instance_url_context.set(instance_url or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            access_token_context.reset(access_token_token)
            instance_url_context.reset(instance_url_token)

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