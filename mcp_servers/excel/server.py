import base64
import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict

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
    excel_create_workbook,
    excel_create_worksheets,
    excel_get_worksheet,
    excel_list_worksheets,
    excel_write_to_cell,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

EXCEL_MCP_SERVER_PORT = int(os.getenv("EXCEL_MCP_SERVER_PORT", "5000"))


def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header or environment."""
    auth_data = os.getenv("AUTH_DATA")

    if not auth_data:
        header_key = b"x-auth-data"
        if hasattr(request_or_scope, "headers"):
            # SSE request object
            auth_data = request_or_scope.headers.get(header_key)
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode("utf-8")
        elif isinstance(request_or_scope, dict) and "headers" in request_or_scope:
            # StreamableHTTP scope dict
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(header_key)
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode("utf-8")

    if not auth_data:
        return ""

    try:
        auth_json = json.loads(auth_data)
        token = auth_json.get("access_token", "")
        if isinstance(token, str):
            return token
        return ""
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to parse auth data JSON: %s", exc)
        return ""


def _tool_response(payload: Dict[str, Any]) -> list[types.TextContent]:
    return [
        types.TextContent(
            type="text",
            text=str(payload),
        )
    ]


@click.command()
@click.option("--port", default=EXCEL_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("microsoft-excel-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="microsoft_excel_create_workbook",
                description="Create a new Excel workbook in OneDrive or SharePoint. Optionally seed cell data.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Workbook title. The .xlsx extension is appended automatically.",
                        },
                        "data": {
                            "type": "string",
                            "description": "Optional JSON mapping row numbers to column/value dictionaries (e.g. {'1': {'A': 'Hello'}}).",
                        },
                        "sheet_name": {
                            "type": "string",
                            "description": "Optional name for the first worksheet.",
                        },
                        "parent_link": {
                            "type": "string",
                            "description": "Optional share link to the folder where the workbook should be created. If not specified, creates in the root of the user's personal OneDrive.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "MICROSOFT_EXCEL_WORKBOOK"}
                ),
            ),
            types.Tool(
                name="microsoft_excel_get_worksheet",
                description="Retrieve cell data from an Excel workbook using Microsoft Graph.",
                inputSchema={
                    "type": "object",
                    "required": ["workbook_url"],
                    "properties": {
                        "workbook_url": {
                            "type": "string",
                            "description": "The shared URL of the Excel workbook.",
                        },
                        "worksheet_id": {
                            "type": "string",
                            "description": "Optional worksheet ID. Provide this or worksheet_name. Defaults to the first worksheet.",
                        },
                        "worksheet_name": {
                            "type": "string",
                            "description": "Optional worksheet name. Provide this or worksheet_id. Defaults to the first worksheet.",
                        },
                        "range": {
                            "type": "string",
                            "description": "Optional A1-style range (e.g. 'Sheet1!A1:C10' or 'A1:C10'). If omitted, the used range of the worksheet is returned.",
                        },
                        "cell_value_format": {
                            "type": "string",
                            "enum": ["formatted", "userEntered", "all"],
                            "description": "Choose 'formatted' for display values, 'userEntered' for raw input values, or 'all' for both.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "MICROSOFT_EXCEL_WORKSHEET", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="microsoft_excel_write_to_cell",
                description="Write a single cell value in an Excel worksheet.",
                inputSchema={
                    "type": "object",
                    "required": ["workbook_url", "column", "row", "value"],
                    "properties": {
                        "workbook_url": {
                            "type": "string",
                            "description": "The shared URL of the Excel workbook.",
                        },
                        "column": {
                            "type": "string",
                            "description": "Column label (e.g. 'A', 'AA').",
                        },
                        "row": {
                            "type": "integer",
                            "description": "Row number (positive integer).",
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to write to the cell. Numbers/formulas can be passed as strings.",
                        },
                        "worksheet_id": {
                            "type": "string",
                            "description": "Optional worksheet ID. Provide this or worksheet_name. Defaults to the first worksheet.",
                        },
                        "worksheet_name": {
                            "type": "string",
                            "description": "Optional worksheet name. Provide this or worksheet_id. Defaults to the first worksheet.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "MICROSOFT_EXCEL_RANGE"}
                ),
            ),
            types.Tool(
                name="microsoft_excel_list_worksheets",
                description="List worksheets within an Excel workbook.",
                inputSchema={
                    "type": "object",
                    "required": ["workbook_url"],
                    "properties": {
                        "workbook_url": {
                            "type": "string",
                            "description": "The shared URL of the Excel workbook.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "MICROSOFT_EXCEL_WORKBOOK", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="microsoft_excel_create_worksheets",
                description="Create multiple empty worksheets in an Excel workbook.",
                inputSchema={
                    "type": "object",
                    "required": ["workbook_url", "sheet_names"],
                    "properties": {
                        "workbook_url": {
                            "type": "string",
                            "description": "The shared URL of the Excel workbook.",
                        },
                        "sheet_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of names for the new worksheets to create.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "MICROSOFT_EXCEL_WORKSHEET"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "microsoft_excel_create_workbook":
            try:
                title = arguments.get("title")
                if not title:
                    return _tool_response({"error": "title parameter is required"})
                data = arguments.get("data")
                sheet_name = arguments.get("sheet_name")
                parent_link = arguments.get("parent_link")
                result = await excel_create_workbook(
                    title=title,
                    data=data,
                    sheet_name=sheet_name,
                    parent_link=parent_link,
                )
                return _tool_response(result)
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return _tool_response({"error": str(e)})

        elif name == "microsoft_excel_get_worksheet":
            try:
                workbook_url = arguments.get("workbook_url")
                if not workbook_url:
                    return _tool_response({"error": "workbook_url parameter is required"})
                worksheet_id = arguments.get("worksheet_id")
                worksheet_name = arguments.get("worksheet_name")
                range_address = arguments.get("range")
                cell_value_format = arguments.get("cell_value_format", "formatted")
                result = await excel_get_worksheet(
                    workbook_url=workbook_url,
                    worksheet_id=worksheet_id,
                    worksheet_name=worksheet_name,
                    range_address=range_address,
                    cell_value_format=cell_value_format,
                )
                return _tool_response(result)
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return _tool_response({"error": str(e)})

        elif name == "microsoft_excel_write_to_cell":
            try:
                workbook_url = arguments.get("workbook_url")
                column = arguments.get("column")
                row = arguments.get("row")
                value = arguments.get("value")
                if workbook_url is None or column is None or row is None or value is None:
                    return _tool_response(
                        {
                            "error": "workbook_url, column, row, and value parameters are required"
                        }
                    )
                worksheet_id = arguments.get("worksheet_id")
                worksheet_name = arguments.get("worksheet_name")
                try:
                    row_index = int(row)
                except (TypeError, ValueError):
                    return _tool_response({"error": "row must be an integer"})
                result = await excel_write_to_cell(
                    workbook_url=workbook_url,
                    column=column,
                    row=row_index,
                    value=value,
                    worksheet_id=worksheet_id,
                    worksheet_name=worksheet_name,
                )
                return _tool_response(result)
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return _tool_response({"error": str(e)})

        elif name == "microsoft_excel_list_worksheets":
            try:
                workbook_url = arguments.get("workbook_url")
                if not workbook_url:
                    return _tool_response({"error": "workbook_url parameter is required"})
                result = await excel_list_worksheets(workbook_url)
                return _tool_response(result)
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return _tool_response({"error": str(e)})

        elif name == "microsoft_excel_create_worksheets":
            try:
                workbook_url = arguments.get("workbook_url")
                sheet_names = arguments.get("sheet_names")
                if not workbook_url:
                    return _tool_response({"error": "workbook_url parameter is required"})
                if not sheet_names or not isinstance(sheet_names, list):
                    return _tool_response({"error": "sheet_names parameter is required and must be an array"})
                result = await excel_create_worksheets(workbook_url, sheet_names)
                return _tool_response(result)
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return _tool_response({"error": str(e)})

        logger.error("Unknown tool requested: %s", name)
        return _tool_response({"error": f"Unknown tool: {name}"})

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        auth_token = extract_access_token(request)
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

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        auth_token = extract_access_token(scope)
        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Excel MCP server started with SSE + StreamableHTTP")
            try:
                yield
            finally:
                logger.info("Excel MCP server shutting down")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info("Microsoft Excel MCP server listening on port %s", port)
    logger.info("  - SSE endpoint: http://0.0.0.0:%s/sse", port)
    logger.info("  - StreamableHTTP endpoint: http://0.0.0.0:%s/mcp", port)

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()
