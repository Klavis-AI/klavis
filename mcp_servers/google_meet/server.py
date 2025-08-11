import contextlib
import logging
import os
import json
from typing import Any, Dict
from contextvars import ContextVar
import re

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
import requests

logger = logging.getLogger(__name__)

load_dotenv()

SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

auth_token_context: ContextVar[str] = ContextVar('auth_token')
# We're using a ContextVar here to store the auth token for each async request. This way, even if requests overlap, each one gets its own token without mixing them up.

def get_auth_token() -> str:
    # Grab the token from the current context, clean it up, and check if it's valid. If something's wrong, we throw an error to stop things early.
    try:
        token = auth_token_context.get()
        token = token.strip()
        if not token:
            raise RuntimeError("Missing OAuth access token. Pass a valid token in the x-auth-token header.")
        if len(token) < 10:
            raise RuntimeError("Invalid access token format. Token is too short.")
        if len(token) > 4096:
            raise RuntimeError("Invalid access token format. Token is too long.")
        if not all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~:/?#[]@!$&'()*+,;=" for c in token):
            raise RuntimeError("Invalid access token format. Token contains invalid characters.")
        return token
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

async def create_meeting(args: Dict[str, Any]) -> Dict[str, Any]:
    # This function creates a new meeting space by calling the Google Meet API. We send an empty body because Meet doesn't need extra details for basic creation.
    access_token = get_auth_token()
    try:
        response = requests.post(
            'https://meet.googleapis.com/v2/spaces',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={}
        )
        response.raise_for_status()
        space = response.json()
        if 'name' not in space or 'meetingUri' not in space:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'space_id': space['name'],
            'meet_link': space['meetingUri'],
            'space': space
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to create meeting space: {e.response.status_code if e.response else ''} {e}")

async def get_meeting_details(args: Dict[str, Any]) -> Dict[str, Any]:
    access_token = get_auth_token()
    space_id = args.get('space_id')
    if not space_id or not isinstance(space_id, str) or len(space_id) < 1 or len(space_id) > 1000 or not bool(re.match(r'^spaces/[a-zA-Z0-9\-_]+$', space_id)):
        raise ValueError('Invalid space_id')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(space_id)}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        space = response.json()
        if 'name' not in space or 'meetingUri' not in space:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'space_id': space['name'],
            'meet_link': space['meetingUri'],
            'space': space
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get meeting space: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")

async def get_past_meetings(args: Dict[str, Any]) -> Dict[str, Any]:
    access_token = get_auth_token()
    params = {}
    page_size = args.get('page_size', 10)
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise ValueError('Invalid page_size')
    params['pageSize'] = page_size
    if 'page_token' in args:
        page_token = args['page_token']
        if isinstance(page_token, str) and len(page_token) <= 5000:
            params['pageToken'] = page_token
        else:
            raise ValueError('Invalid page_token')
    if 'filter' in args:
        filter_expr = args['filter']
        if isinstance(filter_expr, str) and len(filter_expr) <= 2000:
            params['filter'] = filter_expr
        else:
            raise ValueError('Invalid filter')
    try:
        response = requests.get(
            'https://meet.googleapis.com/v2/conferenceRecords',
            params=params,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        data = response.json()
        conference_records = data.get('conferenceRecords', [])
        return {
            'conference_records': conference_records,
            'next_page_token': data.get('nextPageToken')
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list conference records: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")

async def get_past_meeting_details(args: Dict[str, Any]) -> Dict[str, Any]:
    access_token = get_auth_token()
    conference_record_id = args.get('conference_record_id')
    if not conference_record_id or not isinstance(conference_record_id, str) or len(conference_record_id) < 1 or len(conference_record_id) > 1000 or not bool(re.match(r'^conferenceRecords/[a-zA-Z0-9\-_]+$', conference_record_id)):
        raise ValueError('Invalid conference_record_id')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(conference_record_id)}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        record = response.json()
        if 'name' not in record:
            raise ValueError('Invalid response from Google Meet API: missing required fields')
        return {
            'conference_record_id': record['name'],
            'record': record
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get conference record: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")

async def get_past_meeting_participants(args: Dict[str, Any]) -> Dict[str, Any]:
    access_token = get_auth_token()
    conference_record_id = args.get('conference_record_id')
    if not conference_record_id or not isinstance(conference_record_id, str) or len(conference_record_id) < 1 or len(conference_record_id) > 1000 or not bool(re.match(r'^conferenceRecords/[a-zA-Z0-9\-_]+$', conference_record_id)):
        raise ValueError('Invalid conference_record_id')
    params = {}
    page_size = args.get('page_size', 10)
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise ValueError('Invalid page_size')
    params['pageSize'] = page_size
    if 'page_token' in args:
        page_token = args['page_token']
        if isinstance(page_token, str) and len(page_token) <= 5000:
            params['pageToken'] = page_token
        else:
            raise ValueError('Invalid page_token')
    if 'filter' in args:
        filter_expr = args['filter']
        if isinstance(filter_expr, str) and len(filter_expr) <= 2000:
            params['filter'] = filter_expr
        else:
            raise ValueError('Invalid filter')
    try:
        response = requests.get(
            f'https://meet.googleapis.com/v2/{requests.utils.quote(conference_record_id)}/participants',
            params=params,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        data = response.json()
        participants = data.get('participants', [])
        return {
            'participants': participants,
            'next_page_token': data.get('nextPageToken'),
            'participant_count': len(participants)
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to list participants: {e.response.status_code if e.response else ''} {e.response.text if e.response else str(e)}")

@click.command()
@click.option("--port", default=SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    # Set up basic logging so we can see what's happening at the level we choose.
    logging.basicConfig(level=getattr(logging, log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # This is the core MCP server object that handles tool listing and calls.
    app = Server("google-meet-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        # Define all the tools available in this server. Each tool has a name, description, and input schema for validation.
        return [
            types.Tool(
                name="create_meeting",
                description="Create a new meeting",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="get_meeting_details",
                description="Get details of a meeting",
                inputSchema={
                    "type": "object",
                    "required": ["space_id"],
                    "properties": {
                        "space_id": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1000,
                            "pattern": "^spaces/[a-zA-Z0-9\\-_]+$",
                            "description": "Meeting space ID (spaces/{space-id})"
                        }
                    }
                },
            ),
            types.Tool(
                name="get_past_meetings",
                description="Get details for completed meetings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of records to return"},
                        "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                        "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                    }
                },
            ),
            types.Tool(
                name="get_past_meeting_details",
                description="Get details of a specific meeting",
                inputSchema={
                    "type": "object",
                    "required": ["conference_record_id"],
                    "properties": {
                        "conference_record_id": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1000,
                            "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                            "description": "Conference record ID (conferenceRecords/{record-id})"
                        }
                    }
                },
            ),
            types.Tool(
                name="get_past_meeting_participants",
                description="Get a list of participants from a past meeting",
                inputSchema={
                    "type": "object",
                    "required": ["conference_record_id"],
                    "properties": {
                        "conference_record_id": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1000,
                            "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                            "description": "Conference record ID (conferenceRecords/{record-id})"
                        },
                        "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of participants to return"},
                        "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                        "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                    }
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        # This is where we route the tool calls. Based on the name, we call the right function and return the result as text.
        try:
            if name == "create_meeting":
                result = await create_meeting(arguments)
                return [types.TextContent(type="text", text=json.dumps(result))]
            elif name == "get_meeting_details":
                result = await get_meeting_details(arguments)
                return [types.TextContent(type="text", text=json.dumps(result))]
            elif name == "get_past_meetings":
                result = await get_past_meetings(arguments)
                return [types.TextContent(type="text", text=json.dumps(result))]
            elif name == "get_past_meeting_details":
                result = await get_past_meeting_details(arguments)
                return [types.TextContent(type="text", text=json.dumps(result))]
            elif name == "get_past_meeting_participants":
                result = await get_past_meeting_participants(arguments)
                return [types.TextContent(type="text", text=json.dumps(result))]
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        # For SSE requests, we grab the token from headers, set it in context, and run the app with SSE transport.
        auth_token = request.headers.get('x-auth-token')
        token = auth_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            auth_token_context.reset(token)
        return Response()

    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        # Similar to SSE, but for HTTP: extract token from headers, set context, and handle the request.
        headers = scope.get("headers", [])
        auth_token = next((v.decode('utf-8') for k, v in headers if k == b'x-auth-token'), None)
        token = auth_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> None:
        # This manages the app's lifetime: starts the session manager, logs startup, yields control, then shuts down.
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            yield
            logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
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
