"""Google Docs MCP Server - Main entry point."""

import contextlib
import json
import logging
import os
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

# Import from tools package
from tools import (
    # Base utilities
    auth_token_context,
    extract_access_token,
    # Converters (for backward compatibility)
    normalize_document_response,
    # Tools
    get_document_by_id,
    get_all_documents,
    insert_text_at_end,
    create_blank_document,
    create_document_from_text,
    edit_text,
    apply_style,
    insert_formatted_text,
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_DOCS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_DOCS_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option("--port", default=GOOGLE_DOCS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("google-docs-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_docs_get_document_by_id",
                description="""Retrieve a Google Docs document by ID.

Response formats: 'normalized' (default), 'raw', 'plain_text', 'markdown', 'structured'.
Use 'structured' to get character indices for editing with apply_style.""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document to retrieve.",
                        },
                        "response_format": {
                            "type": "string",
                            "enum": ["raw", "plain_text", "markdown", "structured", "normalized"],
                            "description": "Output format. Default: 'normalized' (backward compatible)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_docs_get_all_documents",
                description="Get all Google Docs documents from the user's Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_docs_insert_text_at_end",
                description="Insert text at the end of a Google Docs document.",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document to modify.",
                        },
                        "text": {
                            "type": "string",
                            "description": "The text content to insert at the end of the document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_create_blank_document",
                description="Create a new blank Google Docs document with a title.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title for the new document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_create_document_from_text",
                description="Create a new Google Docs document with specified text content.",
                inputSchema={
                    "type": "object",
                    "required": ["title", "text_content"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title for the new document.",
                        },
                        "text_content": {
                            "type": "string",
                            "description": "The text content to include in the new document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            # New tools
            types.Tool(
                name="google_docs_edit_text",
                description="""Edit text in a Google Docs document by replacing old text with new text.

Operations: Replace (old_text→new_text), Delete (new_text=""), Append (old_text="" with append_to_end=true).
Note: Google Docs API always replaces all occurrences.""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "old_text", "new_text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to find and replace. Use empty string with append_to_end=true to insert at end.",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The replacement text. Use empty string to delete.",
                        },
                        "match_case": {
                            "type": "boolean",
                            "description": "Whether to match case when finding old_text. Default: true",
                        },
                        "replace_all": {
                            "type": "boolean",
                            "description": "Replace all occurrences or just the first one. Default: false (Note: Google Docs API always replaces all)",
                        },
                        "append_to_end": {
                            "type": "boolean",
                            "description": "If true and old_text is empty, append new_text to the end of document. Default: false",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_apply_style",
                description="""Apply formatting styles to a specified range in a Google Docs document.

Supports both character-level styles (bold, italic, etc.) and paragraph-level styles (headings, alignment, etc.).

To find the correct indices, use google_docs_get_document_by_id with response_format='structured'.
""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "start_index", "end_index"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "start_index": {
                            "type": "integer",
                            "description": "Start position of the range (1-based, inclusive).",
                        },
                        "end_index": {
                            "type": "integer",
                            "description": "End position of the range (exclusive).",
                        },
                        # Character styles
                        "bold": {
                            "type": "boolean",
                            "description": "Apply bold formatting.",
                        },
                        "italic": {
                            "type": "boolean",
                            "description": "Apply italic formatting.",
                        },
                        "underline": {
                            "type": "boolean",
                            "description": "Apply underline formatting.",
                        },
                        "strikethrough": {
                            "type": "boolean",
                            "description": "Apply strikethrough formatting.",
                        },
                        "font_size": {
                            "type": "number",
                            "description": "Font size in points (e.g., 12, 14, 18).",
                        },
                        "font_family": {
                            "type": "string",
                            "description": "Font family name (e.g., 'Arial', 'Times New Roman').",
                        },
                        "foreground_color": {
                            "type": "string",
                            "description": "Text color in hex format (e.g., '#FF0000' for red).",
                        },
                        "background_color": {
                            "type": "string",
                            "description": "Background/highlight color in hex format.",
                        },
                        "link_url": {
                            "type": "string",
                            "description": "URL to create a hyperlink.",
                        },
                        # Paragraph styles
                        "heading_type": {
                            "type": "string",
                            "enum": ["NORMAL_TEXT", "TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"],
                            "description": "Paragraph heading style.",
                        },
                        "alignment": {
                            "type": "string",
                            "enum": ["START", "CENTER", "END", "JUSTIFIED"],
                            "description": "Text alignment.",
                        },
                        "line_spacing": {
                            "type": "number",
                            "description": "Line spacing (100 = single, 150 = 1.5, 200 = double).",
                        },
                        "space_above": {
                            "type": "number",
                            "description": "Space above paragraph in points.",
                        },
                        "space_below": {
                            "type": "number",
                            "description": "Space below paragraph in points.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_insert_formatted_text",
                description="""Insert formatted text using markdown-like syntax.

Supported: **bold**, *italic*, ~~strikethrough~~, `code`, [link](url), # headings (1-6), - bullets.
Escape with backslash: \\* \\_ \\` for literal characters.""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "formatted_text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "formatted_text": {
                            "type": "string",
                            "description": "Text with markdown-like syntax for formatting.",
                        },
                        "position": {
                            "type": "string",
                            "enum": ["end", "beginning"],
                            "description": "Where to insert the text. Default: 'end'",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == "google_docs_get_document_by_id":
            document_id = arguments.get("document_id")
            if not document_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id parameter is required",
                    )
                ]

            # Get response_format with default 'normalized' for backward compatibility
            response_format = arguments.get("response_format", "normalized")

            try:
                result = await get_document_by_id(document_id, response_format)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result),
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

        elif name == "google_docs_get_all_documents":
            try:
                result = await get_all_documents()
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_insert_text_at_end":
            document_id = arguments.get("document_id")
            text = arguments.get("text")
            if not document_id or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id and text parameters are required",
                    )
                ]

            try:
                result = await insert_text_at_end(document_id, text)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_create_blank_document":
            title = arguments.get("title")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title parameter is required",
                    )
                ]

            try:
                result = await create_blank_document(title)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_create_document_from_text":
            title = arguments.get("title")
            text_content = arguments.get("text_content")
            if not title or not text_content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title and text_content parameters are required",
                    )
                ]

            try:
                result = await create_document_from_text(title, text_content)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_edit_text":
            document_id = arguments.get("document_id")
            old_text = arguments.get("old_text")
            new_text = arguments.get("new_text")

            if not document_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id parameter is required",
                    )
                ]

            # old_text and new_text can be empty strings, so check for None explicitly
            if old_text is None or new_text is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: old_text and new_text parameters are required",
                    )
                ]

            match_case = arguments.get("match_case", True)
            replace_all = arguments.get("replace_all", False)
            append_to_end = arguments.get("append_to_end", False)

            try:
                result = await edit_text(
                    document_id=document_id,
                    old_text=old_text,
                    new_text=new_text,
                    match_case=match_case,
                    replace_all=replace_all,
                    append_to_end=append_to_end
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_apply_style":
            document_id = arguments.get("document_id")
            start_index = arguments.get("start_index")
            end_index = arguments.get("end_index")

            if not document_id or start_index is None or end_index is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id, start_index, and end_index parameters are required",
                    )
                ]

            try:
                result = await apply_style(
                    document_id=document_id,
                    start_index=start_index,
                    end_index=end_index,
                    bold=arguments.get("bold"),
                    italic=arguments.get("italic"),
                    underline=arguments.get("underline"),
                    strikethrough=arguments.get("strikethrough"),
                    font_size=arguments.get("font_size"),
                    font_family=arguments.get("font_family"),
                    foreground_color=arguments.get("foreground_color"),
                    background_color=arguments.get("background_color"),
                    link_url=arguments.get("link_url"),
                    heading_type=arguments.get("heading_type"),
                    alignment=arguments.get("alignment"),
                    line_spacing=arguments.get("line_spacing"),
                    space_above=arguments.get("space_above"),
                    space_below=arguments.get("space_below")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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

        elif name == "google_docs_insert_formatted_text":
            document_id = arguments.get("document_id")
            formatted_text = arguments.get("formatted_text")

            if not document_id or not formatted_text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id and formatted_text parameters are required",
                    )
                ]

            position = arguments.get("position", "end")

            try:
                result = await insert_formatted_text(
                    document_id=document_id,
                    formatted_text=formatted_text,
                    position=position
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
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
