import contextlib
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
    get_spotify_access_token,
    get_spotify_client,
    search_tracks,
    auth_token_context,
    get_tracks_info,
    get_user_spotify_client,
    get_user_saved_tracks,
    check_user_saved_tracks,
    save_tracks_for_current_user,
    remove_user_saved_tracks,
    get_albums_info,
    get_album_tracks,
    get_user_saved_albums,
    save_albums_for_current_user,
    remove_albums_for_current_user,
    check_user_saved_albums,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

SPOTIFY_MCP_SERVER_PORT = int(os.getenv("SPOTIFY_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option(
    "--port", default=SPOTIFY_MCP_SERVER_PORT, help="Port to listen on for HTTP"
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
    app = Server("spotify-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="spotify_search_tracks",
                description="Search on Spotify",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for (track, album, artist, playlist, show, episode)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of search  a track or album or artist or playlist or show or episode",
                            "enum": ["track", "album", "artist", "playlist", "show", "episode"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return (default: 10)",
                            "default": 10
                        },
                        
                    },
                    "required": ["query","type"]
                }
            ),
            types.Tool(
                name="spotify_get_track_info",
                description="Get detailed information about a specific track",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify track IDs to retrieve information for"
                        },
                    },
                    "required": ["ids"]
                }
            ),
            types.Tool(
                name="spotify_get_user_saved_tracks",
                description="Get the user's saved tracks (liked/saved songs) from Spotify",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of tracks to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first track to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="spotify_check_user_saved_tracks",
                description="Check if a track or multiple tracks is saved in the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "track_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify track IDs to check"
                        },
                    },
                    "required": ["track_ids"]
                }
            ),
            types.Tool(
                name="spotify_save_tracks_for_current_user",
                description="Save tracks to the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "track_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify track IDs to save"
                        },
                    },
                    "required": ["track_ids"]
                }
            ),
            types.Tool(
                name="spotify_remove_user_saved_tracks",
                description="Remove tracks from the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "track_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify track IDs to remove"
                        },
                    },
                    "required": ["track_ids"]
                }
            ),
            types.Tool(
                name="spotify_get_albums_info",
                description="Get detailed information about one or multiple albums",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "album_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify album IDs to retrieve information for"
                        },
                    },
                    "required": ["album_ids"]
                }
            ),
            types.Tool(
                name="spotify_get_album_tracks",
                description="Get detailed information about tracks in a specific album",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "album_id": {
                            "type": "string",
                            "description": "Spotify album ID to retrieve tracks for"
                        },
                    },
                    "required": ["album_id"]
                }
            ),
            types.Tool(
                name="spotify_get_user_saved_albums",
                description="Get the user's saved albums from Spotify",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of albums to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first album to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="spotify_save_albums_for_current_user",
                description="Save albums to the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "album_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify album IDs to save"
                        },
                    },
                    "required": ["album_ids"]
                }
            ),
            types.Tool(
                name="spotify_remove_albums_for_current_user",
                description="Remove albums from the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "album_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify album IDs to remove"
                        },
                    },
                    "required": ["album_ids"]
                }
            ),
            types.Tool(
                name="spotify_check_user_saved_albums",
                description="Check if an album or multiple albums is saved in the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "album_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify album IDs to check"
                        },
                    },
                    "required": ["album_ids"]
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Tool called: {name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
        
        
        token =  get_spotify_access_token()
        sp= get_spotify_client()
        spOauth,user_token = get_user_spotify_client()
        if name == "spotify_search_tracks":
            query = arguments.get("query", "")
            type= arguments.get("type","")
            limit = arguments.get("limit", 10)
            logger.info(f"Searching tracks with query: {query}, type: {type}, limit: {limit}")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Query parameter is required for search.",
                    )
                ]
            
            
    
            result = search_tracks(query, type,limit,sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            return result
        elif name == "spotify_get_track_info":
            track_ids = arguments.get("ids", "")
            logger.info(f"Getting track info for track_id: {track_ids}")
            if not track_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ID parameter is required to get track information.",
                    )
                ]
    
            result = get_tracks_info(track_ids, sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_user_saved_tracks":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user saved tracks with limit: {limit}, offset: {offset}")
            
            result = get_user_saved_tracks(spOauth, limit, offset)
            logger.info(f"User saved tracks result: {result}")
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_check_user_saved_tracks":
            track_ids = arguments.get("track_ids", [])
            logger.info(f"Checking user saved tracks for IDs: {track_ids}")
            if not track_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="track_ids parameter is required to check saved tracks.",
                    )
                ]
    
            result = check_user_saved_tracks(track_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_save_tracks_for_current_user":
            track_ids = arguments.get("track_ids", [])
            logger.info(f"Saving tracks for current user: {track_ids}")
            if not track_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="track_ids parameter is required to save tracks.",
                    )
                ]
    
            result = save_tracks_for_current_user(track_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_remove_user_saved_tracks":
            track_ids = arguments.get("track_ids", [])
            logger.info(f"Removing tracks for current user: {track_ids}")
            if not track_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="track_ids parameter is required to remove tracks.",
                    )
                ]
    
            result = remove_user_saved_tracks(track_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_albums_info":
            album_ids = arguments.get("album_ids", [])
            logger.info(f"Getting albums info for IDs: {album_ids}")
            if not album_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="album_ids parameter is required to get album information.",
                    )
                ]
    
            result = get_albums_info(album_ids, sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_album_tracks":
            album_id = arguments.get("album_id", "")
            logger.info(f"Getting album tracks for album_id: {album_id}")
            if not album_id:
                return [
                    types.TextContent(
                        type="text",
                        text="album_id parameter is required to get album tracks.",
                    )
                ]
    
            result = get_album_tracks(album_id, sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_user_saved_albums":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user saved albums with limit: {limit}, offset: {offset}")
            
            result = get_user_saved_albums(spOauth, limit, offset)
            logger.info(f"User saved albums result: {result}")
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_save_albums_for_current_user":
            album_ids = arguments.get("album_ids", [])
            logger.info(f"Saving albums for current user: {album_ids}")
            if not album_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="album_ids parameter is required to save albums.",
                    )
                ]
    
            result = save_albums_for_current_user(album_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
            
        elif name == "spotify_remove_albums_for_current_user":
            album_ids = arguments.get("album_ids", [])
            logger.info(f"Removing albums for current user: {album_ids}")
            if not album_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="album_ids parameter is required to remove albums.",
                    )
                ]
    
            result = remove_albums_for_current_user(album_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_check_user_saved_albums":
            album_ids = arguments.get("album_ids", [])
            logger.info(f"Checking user saved albums for IDs: {album_ids}")
            if not album_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="album_ids parameter is required to check saved albums.",
                    )
                ]
    
            result = check_user_saved_albums(album_ids, spOauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
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