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

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_DOCS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_DOCS_MCP_SERVER_PORT", "5000"))

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

def get_docs_service(access_token: str):
    """Create Google Docs service with access token."""
    credentials = Credentials(token=access_token)
    return build('docs', 'v1', credentials=credentials)

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


def normalize_document_response(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the Google Docs API response to a simplified structure.
    Reduces complexity while preserving important information.
    """
    
    def extract_text_from_paragraph(paragraph: Dict) -> Dict[str, Any]:
        """Extract text content and styling from a paragraph."""
        elements = paragraph.get('elements', [])
        text_parts = []
        
        for element in elements:
            if 'textRun' in element:
                text_run = element['textRun']
                content = text_run.get('content', '')
                text_style = text_run.get('textStyle', {})
                
                part = {'text': content}
                if text_style.get('bold'):
                    part['bold'] = True
                if text_style.get('italic'):
                    part['italic'] = True
                if text_style.get('underline'):
                    part['underline'] = True
                
                text_parts.append(part)
        
        # Combine text for simple display
        full_text = ''.join(p['text'] for p in text_parts).strip()
        
        result = {'text': full_text}
        
        # Add paragraph style info
        para_style = paragraph.get('paragraphStyle', {})
        named_style = para_style.get('namedStyleType')
        if named_style and named_style != 'NORMAL_TEXT':
            result['style'] = named_style
        
        heading_id = para_style.get('headingId')
        if heading_id:
            result['headingId'] = heading_id
        
        # Add bullet info if present
        if 'bullet' in paragraph:
            bullet = paragraph['bullet']
            result['isBullet'] = True
            result['listId'] = bullet.get('listId')
            if bullet.get('nestingLevel', 0) > 0:
                result['nestingLevel'] = bullet['nestingLevel']
        
        # Include rich text parts if there's formatting
        has_formatting = any(
            p.get('bold') or p.get('italic') or p.get('underline')
            for p in text_parts
        )
        if has_formatting:
            result['formattedParts'] = [p for p in text_parts if p['text'].strip()]
        
        return result
    
    def extract_table(table: Dict) -> Dict[str, Any]:
        """Extract table content in a simplified format."""
        rows = table.get('rows', 0)
        columns = table.get('columns', 0)
        table_rows = table.get('tableRows', [])
        
        extracted_rows = []
        for table_row in table_rows:
            cells = []
            for cell in table_row.get('tableCells', []):
                cell_content = []
                for content_item in cell.get('content', []):
                    if 'paragraph' in content_item:
                        para_data = extract_text_from_paragraph(content_item['paragraph'])
                        if para_data['text']:
                            cell_content.append(para_data['text'])
                cells.append(' '.join(cell_content))
            extracted_rows.append(cells)
        
        return {
            'type': 'table',
            'rows': rows,
            'columns': columns,
            'data': extracted_rows
        }
    
    def process_content(content_list: list) -> list:
        """Process the document content into a simplified structure."""
        processed = []
        
        for item in content_list:
            # Skip section breaks
            if 'sectionBreak' in item:
                continue
            
            # Process paragraphs
            if 'paragraph' in item:
                para_data = extract_text_from_paragraph(item['paragraph'])
                if para_data['text']:  # Only include non-empty paragraphs
                    processed.append({
                        'type': 'paragraph',
                        **para_data
                    })
            
            # Process tables
            elif 'table' in item:
                table_data = extract_table(item['table'])
                processed.append(table_data)
        
        return processed
    
    # Build the normalized response
    normalized = {
        'documentId': raw_response.get('documentId'),
        'title': raw_response.get('title'),
        'revisionId': raw_response.get('revisionId'),
    }
    
    # Process body content
    body = raw_response.get('body', {})
    content = body.get('content', [])
    normalized['content'] = process_content(content)
    
    # Extract document metadata
    doc_style = raw_response.get('documentStyle', {})
    if doc_style:
        page_size = doc_style.get('pageSize', {})
        normalized['pageInfo'] = {
            'width': page_size.get('width', {}).get('magnitude'),
            'height': page_size.get('height', {}).get('magnitude'),
            'unit': page_size.get('width', {}).get('unit', 'PT'),
            'margins': {
                'top': doc_style.get('marginTop', {}).get('magnitude'),
                'bottom': doc_style.get('marginBottom', {}).get('magnitude'),
                'left': doc_style.get('marginLeft', {}).get('magnitude'),
                'right': doc_style.get('marginRight', {}).get('magnitude'),
            }
        }
    
    # Include list definitions (simplified)
    lists = raw_response.get('lists', {})
    if lists:
        normalized['lists'] = {
            list_id: {
                'type': 'bullet' if props.get('listProperties', {}).get('nestingLevels', [{}])[0].get('glyphSymbol') else 'numbered'
            }
            for list_id, props in lists.items()
        }
    
    return normalized

async def _get_document_raw(document_id: str) -> Dict[str, Any]:
    """Internal function to get raw Google Docs API response."""
    access_token = get_auth_token()
    service = get_docs_service(access_token)
    request = service.documents().get(documentId=document_id)
    response = request.execute()
    return dict(response)


async def get_document_by_id(document_id: str) -> Dict[str, Any]:
    """Get the latest version of the specified Google Docs document.
    
    Args:
        document_id: The ID of the Google Docs document to retrieve.
    
    Returns:
        Normalized document response with simplified structure.
    """
    logger.info(f"Executing tool: get_document_by_id with document_id: {document_id}")
    try:
        raw_response = await _get_document_raw(document_id)
        return normalize_document_response(raw_response)
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_document_by_id: {e}")
        raise e

async def insert_text_at_end(document_id: str, text: str) -> Dict[str, Any]:
    """Insert text at the end of a Google Docs document."""
    logger.info(f"Executing tool: insert_text_at_end with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        # Need raw response to get endIndex
        document = await _get_document_raw(document_id)
        
        end_index = document["body"]["content"][-1]["endIndex"]
        
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': int(end_index) - 1
                    },
                    'text': text
                }
            }
        ]
        
        # Execute the request
        response = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        
        return {
            "id": document_id,
            "status": "success",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool insert_text_at_end: {e}")
        raise e

async def create_blank_document(title: str) -> Dict[str, Any]:
    """Create a new blank Google Docs document with a title."""
    logger.info(f"Executing tool: create_blank_document with title: {title}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        body = {"title": title}
        
        request = service.documents().create(body=body)
        response = request.execute()
        
        return {
            "title": response["title"],
            "id": response["documentId"],
            "url": f"https://docs.google.com/document/d/{response['documentId']}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_blank_document: {e}")
        raise e

async def create_document_from_text(title: str, text_content: str) -> Dict[str, Any]:
    """Create a new Google Docs document with specified text content."""
    logger.info(f"Executing tool: create_document_from_text with title: {title}")
    try:
        # First, create a blank document
        document = await create_blank_document(title)
        
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        # Insert the text content
        requests = [
            {
                "insertText": {
                    "location": {
                        "index": 1,
                    },
                    "text": text_content,
                }
            }
        ]
        
        # Execute the batchUpdate method to insert text
        service.documents().batchUpdate(
            documentId=document["id"], body={"requests": requests}
        ).execute()
        
        return {
            "title": document["title"],
            "id": document["id"],
            "url": f"https://docs.google.com/document/d/{document["id"]}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_document_from_text: {e}")
        raise e

async def get_all_documents() -> Dict[str, Any]:
    """Get all Google Docs documents from the user's Drive."""
    logger.info(f"Executing tool: get_all_documents")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        # Query for Google Docs files
        query = "mimeType='application/vnd.google-apps.document'"
        
        request = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc"
        )
        response = request.execute()
        
        documents = []
        for file in response.get('files', []):
            documents.append({
                'id': file['id'],
                'name': file['name'],
                'createdAt': file.get('createdTime'),
                'modifiedAt': file.get('modifiedTime'),
                'url': file.get('webViewLink')
            })
        
        return {
            'documents': documents,
            'total_count': len(documents)
        }
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_all_documents: {e}")
        raise e

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
                description="Retrieve a Google Docs document by ID.",
                inputSchema={
                    "type": "object",
                    "required": ["document_id"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document to retrieve.",
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
            
            try:
                result = await get_document_by_id(document_id)
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
        
        elif name == "google_docs_get_all_documents":            
            try:
                result = await get_all_documents()
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