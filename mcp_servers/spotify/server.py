# server.py
import contextlib
import logging
import os
import json
import sys
from typing import List, Optional
from contextvars import ContextVar
from collections.abc import AsyncIterator

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

# your existing imports
from pydantic import BaseModel, Field
from spotipy import SpotifyException

from tools import spotify_api
from tools.utils import normalize_redirect_uri

load_dotenv()

# -------------------------
# Keep your existing logger + client setup
# -------------------------
def setup_logger():
    class Logger:
        def info(self, message):
            print(f"[INFO] {message}", file=sys.stderr)

        def error(self, message):
            print(f"[ERROR] {message}", file=sys.stderr)

    return Logger()

logger = setup_logger()

# Normalize redirect uri if provided in spotify_api
if spotify_api.REDIRECT_URI:
    spotify_api.REDIRECT_URI = normalize_redirect_uri(spotify_api.REDIRECT_URI)
spotify_client = spotify_api.Client(logger)

# -------------------------
# MCP Server and tool models
# -------------------------
server = Server("spotify-mcp-server")


class ToolModel(BaseModel):
    @classmethod
    def as_tool(cls):
        return types.Tool(
            name="Spotify" + cls.__name__,
            description=cls.__doc__,
            inputSchema=cls.model_json_schema()
        )


class Playback(ToolModel):
    """Manages the current playback with the following actions:
    - get: Get information about user's current track.
    - start: Starts playing new item or resumes current playback if called with no uri.
    - pause: Pauses current playback.
    - skip: Skips current track.
    """
    action: str = Field(description="Action to perform: 'get', 'start', 'pause' or 'skip'.")
    spotify_uri: Optional[str] = Field(default=None, description="Spotify uri of item to play for 'start' action. If omitted, resumes current playback.")
    num_skips: Optional[int] = Field(default=1, description="Number of tracks to skip for `skip` action.")


class Queue(ToolModel):
    """Manage the playback queue - get the queue or add tracks."""
    action: str = Field(description="Action to perform: 'add' or 'get'.")
    track_id: Optional[str] = Field(default=None, description="Track ID to add to queue (required for add action)")


class GetInfo(ToolModel):
    """Get detailed information about a Spotify item (track, album, artist, or playlist)."""
    item_uri: str = Field(description="URI of the item to get information about. If 'playlist' or 'album', returns its tracks. If 'artist', returns albums and top tracks.")


class Search(ToolModel):
    """Search for tracks, albums, artists, or playlists on Spotify."""
    query: str = Field(description="query term")
    qtype: Optional[str] = Field(default="track", description="Type of items to search for (track, album, artist, playlist, or comma-separated combination)")
    limit: Optional[int] = Field(default=10, description="Maximum number of items to return")


class Playlist(ToolModel):
    """Manage Spotify playlists."""
    action: str = Field(description="Action to perform: 'get', 'get_tracks', 'add_tracks', 'remove_tracks', 'change_details'.")
    playlist_id: Optional[str] = Field(default=None, description="ID of the playlist to manage.")
    track_ids: Optional[List[str]] = Field(default=None, description="List of track IDs to add/remove.")
    name: Optional[str] = Field(default=None, description="New name for the playlist.")
    description: Optional[str] = Field(default=None, description="New description for the playlist.")


# Prompts/resources stubs (keep as before)
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return []


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return []


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("Listing available tools")
    tools = [
        Playback.as_tool(),
        Search.as_tool(),
        Queue.as_tool(),
        GetInfo.as_tool(),
        Playlist.as_tool(),
    ]
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    return tools


@server.call_tool()
async def handle_call_tool(
        name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    assert name[:7] == "Spotify", f"Unknown tool: {name}"
    try:
        match name[7:]:
            case "Playback":
                action = arguments.get("action")
                match action:
                    case "get":
                        curr_track = spotify_client.get_current_track()
                        if curr_track:
                            return [types.TextContent(type="text", text=json.dumps(curr_track, indent=2))]
                        return [types.TextContent(type="text", text="No track playing.")]
                    case "start":
                        spotify_client.start_playback(spotify_uri=arguments.get("spotify_uri"))
                        return [types.TextContent(type="text", text="Playback starting.")]
                    case "pause":
                        spotify_client.pause_playback()
                        return [types.TextContent(type="text", text="Playback paused.")]
                    case "skip":
                        num_skips = int(arguments.get("num_skips", 1))
                        spotify_client.skip_track(n=num_skips)
                        return [types.TextContent(type="text", text="Skipped to next track.")]
            case "Search":
                search_results = spotify_client.search(
                    query=arguments.get("query", ""),
                    qtype=arguments.get("qtype", "track"),
                    limit=arguments.get("limit", 10)
                )
                return [types.TextContent(type="text", text=json.dumps(search_results, indent=2))]
            case "Queue":
                action = arguments.get("action")
                match action:
                    case "add":
                        track_id = arguments.get("track_id")
                        if not track_id:
                            return [types.TextContent(type="text", text="track_id is required for add action")]
                        spotify_client.add_to_queue(track_id)
                        return [types.TextContent(type="text", text=f"Track added to queue.")]
                    case "get":
                        queue = spotify_client.get_queue()
                        return [types.TextContent(type="text", text=json.dumps(queue, indent=2))]
                    case _:
                        return [types.TextContent(type="text", text=f"Unknown queue action: {action}. Supported actions are: add, remove, and get.")]
            case "GetInfo":
                item_info = spotify_client.get_info(item_uri=arguments.get("item_uri"))
                return [types.TextContent(type="text", text=json.dumps(item_info, indent=2))]
            case "Playlist":
                action = arguments.get("action")
                match action:
                    case "get":
                        playlists = spotify_client.get_current_user_playlists()
                        return [types.TextContent(type="text", text=json.dumps(playlists, indent=2))]
                    case "get_tracks":
                        if not arguments.get("playlist_id"):
                            return [types.TextContent(type="text", text="playlist_id is required for get_tracks action.")]
                        tracks = spotify_client.get_playlist_tracks(arguments.get("playlist_id"))
                        return [types.TextContent(type="text", text=json.dumps(tracks, indent=2))]
                    case "add_tracks":
                        track_ids = arguments.get("track_ids")
                        if isinstance(track_ids, str):
                            try:
                                track_ids = json.loads(track_ids)
                            except json.JSONDecodeError:
                                return [types.TextContent(type="text", text="Error: track_ids must be a list or a valid JSON array.")]
                        spotify_client.add_tracks_to_playlist(playlist_id=arguments.get("playlist_id"), track_ids=track_ids)
                        return [types.TextContent(type="text", text="Tracks added to playlist.")]
                    case "remove_tracks":
                        track_ids = arguments.get("track_ids")
                        if isinstance(track_ids, str):
                            try:
                                track_ids = json.loads(track_ids)
                            except json.JSONDecodeError:
                                return [types.TextContent(type="text", text="Error: track_ids must be a list or a valid JSON array.")]
                        spotify_client.remove_tracks_from_playlist(playlist_id=arguments.get("playlist_id"), track_ids=track_ids)
                        return [types.TextContent(type="text", text="Tracks removed from playlist.")]
                    case "change_details":
                        if not arguments.get("playlist_id"):
                            return [types.TextContent(type="text", text="playlist_id is required for change_details action.")]
                        if not arguments.get("name") and not arguments.get("description"):
                            return [types.TextContent(type="text", text="At least one of name, description, public, or collaborative is required.")]
                        spotify_client.change_playlist_details(playlist_id=arguments.get("playlist_id"), name=arguments.get("name"), description=arguments.get("description"))
                        return [types.TextContent(type="text", text="Playlist details changed.")]
                    case _:
                        return [types.TextContent(type="text", text=f"Unknown playlist action: {action}.")]
            case _:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=error_msg)]
    except SpotifyException as se:
        error_msg = f"Spotify Client error occurred: {str(se)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=f"An error occurred with the Spotify Client: {str(se)}")]
    except Exception as e:
        error_msg = f"Unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

# -------------------------
# New: Affinity-style HTTP orchestration (main)
# -------------------------
DEFAULT_PORT = int(os.getenv("SPOTIFY_MCP_SERVER_PORT", "5001"))

@click.command()
@click.option("--port", default=DEFAULT_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--json-response", is_flag=True, default=False, help="Enable JSON responses for StreamableHTTP instead of SSE streams")
def main(port: int, log_level: str, json_response: bool) -> int:
    logging.basicConfig(level=getattr(logging, log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info(f"Starting Spotify MCP server on port {port}")

    # Server instance is already set up via decorators above (server)
    app = server 

    # SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        # extract optional auth header if you plan to support it (keeps parity with Affinity)
        auth_token = request.headers.get('x-auth-token')
        # Set up SSE streams and run MCP server for that connection
        token = None
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())
        finally:
            pass
        return Response()

    # StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(app=app, event_store=None, json_response=json_response, stateless=True)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Spotify application started with StreamableHTTP transport.")
            try:
                yield
            finally:
                logger.info("Spotify application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0


def cli_main():
    """Synchronous entry point for CLI scripts."""
    main()  # click will handle invocation

if __name__ == "__main__":
    main()
