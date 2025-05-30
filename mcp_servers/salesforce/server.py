import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
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
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SALESFORCE_MCP_SERVER_PORT = int(os.getenv("SALESFORCE_MCP_SERVER_PORT", "5001"))

# Context variable to store the auth data for each request
auth_context: ContextVar[Dict[str, Any]] = ContextVar('auth_context')

def get_auth_context() -> Dict[str, Any]:
    """Get the authentication context from context."""
    try:
        return auth_context.get()
    except LookupError:
        raise RuntimeError("Authentication context not found in request context")

async def make_salesforce_graphql_request(instance_url: str, access_token: str, query: str, variables: Optional[Dict] = None, operation_name: Optional[str] = None) -> Dict[str, Any]:
    """Make a GraphQL request to Salesforce."""
    graphql_endpoint = f"{instance_url}/services/data/v60.0/graphql"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/graphql-response+json, application/json'
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    if operation_name:
        payload["operationName"] = operation_name
    
    async with aiohttp.ClientSession() as session:
        async with session.post(graphql_endpoint, json=payload, headers=headers) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise RuntimeError(f"Salesforce GraphQL API Error ({response.status}): {error_text}")
            
            result = await response.json()
            print(f"----- result: {result}")
            return result

async def search_records(object_type: str, search_term: str, fields: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    """Search for records using GraphQL query."""
    logger.info(f"Executing tool: search_records with object_type: {object_type}, search_term: {search_term}")
    
    try:
        auth_data = get_auth_context()
        instance_url = auth_data.get('instance_url')
        access_token = auth_data.get('access_token')
        
        if not instance_url or not access_token:
            raise RuntimeError("Missing instance_url or access_token in authentication context")
        
        # Default fields if none provided
        if not fields:
            fields = ["Id", "Name"] if object_type != "User" else ["Id", "Name", "Email"]
        
        fields_str = " ".join(fields)
        
        # Build GraphQL query for search
        query = f"""
        query SearchRecords($searchTerm: String!, $limit: Int!) {{
            uiapi {{
                query {{
                    {object_type}(
                        where: {{ Name: {{ like: $searchTerm }} }}
                        first: $limit
                    ) {{
                        edges {{
                            node {{
                                {fields_str}
                            }}
                        }}
                        totalCount
                    }}
                }}
            }}
        }}
        """
        
        variables = {
            "searchTerm": f"%{search_term}%",
            "limit": limit
        }
        
        result = await make_salesforce_graphql_request(instance_url, access_token, query, variables)
        return result
        
    except Exception as e:
        logger.exception(f"Error executing tool search_records: {e}")
        raise e

async def get_record_by_id(object_type: str, record_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific record by ID using GraphQL."""
    logger.info(f"Executing tool: get_record_by_id with object_type: {object_type}, record_id: {record_id}")
    
    try:
        auth_data = get_auth_context()
        instance_url = auth_data.get('instance_url')
        access_token = auth_data.get('access_token')
        
        if not instance_url or not access_token:
            raise RuntimeError("Missing instance_url or access_token in authentication context")
        
        # Default fields if none provided
        if not fields:
            if object_type == "Account":
                fields = ["Id", "Name", "Type", "Industry", "Website", "Phone"]
            elif object_type == "Contact":
                fields = ["Id", "FirstName", "LastName", "Email", "Phone", "AccountId"]
            elif object_type == "Lead":
                fields = ["Id", "FirstName", "LastName", "Company", "Email", "Phone", "Status"]
            elif object_type == "Opportunity":
                fields = ["Id", "Name", "Amount", "StageName", "CloseDate", "AccountId"]
            else:
                fields = ["Id", "Name"]
        
        fields_str = " ".join(fields)
        
        # Build GraphQL query for specific record
        query = f"""
        query GetRecord($recordId: ID!) {{
            uiapi {{
                query {{
                    {object_type}(where: {{ Id: {{ eq: $recordId }} }}) {{
                        edges {{
                            node {{
                                {fields_str}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        variables = {"recordId": record_id}
        
        result = await make_salesforce_graphql_request(instance_url, access_token, query, variables)
        return result
        
    except Exception as e:
        logger.exception(f"Error executing tool get_record_by_id: {e}")
        raise e

async def query_related_records(parent_object_type: str, parent_id: str, relationship_name: str, child_object_type: str, fields: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    """Query related records using GraphQL."""
    logger.info(f"Executing tool: query_related_records with parent: {parent_object_type}:{parent_id}, relationship: {relationship_name}")
    
    try:
        auth_data = get_auth_context()
        instance_url = auth_data.get('instance_url')
        access_token = auth_data.get('access_token')
        
        if not instance_url or not access_token:
            raise RuntimeError("Missing instance_url or access_token in authentication context")
        
        # Default fields if none provided
        if not fields:
            if child_object_type == "Contact":
                fields = ["Id", "FirstName", "LastName", "Email", "Phone"]
            elif child_object_type == "Opportunity":
                fields = ["Id", "Name", "Amount", "StageName", "CloseDate"]
            elif child_object_type == "Case":
                fields = ["Id", "Subject", "Status", "Priority", "CreatedDate"]
            else:
                fields = ["Id", "Name"]
        
        fields_str = " ".join(fields)
        
        # Build GraphQL query for related records
        query = f"""
        query GetRelatedRecords($parentId: ID!, $limit: Int!) {{
            uiapi {{
                query {{
                    {parent_object_type}(where: {{ Id: {{ eq: $parentId }} }}) {{
                        edges {{
                            node {{
                                Id
                                {relationship_name}(first: $limit) {{
                                    edges {{
                                        node {{
                                            {fields_str}
                                        }}
                                    }}
                                    totalCount
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        variables = {
            "parentId": parent_id,
            "limit": limit
        }
        
        result = await make_salesforce_graphql_request(instance_url, access_token, query, variables)
        return result
        
    except Exception as e:
        logger.exception(f"Error executing tool query_related_records: {e}")
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
                name="salesforce_search_records",
                description="Search for Salesforce records using GraphQL with flexible field selection.",
                inputSchema={
                    "type": "object",
                    "required": ["object_type", "search_term"],
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "The Salesforce object type to search (e.g., Account, Contact, Lead, Opportunity, Case).",
                        },
                        "search_term": {
                            "type": "string",
                            "description": "The search term to look for in the object's Name field.",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of fields to retrieve. Defaults to common fields for each object type.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return (default: 10).",
                            "default": 10,
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_get_record_by_id",
                description="Retrieve a specific Salesforce record by ID using GraphQL.",
                inputSchema={
                    "type": "object",
                    "required": ["object_type", "record_id"],
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "The Salesforce object type (e.g., Account, Contact, Lead, Opportunity, Case).",
                        },
                        "record_id": {
                            "type": "string",
                            "description": "The Salesforce record ID (18-character ID).",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of fields to retrieve. Defaults to common fields for each object type.",
                        },
                    },
                },
            ),
            types.Tool(
                name="salesforce_query_related_records",
                description="Query related records using GraphQL relationships (e.g., get Contacts for an Account).",
                inputSchema={
                    "type": "object",
                    "required": ["parent_object_type", "parent_id", "relationship_name", "child_object_type"],
                    "properties": {
                        "parent_object_type": {
                            "type": "string",
                            "description": "The parent object type (e.g., Account).",
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "The parent record ID.",
                        },
                        "relationship_name": {
                            "type": "string",
                            "description": "The relationship name (e.g., Contacts, Opportunities, Cases).",
                        },
                        "child_object_type": {
                            "type": "string",
                            "description": "The child object type (e.g., Contact, Opportunity, Case).",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of fields to retrieve from child records.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of related records to return (default: 10).",
                            "default": 10,
                        },
                    },
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:     
        if name == "salesforce_search_records":
            object_type = arguments.get("object_type")
            search_term = arguments.get("search_term")
            fields = arguments.get("fields")
            limit = arguments.get("limit", 10)
            
            if not object_type or not search_term:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: object_type and search_term parameters are required",
                    )
                ]
            
            try:
                result = await search_records(object_type, search_term, fields, limit)
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
        
        elif name == "salesforce_get_record_by_id":
            object_type = arguments.get("object_type")
            record_id = arguments.get("record_id")
            fields = arguments.get("fields")
            
            if not object_type or not record_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: object_type and record_id parameters are required",
                    )
                ]
            
            try:
                result = await get_record_by_id(object_type, record_id, fields)
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
        
        elif name == "salesforce_query_related_records":
            parent_object_type = arguments.get("parent_object_type")
            parent_id = arguments.get("parent_id")
            relationship_name = arguments.get("relationship_name")
            child_object_type = arguments.get("child_object_type")
            fields = arguments.get("fields")
            limit = arguments.get("limit", 10)
            
            if not all([parent_object_type, parent_id, relationship_name, child_object_type]):
                return [
                    types.TextContent(
                        type="text",
                        text="Error: parent_object_type, parent_id, relationship_name, and child_object_type parameters are required",
                    )
                ]
            
            try:
                result = await query_related_records(parent_object_type, parent_id, relationship_name, child_object_type, fields, limit)
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
        
        # Extract auth data from headers
        instance_url = request.headers.get('x-instance-url')
        access_token = request.headers.get('x-auth-token')
        
        if not instance_url or not access_token:
            logger.error('Error: Salesforce instance URL and access token are required. Provide them via x-instance-url and x-access-token headers.')
            return Response("Authentication required", status_code=401)
        
        # Set the auth context for this request
        auth_data = {"instance_url": instance_url, "access_token": access_token}
        token = auth_context.set(auth_data)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_context.reset(token)
        
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
        
        # Extract auth data from headers
        headers = dict(scope.get("headers", []))
        instance_url = headers.get(b'x-instance-url')
        access_token = headers.get(b'x-auth-token')
        
        if instance_url:
            instance_url = instance_url.decode('utf-8')
        if access_token:
            access_token = access_token.decode('utf-8')
        
        if not instance_url or not access_token:
            logger.error('Error: Salesforce instance URL and access token are required. Provide them via x-instance-url and x-access-token headers.')
            response = Response("Authentication required", status_code=401)
            await response(scope, receive, send)
            return
        
        # Set the auth context for this request
        auth_data = {"instance_url": instance_url, "access_token": access_token}
        token = auth_context.set(auth_data)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_context.reset(token)

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