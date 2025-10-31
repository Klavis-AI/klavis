import contextlib
import base64
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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from exceptions import RetryableToolError
from models import (
    SheetDataInput,
    Spreadsheet,
    SpreadsheetProperties,
)
from utils import (
    create_sheet,
    parse_get_spreadsheet_response,
    parse_write_to_cell_response,
    validate_write_to_cell_params,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_SHEETS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_SHEETS_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

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

def get_sheets_service(access_token: str):
    """Create Google Sheets service with access token."""
    credentials = Credentials(token=access_token)
    return build('sheets', 'v4', credentials=credentials)

# This is used for the list_all_sheets tool
def get_drive_service(access_token: str):
    """Create Google Drive service with access token."""
    credentials = Credentials(token=access_token)
    return build('drive', 'v3', credentials=credentials)

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def get_auth_token_or_empty() -> str:
    """Get the authentication token from context or return empty string."""
    try:
        return auth_token_context.get()
    except LookupError:
        return ""

# Context class to mock the context.get_auth_token_or_empty() calls
class Context:
    def get_auth_token_or_empty(self) -> str:
        return get_auth_token_or_empty()

context = Context()

async def create_spreadsheet_tool(
    title: str = "Untitled spreadsheet",
    data: str | None = None,
) -> Dict[str, Any]:
    """Create a new spreadsheet with the provided title and data in its first sheet."""
    logger.info(f"Executing tool: create_spreadsheet with title: {title}")
    try:
        access_token = get_auth_token()
        service = get_sheets_service(access_token)

        try:
            sheet_data = SheetDataInput(data=data)  # type: ignore[arg-type]
        except Exception as e:
            msg = "Invalid JSON or unexpected data format for parameter `data`"
            raise RetryableToolError(
                message=msg,
                additional_prompt_content=f"{msg}: {e}",
                retry_after_ms=100,
            )

        spreadsheet = Spreadsheet(
            properties=SpreadsheetProperties(title=title),
            sheets=[create_sheet(sheet_data)],
        )

        body = spreadsheet.model_dump()

        response = (
            service.spreadsheets()
            .create(body=body, fields="spreadsheetId,spreadsheetUrl,properties/title")
            .execute()
        )

        return {
            "title": response["properties"]["title"],
            "spreadsheetId": response["spreadsheetId"],
            "spreadsheetUrl": response["spreadsheetUrl"],
        }
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Sheets API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_spreadsheet: {e}")
        raise e

async def get_spreadsheet_tool(spreadsheet_id: str) -> Dict[str, Any]:
    """Get the user entered values and formatted values for all cells in all sheets in the spreadsheet."""
    logger.info(f"Executing tool: get_spreadsheet with spreadsheet_id: {spreadsheet_id}")
    try:
        access_token = get_auth_token()
        service = get_sheets_service(access_token)
        
        response = (
            service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                includeGridData=True,
                fields="spreadsheetId,spreadsheetUrl,properties/title,sheets/properties,sheets/data/rowData/values/userEnteredValue,sheets/data/rowData/values/formattedValue,sheets/data/rowData/values/effectiveValue",
            )
            .execute()
        )
        return parse_get_spreadsheet_response(response)
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Sheets API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_spreadsheet: {e}")
        raise e

async def write_to_cell_tool(
    spreadsheet_id: str,
    column: str,
    row: int,
    value: str,
    sheet_name: str = "Sheet1",
) -> Dict[str, Any]:
    """Write a value to a single cell in a spreadsheet."""
    logger.info(f"Executing tool: write_to_cell with spreadsheet_id: {spreadsheet_id}, cell: {column}{row}")
    try:
        access_token = get_auth_token()
        service = get_sheets_service(access_token)
        
        validate_write_to_cell_params(service, spreadsheet_id, sheet_name, column, row)

        range_ = f"'{sheet_name}'!{column.upper()}{row}"
        body = {
            "range": range_,
            "majorDimension": "ROWS",
            "values": [[value]],
        }

        sheet_properties = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                includeValuesInResponse=True,
                body=body,
            )
            .execute()
        )

        return parse_write_to_cell_response(sheet_properties)
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Sheets API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool write_to_cell: {e}")
        raise e

async def list_all_sheets_tool() -> Dict[str, Any]:
    """List all Google Sheets spreadsheets in the user's Google Drive."""
    logger.info("Executing tool: list_all_sheets")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        # Search for Google Sheets files (mimeType for Google Sheets)
        query = "mimeType='application/vnd.google-apps.spreadsheet'"
        
        results = service.files().list(
            q=query,
            fields="files(id,name,createdTime,modifiedTime,owners,webViewLink)",
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        spreadsheets = []
        for file in files:
            spreadsheet_info = {
                "id": file.get('id'),
                "name": file.get('name'),
                "createdTime": file.get('createdTime'),
                "modifiedTime": file.get('modifiedTime'),
                "webViewLink": file.get('webViewLink'),
                "owners": [owner.get('displayName', owner.get('emailAddress', 'Unknown')) 
                          for owner in file.get('owners', [])]
            }
            spreadsheets.append(spreadsheet_info)
        
        return {
            "spreadsheets": spreadsheets,
            "total_count": len(spreadsheets)
        }
        
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool list_all_sheets: {e}")
        raise e

@click.command()
@click.option("--port", default=GOOGLE_SHEETS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("google-sheets-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_sheets_create_spreadsheet",
                description="Create a new spreadsheet with a title and optional data.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the new spreadsheet.",
                        },
                        "data": {
                            "type": "string",
                            "description": "The data to write to the spreadsheet. A JSON string (property names enclosed in double quotes) representing a dictionary that maps row numbers to dictionaries that map column letters to cell values. For example, data[23]['C'] would be the value of the cell in row 23, column C. Type hint: dict[int, dict[str, Union[int, float, str, bool]]]",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_SHEETS_SPREADSHEET"}
                ),
            ),
            types.Tool(
                name="google_sheets_get_spreadsheet",
                description="Retrieve spreadsheet properties and cell data for all sheets.",
                inputSchema={
                    "type": "object",
                    "required": ["spreadsheet_id"],
                    "properties": {
                        "spreadsheet_id": {
                            "type": "string",
                            "description": "The ID of the spreadsheet to retrieve.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_SHEETS_SPREADSHEET", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_sheets_write_to_cell",
                description="Write a value to a specific cell in a spreadsheet.",
                inputSchema={
                    "type": "object",
                    "required": ["spreadsheet_id", "column", "row", "value"],
                    "properties": {
                        "spreadsheet_id": {
                            "type": "string",
                            "description": "The ID of the spreadsheet to write to.",
                        },
                        "column": {
                            "type": "string",
                            "description": "The column string to write to. For example, 'A', 'F', or 'AZ'.",
                        },
                        "row": {
                            "type": "integer",
                            "description": "The row number to write to.",
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to write to the cell.",
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "The name of the sheet to write to. Defaults to 'Sheet1'.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_SHEETS_CELL"}
                ),
            ),
            types.Tool(
                name="google_sheets_list_all_sheets",
                description="List all Google Sheets spreadsheets in the user's Google Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_SHEETS_SPREADSHEET", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:     
        if name == "google_sheets_create_spreadsheet":
            title = arguments.get("title")
            data = arguments.get("data")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title parameter is required",
                    )
                ]
            
            try:
                result = await create_spreadsheet_tool(title, data)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
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
        
        elif name == "google_sheets_get_spreadsheet":
            spreadsheet_id = arguments.get("spreadsheet_id")
            if not spreadsheet_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: spreadsheet_id parameter is required",
                    )
                ]
            
            try:
                result = await get_spreadsheet_tool(spreadsheet_id)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
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
        
        elif name == "google_sheets_write_to_cell":
            spreadsheet_id = arguments.get("spreadsheet_id")
            column = arguments.get("column")
            row = arguments.get("row")
            value = arguments.get("value")
            sheet_name = arguments.get("sheet_name", "Sheet1")
            
            if not all([spreadsheet_id, column, row is not None, value is not None]):
                return [
                    types.TextContent(
                        type="text",
                        text="Error: spreadsheet_id, column, row, and value parameters are required",
                    )
                ]
            
            try:
                result = await write_to_cell_tool(spreadsheet_id, column, row, value, sheet_name)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
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
        
        elif name == "google_sheets_list_all_sheets":
            try:
                result = await list_all_sheets_tool()
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
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