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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_DOCS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_DOCS_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

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

async def get_document_by_id(document_id: str) -> Dict[str, Any]:
    """Get the latest version of the specified Google Docs document."""
    logger.info(f"Executing tool: get_document_by_id with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        request = service.documents().get(documentId=document_id)
        response = request.execute()
        
        return dict(response)
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
        
        document = await get_document_by_id(document_id)
        
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
        
        return dict(response)
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
            "document_id": response["documentId"],
            "document_url": f"https://docs.google.com/document/d/{response['documentId']}/edit",
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
            documentId=document["document_id"], body={"requests": requests}
        ).execute()
        
        return {
            "title": document["title"],
            "documentId": document["document_id"],
            "documentUrl": f"https://docs.google.com/document/d/{document['document_id']}/edit",
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
                'createdTime': file.get('createdTime'),
                'modifiedTime': file.get('modifiedTime'),
                'webViewLink': file.get('webViewLink')
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
            ),
            types.Tool(
                name="google_docs_get_all_documents",
                description="Get all Google Docs documents from the user's Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
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