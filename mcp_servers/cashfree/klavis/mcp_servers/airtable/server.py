import contextlib
import base64
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
    create_field,
    create_records,
    create_table,
    delete_records,
    get_bases_info,
    get_record,
    get_tables_info,
    list_records,
    update_field,
    update_records,
    update_table,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

AIRTABLE_MCP_SERVER_PORT = int(os.getenv("AIRTABLE_MCP_SERVER_PORT", "5000"))

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
@click.option(
    "--port", default=AIRTABLE_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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
    app = Server("airtable-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="airtable_list_bases_info",
                description="Get information about all bases",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_BASE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="airtable_list_tables_info",
                description="Get information about all tables in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base to get tables from",
                        },
                    },
                    "required": ["base_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_TABLE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="airtable_create_table",
                description="Create a new table in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base to create the table in",
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the new table",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the table",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of field objects to create in the table",
                        },
                    },
                    "required": ["base_id", "name", "fields"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_TABLE"}
                ),
            ),
            types.Tool(
                name="airtable_update_table",
                description="Update an existing table in a base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional new name for the table",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional new description for the table",
                        },
                    },
                    "required": ["base_id", "table_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_TABLE"}
                ),
            ),
            types.Tool(
                name="airtable_create_field",
                description="Create a new field in a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table to create the field in",
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the new field",
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of the field (e.g., 'singleLineText', 'number', 'singleSelect', etc.)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the field",
                        },
                        "options": {
                            "type": "object",
                            "description": "Optional field configuration options specific to the field type",
                        },
                    },
                    "required": ["base_id", "table_id", "name", "type"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_FIELD"}
                ),
            ),
            types.Tool(
                name="airtable_update_field",
                description="Update an existing field in a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table containing the field",
                        },
                        "field_id": {
                            "type": "string",
                            "description": "ID of the field to update",
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional new name for the field",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional new description for the field",
                        },
                    },
                    "required": ["base_id", "table_id", "field_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_FIELD"}
                ),
            ),
            types.Tool(
                name="airtable_list_records",
                description="Get all records from a table with optional filtering and formatting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID or name of the table to get records from",
                        },
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of field names to include in results (only these fields will be returned)",
                        },
                        "filter_by_formula": {
                            "type": "string",
                            "description": "Formula to filter records (e.g., \"{Status} = 'Active'\")",
                        },
                        "max_records": {
                            "type": "integer",
                            "description": "Maximum number of records to return (default: all records, max: 100)",
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of records to return per page (1-100, default: 100)",
                        },
                        "sort": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "direction": {
                                        "type": "string",
                                        "enum": ["asc", "desc"],
                                    },
                                },
                            },
                            "description": "List of sort objects with 'field' and 'direction' keys",
                        },
                        "return_fields_by_field_id": {
                            "type": "boolean",
                            "description": "Return fields keyed by field ID instead of name",
                        },
                    },
                    "required": ["base_id", "table_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_RECORD", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="airtable_get_record",
                description="Get a single record from a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID or name of the table containing the record",
                        },
                        "record_id": {
                            "type": "string",
                            "description": "ID of the record to retrieve",
                        },
                    },
                    "required": ["base_id", "table_id", "record_id"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_RECORD", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="airtable_create_records",
                description="Create multiple records in a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table to create records in",
                        },
                        "records": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of record objects to create",
                        },
                        "typecast": {
                            "type": "boolean",
                            "description": "Whether to automatically convert string values to appropriate types",
                        },
                        "return_fields_by_field_id": {
                            "type": "boolean",
                            "description": "Whether to return fields keyed by field ID instead of name",
                        },
                    },
                    "required": ["base_id", "table_id", "records"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_RECORD"}
                ),
            ),
            types.Tool(
                name="airtable_update_records",
                description="Update multiple records in a table with optional upsert functionality",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table containing the records",
                        },
                        "records": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Array of record objects. For regular updates: include 'id' and 'fields'. For upserts: include only 'fields'",
                        },
                        "typecast": {
                            "type": "boolean",
                            "description": "Whether to automatically convert string values to appropriate types",
                        },
                        "return_fields_by_field_id": {
                            "type": "boolean",
                            "description": "Whether to return fields keyed by field ID instead of name",
                        },
                        "perform_upsert": {
                            "type": "object",
                            "description": "Upsert configuration with fieldsToMergeOn array for matching existing records",
                            "properties": {
                                "fieldsToMergeOn": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of field names to use for matching existing records",
                                }
                            },
                        },
                    },
                    "required": ["base_id", "table_id", "records"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_RECORD"}
                ),
            ),
            types.Tool(
                name="airtable_delete_records",
                description="Delete multiple records from a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_id": {
                            "type": "string",
                            "description": "ID of the base containing the table",
                        },
                        "table_id": {
                            "type": "string",
                            "description": "ID of the table containing the records",
                        },
                        "record_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of record IDs to delete",
                        },
                    },
                    "required": ["base_id", "table_id", "record_ids"],
                },
                annotations=types.ToolAnnotations(
                    **{"category": "AIRTABLE_RECORD"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "airtable_list_bases_info":
            try:
                result = await get_bases_info()
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
        elif name == "airtable_list_tables_info":
            try:
                result = await get_tables_info(base_id=arguments.get("base_id"))
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
        elif name == "airtable_create_table":
            try:
                result = await create_table(
                    base_id=arguments.get("base_id"),
                    name=arguments.get("name"),
                    description=arguments.get("description"),
                    fields=arguments.get("fields"),
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
        elif name == "airtable_update_table":
            try:
                result = await update_table(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    name=arguments.get("name"),
                    description=arguments.get("description"),
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
        elif name == "airtable_create_field":
            try:
                result = await create_field(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    name=arguments.get("name"),
                    type=arguments.get("type"),
                    description=arguments.get("description"),
                    options=arguments.get("options"),
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
        elif name == "airtable_update_field":
            try:
                result = await update_field(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    field_id=arguments.get("field_id"),
                    name=arguments.get("name"),
                    description=arguments.get("description"),
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
        elif name == "airtable_list_records":
            try:
                result = await list_records(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    fields=arguments.get("fields"),
                    filter_by_formula=arguments.get("filter_by_formula"),
                    max_records=arguments.get("max_records"),
                    page_size=arguments.get("page_size"),
                    sort=arguments.get("sort"),
                    return_fields_by_field_id=arguments.get(
                        "return_fields_by_field_id"
                    ),
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
        elif name == "airtable_get_record":
            try:
                result = await get_record(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    record_id=arguments.get("record_id"),
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
        elif name == "airtable_create_records":
            try:
                result = await create_records(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    records=arguments.get("records"),
                    typecast=arguments.get("typecast"),
                    return_fields_by_field_id=arguments.get(
                        "return_fields_by_field_id"
                    ),
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
        elif name == "airtable_update_records":
            try:
                result = await update_records(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    records=arguments.get("records"),
                    typecast=arguments.get("typecast"),
                    return_fields_by_field_id=arguments.get(
                        "return_fields_by_field_id"
                    ),
                    perform_upsert=arguments.get("perform_upsert"),
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
        elif name == "airtable_delete_records":
            try:
                result = await delete_records(
                    base_id=arguments.get("base_id"),
                    table_id=arguments.get("table_id"),
                    record_ids=arguments.get("record_ids"),
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
