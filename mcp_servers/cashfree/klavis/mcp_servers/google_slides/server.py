import os
import base64
import json
import uuid
import logging
import contextlib
from collections.abc import AsyncIterator
from typing import List, Optional, Dict, Any
from contextvars import ContextVar

import click
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import service_account
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-slides-mcp-server")

# Constants
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive.readonly']
GOOGLE_SLIDES_MCP_SERVER_PORT = int(os.getenv("GOOGLE_SLIDES_MCP_SERVER_PORT", "5000"))

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

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

def get_slides_service(access_token: str):
    """Create Google Slides service with access token."""
    credentials = Credentials(token=access_token)
    return build('slides', 'v1', credentials=credentials)

def get_drive_service(access_token: str):
    """Create Google Drive service with access token."""
    credentials = Credentials(token=access_token)
    return build('drive', 'v3', credentials=credentials)

def get_credentials():
    """
    Gets Google API credentials from service account or OAuth2 flow.
    Returns credentials object for use with Google APIs.
    """
    # Try to get token from context first
    try:
        access_token = get_auth_token()
        if access_token:
            return Credentials(token=access_token)
    except RuntimeError:
        pass  # No token in context, fall back to other methods
    creds = None
    # Check if we have service account credentials
    if os.path.exists('service-account.json'):
        return service_account.Credentials.from_service_account_file(
            'service-account.json', scopes=SCOPES)
    
    # Check if we have saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(
            json.loads(open('token.json').read()), SCOPES)
    
    # If there are no valid credentials, or they're expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            # Load client secrets
            if os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise Exception("No credentials found. Please set up credentials.")
        
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

async def create_presentation(title: str) -> str:
    """
    Creates a new Google Slides presentation with the specified title.
    
    Args:
        title: The title of the new presentation
        
    Returns:
        A URL to the created presentation
    """
    try:
        creds = get_credentials()
        service = build('slides', 'v1', credentials=creds)
        
        presentation = {
            'title': title
        }
        
        presentation = service.presentations().create(body=presentation).execute()
        presentation_id = presentation.get('presentationId')
        
        return f"Presentation created: https://docs.google.com/presentation/d/{presentation_id}/edit"
    except Exception as e:
        logger.error(f"Error creating presentation: {e}")
        return f"Error creating presentation: {str(e)}"

async def add_slide(presentation_id: str, title: Optional[str] = None, content: Optional[str] = None) -> str:
    """
    Adds a new slide to an existing presentation.
    
    Args:
        presentation_id: The ID of the presentation to add a slide to
        title: Optional title for the slide
        content: Optional content for the slide body
        
    Returns:
        A message indicating the result of the operation
    """
    try:
        creds = get_credentials()
        service = build('slides', 'v1', credentials=creds)
        
        # Create a blank slide
        requests = [
            {
                'createSlide': {
                    'objectId': str(uuid.uuid4()),
                    'insertionIndex': '1',
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    }
                }
            }
        ]
        
        response = service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
        
        slide_id = response.get('replies', [{}])[0].get('createSlide', {}).get('objectId')
        
        # If title or content provided, add them in a second request
        if title or content:
            content_requests = []
            
            if title:
                content_requests.append({
                    'insertText': {
                        'objectId': slide_id,
                        'insertionIndex': 0,
                        'text': title
                    }
                })
            
            if content:
                content_requests.append({
                    'insertText': {
                        'objectId': slide_id,
                        'insertionIndex': 0,
                        'text': content
                    }
                })
                
            if content_requests:
                service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={'requests': content_requests}
                ).execute()
        
        return f"Slide added to presentation: https://docs.google.com/presentation/d/{presentation_id}/edit"
    except Exception as e:
        logger.error(f"Error adding slide: {e}")
        return f"Error adding slide: {str(e)}"

async def list_presentations() -> str:
    """
    Lists all available presentations in the user's Google Drive.
    
    Returns:
        A formatted string listing all presentations
    """
    try:
        creds = get_credentials()
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Query for Google Slides files
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.presentation'",
            pageSize=10,
            fields="files(id, name, webViewLink)"
        ).execute()
        
        presentations = results.get('files', [])
        
        if not presentations:
            return "No presentations found."
        
        result = "Available presentations:\n\n"
        for p in presentations:
            result += f"- {p.get('name')}: {p.get('webViewLink')}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error listing presentations: {e}")
        return f"Error listing presentations: {str(e)}"
        
async def get_presentation(presentation_id: str, fields: Optional[str] = None) -> str:
    """
    Retrieves detailed information about a specific presentation.
    
    Args:
        presentation_id: The ID of the presentation to retrieve
        fields: Optional field mask to limit the returned data (e.g., "slides,pageSize")
        
    Returns:
        A formatted string with presentation details
    """
    try:
        creds = get_credentials()
        service = build('slides', 'v1', credentials=creds)
        
        # Set default fields if none specified
        if not fields:
            fields = "presentationId,title,revisionId,slides,pageSize"
            
        # Retrieve the presentation
        presentation = service.presentations().get(
            presentationId=presentation_id,
            fields=fields
        ).execute()
        
        # Format the response
        title = presentation.get('title', 'Untitled')
        slide_count = len(presentation.get('slides', []))
        revision_id = presentation.get('revisionId', 'Unknown')
        page_size = presentation.get('pageSize', {})
        width = page_size.get('width', {}).get('magnitude', 0)
        height = page_size.get('height', {}).get('magnitude', 0)
        
        result = f"Presentation: {title}\n"
        result += f"ID: {presentation_id}\n"
        result += f"Slides: {slide_count}\n"
        result += f"Revision ID: {revision_id}\n"
        result += f"Page Size: {width}x{height}\n\n"
        
        if 'slides' in fields.split(',') and slide_count > 0:
            result += "Slide Overview:\n"
            for i, slide in enumerate(presentation.get('slides', [])):
                slide_id = slide.get('objectId', 'Unknown')
                result += f"Slide {i+1} (ID: {slide_id})\n"
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving presentation: {e}")
        return f"Error retrieving presentation: {str(e)}"
        
async def batch_update_presentation(presentation_id: str, requests: List[Dict]) -> str:
    """
    Applies a series of updates to a presentation.
    This is the primary method for modifying slides (adding text, shapes, images, creating slides, etc.)
    
    Args:
        presentation_id: The ID of the presentation to update
        requests: List of request objects defining the updates
        
    Returns:
        A message indicating the result of the operation
    """
    try:
        creds = get_credentials()
        service = build('slides', 'v1', credentials=creds)
        
        # Execute the batch update
        response = service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
        
        # Format the response
        replies = response.get('replies', [])
        result = f"Successfully applied {len(replies)} updates to presentation\n"
        result += f"Presentation URL: https://docs.google.com/presentation/d/{presentation_id}/edit\n\n"
        
        # Add information about created slides if any
        created_slides = [r.get('createSlide', {}).get('objectId') 
                         for r in replies if 'createSlide' in r]
        if created_slides:
            result += f"Created {len(created_slides)} new slides with IDs: {', '.join(created_slides)}\n"
        
        return result
    except Exception as e:
        logger.error(f"Error updating presentation: {e}")
        return f"Error updating presentation: {str(e)}"
        
async def summarize_presentation(presentation_id: str, include_notes: bool = False) -> str:
    """
    Extracts and formats all text content from a presentation for easier summarization.
    
    Args:
        presentation_id: The ID of the presentation to summarize
        include_notes: Whether to include speaker notes in the summary
        
    Returns:
        A formatted string containing the presentation's text content
    """
    try:
        creds = get_credentials()
        service = build('slides', 'v1', credentials=creds)
        
        # Retrieve the presentation with all text elements
        presentation = service.presentations().get(
            presentationId=presentation_id
        ).execute()
        
        title = presentation.get('title', 'Untitled')
        slides = presentation.get('slides', [])
        
        result = f"Summary of: {title}\n"
        result += f"Total Slides: {len(slides)}\n\n"
        
        # Process each slide
        for i, slide in enumerate(slides):
            slide_id = slide.get('objectId', 'Unknown')
            result += f"Slide {i+1} (ID: {slide_id}):\n"
            
            # Extract text from text elements
            text_elements = []
            page_elements = slide.get('pageElements', [])
            
            for element in page_elements:
                if 'shape' in element and 'text' in element['shape']:
                    shape_text = ""
                    text_runs = element['shape']['text'].get('textElements', [])
                    
                    for text_run in text_runs:
                        if 'textRun' in text_run and 'content' in text_run['textRun']:
                            shape_text += text_run['textRun']['content']
                    
                    if shape_text.strip():
                        text_elements.append(shape_text.strip())
            
            # Add the text content
            if text_elements:
                for text in text_elements:
                    result += f"  {text}\n"
            else:
                result += "  [No text content]\n"
            
            # Add speaker notes if requested
            if include_notes and 'slideProperties' in slide and 'notesPage' in slide['slideProperties']:
                notes_page = slide['slideProperties']['notesPage']
                notes_text = ""
                
                if 'pageElements' in notes_page:
                    for element in notes_page['pageElements']:
                        if 'shape' in element and 'text' in element['shape']:
                            text_runs = element['shape']['text'].get('textElements', [])
                            
                            for text_run in text_runs:
                                if 'textRun' in text_run and 'content' in text_run['textRun']:
                                    notes_text += text_run['textRun']['content']
                
                if notes_text.strip():
                    result += f"  Notes: {notes_text.strip()}\n"
            
            result += "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error summarizing presentation: {e}")
        return f"Error summarizing presentation: {str(e)}"

@click.command()
@click.option("--port", default=GOOGLE_SLIDES_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server(
        "google-slides-mcp-server",
        instructions="Create and manage Google Slides presentations. You can create new presentations, add slides to existing presentations, and list available presentations.",
    )

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="create_presentation",
                description="Create a new Google Slides presentation with the specified title.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the new presentation."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_PRESENTATION"}),
            ),
            types.Tool(
                name="add_slide",
                description="Add a new slide to an existing presentation.",
                inputSchema={
                    "type": "object",
                    "required": ["presentation_id"],
                    "properties": {
                        "presentation_id": {
                            "type": "string",
                            "description": "The ID of the presentation to add a slide to."
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for the slide."
                        },
                        "content": {
                            "type": "string",
                            "description": "Optional content for the slide body."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_SLIDE"}),
            ),
            types.Tool(
                name="list_presentations",
                description="List all available presentations in the user's Google Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_PRESENTATION", "readOnlyHint": True}),
            ),
            types.Tool(
                name="get_presentation",
                description="Retrieves detailed information about a specific presentation.",
                inputSchema={
                    "type": "object",
                    "required": ["presentation_id"],
                    "properties": {
                        "presentation_id": {
                            "type": "string",
                            "description": "The ID of the presentation to retrieve."
                        },
                        "fields": {
                            "type": "string",
                            "description": "Optional field mask to limit the returned data (e.g., 'slides,pageSize')."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_PRESENTATION", "readOnlyHint": True}),
            ),
            types.Tool(
                name="batch_update_presentation",
                description="Applies a series of updates to a presentation. This is the primary method for modifying slides.",
                inputSchema={
                    "type": "object",
                    "required": ["presentation_id", "requests"],
                    "properties": {
                        "presentation_id": {
                            "type": "string",
                            "description": "The ID of the presentation to update."
                        },
                        "requests": {
                            "type": "array",
                            "description": "An array of request objects defining the updates. Refer to the Google Slides API batchUpdate documentation."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_PRESENTATION"}),
            ),
            types.Tool(
                name="summarize_presentation",
                description="Extracts and formats all text content from a presentation for easier summarization.",
                inputSchema={
                    "type": "object",
                    "required": ["presentation_id"],
                    "properties": {
                        "presentation_id": {
                            "type": "string",
                            "description": "The ID of the presentation to summarize."
                        },
                        "include_notes": {
                            "type": "boolean",
                            "description": "Whether to include speaker notes in the summary."
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_SLIDES_PRESENTATION", "readOnlyHint": True}),
            )
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context

        if name == "create_presentation":
            title = arguments.get("title")
            
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'title' parameter is required"
                    )
                ]
            
            try:
                result = await create_presentation(title)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
                
        elif name == "add_slide":
            presentation_id = arguments.get("presentation_id")
            title = arguments.get("title")
            content = arguments.get("content")
            
            if not presentation_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'presentation_id' parameter is required"
                    )
                ]
            
            try:
                result = await add_slide(presentation_id, title, content)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
                
        elif name == "list_presentations":
            try:
                result = await list_presentations()
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
        
        elif name == "get_presentation":
            presentation_id = arguments.get("presentation_id")
            fields = arguments.get("fields")
            
            if not presentation_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'presentation_id' parameter is required"
                    )
                ]
            
            try:
                result = await get_presentation(presentation_id, fields)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
        
        elif name == "batch_update_presentation":
            presentation_id = arguments.get("presentation_id")
            requests = arguments.get("requests")
            
            if not presentation_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'presentation_id' parameter is required"
                    )
                ]
            
            if not requests:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'requests' parameter is required"
                    )
                ]
            
            try:
                result = await batch_update_presentation(presentation_id, requests)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
        
        elif name == "summarize_presentation":
            presentation_id = arguments.get("presentation_id")
            include_notes = arguments.get("include_notes", False)
            
            if not presentation_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'presentation_id' parameter is required"
                    )
                ]
            
            try:
                result = await summarize_presentation(presentation_id, include_notes)
                return [
                    types.TextContent(
                        type="text",
                        text=result
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]

        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
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
