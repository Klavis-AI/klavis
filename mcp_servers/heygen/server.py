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

from tools import (
    auth_token_context,
    heygen_get_remaining_credits,
    heygen_get_voices, heygen_get_voice_locales, heygen_get_avatar_groups, heygen_get_avatars_in_avatar_group, heygen_list_avatars,
    heygen_generate_avatar_video, heygen_get_avatar_video_status,
    heygen_list_videos, heygen_delete_video
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

HEYGEN_MCP_SERVER_PORT = int(os.getenv("HEYGEN_MCP_SERVER_PORT", "5000"))

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""

@click.command()
@click.option("--port", default=HEYGEN_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("heygen-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Account Management
            types.Tool(
                name="heygen_get_remaining_credits",
                description="Retrieve the remaining credits in your HeyGen account.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_ACCOUNT", "readOnlyHint": True}),
            ),
            # Assets - Voices
            types.Tool(
                name="heygen_get_voices",
                description="Retrieve a list of available voices from the HeyGen API.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of voices to return (default: 20, max: 100).",
                            "default": 20,
                            "maximum": 100,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VOICE", "readOnlyHint": True}),
            ),
            types.Tool(
                name="heygen_get_voice_locales",
                description="Retrieve a list of available voice locales (languages) from the HeyGen API.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of voice locales to return (default: 20).",
                            "default": 20,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VOICE", "readOnlyHint": True}),
            ),
            # Assets - Avatars
            types.Tool(
                name="heygen_get_avatar_groups",
                description="Retrieve a list of HeyGen avatar groups.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_AVATAR", "readOnlyHint": True}),
            ),
            types.Tool(
                name="heygen_get_avatars_in_avatar_group",
                description="Retrieve a list of avatars in a specific HeyGen avatar group.",
                inputSchema={
                    "type": "object",
                    "required": ["group_id"],
                    "properties": {
                        "group_id": {
                            "type": "string",
                            "description": "The ID of the avatar group.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_AVATAR", "readOnlyHint": True}),
            ),
            types.Tool(
                name="heygen_list_avatars",
                description="Retrieve a list of all available avatars from the HeyGen API. This includes your instant avatars and public avatars.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of avatars to return (default: 20).",
                            "default": 20,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_AVATAR", "readOnlyHint": True}),
            ),
            # Generation
            types.Tool(
                name="heygen_generate_avatar_video",
                description="Generate a new avatar video with the specified avatar, text, and voice.",
                inputSchema={
                    "type": "object",
                    "required": ["avatar_id", "text", "voice_id"],
                    "properties": {
                        "avatar_id": {
                            "type": "string",
                            "description": "The ID of the avatar to use.",
                        },
                        "text": {
                            "type": "string",
                            "description": "The text for the avatar to speak (max 1500 characters).",
                            "maxLength": 1500,
                        },
                        "voice_id": {
                            "type": "string",
                            "description": "The ID of the voice to use.",
                        },
                        "background_color": {
                            "type": "string",
                            "description": "Background color in hex format (default: #ffffff).",
                            "default": "#ffffff",
                        },
                        "width": {
                            "type": "integer",
                            "description": "Video width in pixels (default: 1280).",
                            "default": 1280,
                        },
                        "height": {
                            "type": "integer",
                            "description": "Video height in pixels (default: 720).",
                            "default": 720,
                        },
                        "avatar_style": {
                            "type": "string",
                            "description": "Avatar style (default: normal).",
                            "default": "normal",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VIDEO"}),
            ),
            types.Tool(
                name="heygen_get_avatar_video_status",
                description="Retrieve the status of a video generated via the HeyGen API.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The ID of the video to check status for.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VIDEO", "readOnlyHint": True}),
            ),
            # Management
            types.Tool(
                name="heygen_list_videos",
                description="Retrieve a list of videos from your HeyGen account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 20).",
                            "default": 20,
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of videos to skip (default: 0).",
                            "default": 0,
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VIDEO", "readOnlyHint": True}),
            ),
            types.Tool(
                name="heygen_delete_video",
                description="Delete a video from your HeyGen account.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The ID of the video to delete.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "HEYGEN_VIDEO"}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        # Account Management
        if name == "heygen_get_remaining_credits":
            try:
                result = await heygen_get_remaining_credits()
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
        
        # Assets - Voices
        elif name == "heygen_get_voices":
            limit = arguments.get("limit", 20)
            
            try:
                result = await heygen_get_voices(limit)
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
        
        elif name == "heygen_get_voice_locales":
            limit = arguments.get("limit", 20)
            
            try:
                result = await heygen_get_voice_locales(limit)
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
        
        # Assets - Avatars
        elif name == "heygen_get_avatar_groups":
            try:
                result = await heygen_get_avatar_groups()
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
        
        elif name == "heygen_get_avatars_in_avatar_group":
            group_id = arguments.get("group_id")
            if not group_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: group_id parameter is required",
                    )
                ]
            
            try:
                result = await heygen_get_avatars_in_avatar_group(group_id)
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
        
        elif name == "heygen_list_avatars":
            limit = arguments.get("limit", 20)
            
            try:
                result = await heygen_list_avatars(limit)
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
        
        # Generation
        elif name == "heygen_generate_avatar_video":
            avatar_id = arguments.get("avatar_id")
            text = arguments.get("text")
            voice_id = arguments.get("voice_id")
            
            if not avatar_id or not text or not voice_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: avatar_id, text, and voice_id parameters are required",
                    )
                ]
            
            background_color = arguments.get("background_color", "#ffffff")
            width = arguments.get("width", 1280)
            height = arguments.get("height", 720)
            avatar_style = arguments.get("avatar_style", "normal")
            
            try:
                result = await heygen_generate_avatar_video(
                    avatar_id, text, voice_id, background_color, width, height, avatar_style
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
        
        elif name == "heygen_get_avatar_video_status":
            video_id = arguments.get("video_id")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await heygen_get_avatar_video_status(video_id)
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
        
        # Management
        elif name == "heygen_list_videos":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            
            try:
                result = await heygen_list_videos(limit, offset)
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
        
        elif name == "heygen_delete_video":
            video_id = arguments.get("video_id")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await heygen_delete_video(video_id)
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
        
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Create transport managers
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )
    sse = SseServerTransport("/messages", app)

    async def handle_sse(request):
        async def sse_handler(scope: Scope, receive: Receive, send: Send) -> None:
            # Extract auth token from headers (allow None - will be handled at tool level)
            auth_token = extract_api_key(request)
            
            # Set the auth token in context for this request (can be None/empty)
            token = auth_token_context.set(auth_token or "")
            try:
                await sse.handle_sse(scope, receive, send)
            finally:
                auth_token_context.reset(token)

        return Response(content="", media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        })

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        # Extract auth token from headers (allow None - will be handled at tool level)
        auth_token = extract_api_key(scope)
        
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