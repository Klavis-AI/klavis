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
    get_artists_info,
    get_artist_albums,
    get_artist_top_tracks,
    get_episodes_info,
    save_episodes_for_current_user,
    get_user_saved_episodes,
    remove_episodes_for_current_user,
    check_user_saved_episodes,
    get_playlist_by_id,
    get_user_owned_playlists,
    update_playlist_details,
    get_current_user_profile,
    get_current_user_top_items,
    get_spotify_user_public_profile,
    follow_playlist,
    unfollow_playlist,
    get_current_user_followed_artists,
    follow_artists_or_users,
    unfollow_artists_or_users,
    check_user_follows,
    add_items_to_playlist,
    remove_items_from_playlist,
    get_current_user_playlists,
    get_multiple_shows,
    get_show_episodes,
    get_current_user_saved_shows,
    save_shows_to_user_library,
    remove_shows_from_user_library,
    check_user_saved_shows,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

SPOTIFY_MCP_SERVER_PORT = int(os.getenv("SPOTIFY_MCP_SERVER_PORT", "5000"))


@click.command()
@click.option(
    "--port", 
    default=SPOTIFY_MCP_SERVER_PORT, 
    help="Port to listen on for HTTP"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams"
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
                description="Search for tracks, albums, artists, playlists, shows or episodes on Spotify",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for (track, album, artist, playlist, show, episode)"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of search: track, album, artist, playlist, show, episode, or audiobook",
                            "enum": ["track", "album", "artist", "playlist", "show", "episode", "audiobook"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query", "type"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK", "readOnlyHint": True})
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
                        }
                    },
                    "required": ["ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK", "readOnlyHint": True})
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
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK", "readOnlyHint": True})
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
                        }
                    },
                    "required": ["track_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK", "readOnlyHint": True})
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
                        }
                    },
                    "required": ["track_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK"})
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
                        }
                    },
                    "required": ["track_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_TRACK"})
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
                        }
                    },
                    "required": ["album_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM", "readOnlyHint": True})
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
                        }
                    },
                    "required": ["album_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM", "readOnlyHint": True})
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
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM", "readOnlyHint": True})
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
                        }
                    },
                    "required": ["album_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM"})
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
                        }
                    },
                    "required": ["album_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM"})
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
                        }
                    },
                    "required": ["album_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ALBUM", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_artists_info",
                description="Get detailed information about one or multiple artists",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "artist_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify artist IDs to retrieve information for"
                        }
                    },
                    "required": ["artist_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ARTIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_artist_albums",
                description="Get detailed information about albums by a specific artist",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "artist_id": {
                            "type": "string",
                            "description": "Spotify artist ID to retrieve albums for"
                        }
                    },
                    "required": ["artist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ARTIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_artist_top_tracks",
                description="Get the top tracks of a specific artist by country",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "artist_id": {
                            "type": "string",
                            "description": "Spotify artist ID to retrieve top tracks for"
                        },
                        "country": {
                            "type": "string",
                            "description": "2-letter country code (e.g., 'US', 'GB', 'IN')"
                        }
                    },
                    "required": ["artist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_ARTIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_episodes_info",
                description="Get detailed information about one or multiple podcast episodes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "episode_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify episode IDs to retrieve information for"
                        },
                        "market": {
                            "type": "string",
                            "description": "Country market to restrict results (ISO 3166-1 alpha-2, default: None)",
                            "default": None
                        }
                    },
                    "required": ["episode_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_EPISODE", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_save_episodes_for_current_user",
                description="Save podcast episodes to the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "episode_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify episode IDs to save"
                        }
                    },
                    "required": ["episode_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_EPISODE"})
            ),
            types.Tool(
                name="spotify_get_user_saved_episodes",
                description="Get the user's saved podcast episodes from Spotify",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of episodes to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first episode to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_EPISODE", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_remove_episodes_for_current_user",
                description="Remove podcast episodes from the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "episode_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify episode IDs to remove"
                        }
                    },
                    "required": ["episode_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_EPISODE"})
            ),
            types.Tool(
                name="spotify_check_user_saved_episodes",
                description="Check if a podcast episode or multiple episodes is saved in the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "episode_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify episode IDs to check"
                        }
                    },
                    "required": ["episode_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_EPISODE", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_playlist_by_id",
                description="Get a Spotify playlist's full metadata and contents by its Spotify ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to retrieve"
                        },
                        "market": {
                            "type": "string",
                            "description": "Country market to restrict results (ISO 3166-1 alpha-2, default: None)",
                            "default": None
                        }
                    },
                    "required": ["playlist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_user_owned_playlists",
                description="Get playlists owned by a specific user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Spotify user ID to retrieve owned playlists for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max number of playlists to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first playlist to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": ["user_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_update_playlist_details",
                description="Change a playlist's name and/or public/private state",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the playlist (optional)"
                        },
                        "public": {
                            "type": "boolean",
                            "description": "Set to true to make the playlist public, false for private (optional)"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the playlist (optional)"
                        }
                    },
                    "required": ["playlist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST"})
            ),
            types.Tool(
                name="spotify_get_current_user_profile",
                description="Get the current authenticated user's profile information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_current_user_top_items",
                description="Get the current user's top artists or tracks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_type": {
                            "type": "string",
                            "description": "Type of items to retrieve (artists or tracks)",
                            "enum": ["artists", "tracks"]
                        },
                        "time_range": {
                            "type": "string",
                            "description": "Time range for top items (short_term, medium_term, long_term)",
                            "default": "medium_term"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of items to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first item to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": ["item_type"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_spotify_user_public_profile",
                description="Get public profile information about a Spotify user by their user ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Spotify User ID (username) to retrieve public profile for"
                        },
                    },
                    "required": ["user_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_follow_playlist",
                description="Follow a Spotify playlist",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to follow"
                        },
                        "public": {
                            "type": "boolean",
                            "description": "Set to true to make the playlist public, false for private (optional)"
                        }
                    },
                    "required": ["playlist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST"})
            ),
            types.Tool(
                name="spotify_unfollow_playlist",
                description="Unfollow a Spotify playlist",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to unfollow"
                        },
                    },
                    "required": ["playlist_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST"})
            ),
            types.Tool(
                name="spotify_get_current_user_followed_artists",
                description="Get the current user's followed artists",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of artists to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "after": {
                            "type": "string",
                            "description": "Cursor to get the next page of results (optional)"
                        }
                    },
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_follow_artists_or_users",
                description="Follow one or more artists or Spotify users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify artist/user IDs to follow"
                        },
                    },
                    "required": ["ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER"})
            ),
            types.Tool(
                name="spotify_unfollow_artists_or_users",
                description="Unfollow one or more artists or Spotify users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify artist/user IDs to unfollow"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of IDs: 'artist' or 'user'",
                            "enum": ["artist", "user"],
                            "default": "artist"
                        }
                    },
                    "required": ["ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER"})
            ),
            types.Tool(
                name="spotify_check_user_follows",
                description="Check if the current user follows one or more artists or Spotify users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify artist/user IDs to check"
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of IDs: 'artist' or 'user'",
                            "enum": ["artist", "user"],
                            "default": "artist"
                        }
                    },
                    "required": ["ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_USER", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_add_items_to_playlist",
                description="Add items (tracks, episodes) to a Spotify playlist",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to add items to"
                        },
                        "uris": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify URIs (tracks, episodes) to add"
                        },
                        "position": {
                            "type": "integer",
                            "description": "Position in the playlist to insert the items (optional)"
                        }
                    },
                    "required": ["playlist_id", "uris"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST"})
            ),
            types.Tool(
                name="spotify_remove_items_from_playlist",
                description="Remove items (tracks, episodes) from a Spotify playlist",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "Spotify playlist ID to remove items from"
                        },
                        "uris": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify URIs (tracks, episodes) to remove"
                        }
                    },
                    "required": ["playlist_id", "uris"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST"})
            ),
            types.Tool(
                name="spotify_get_current_user_playlists",
                description="Get playlists created by the current authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of playlists to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first playlist to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_PLAYLIST", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_multiple_shows",
                description="Get detailed information about multiple podcast shows",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify show IDs to retrieve information for"
                        },
                    },
                    "required": ["show_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_show_episodes",
                description="Get episodes of a specific podcast show",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_id": {
                            "type": "string",
                            "description": "Spotify show ID to retrieve episodes for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max number of episodes to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first episode to return (for pagination, default: 0)",
                            "default": 0
                        },
                        "market": {
                            "type": "string",
                            "description": "Country market to restrict results (ISO 3166-1 alpha-2, default: None)",
                            "default": None
                        }
                    },
                    "required": ["show_id"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_get_current_user_saved_shows",
                description="Get the current user's saved podcast shows",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of shows to return (default: 20, max: 50)",
                            "default": 20
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Index of the first show to return (for pagination, default: 0)",
                            "default": 0
                        }
                    },
                    "required": []
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW", "readOnlyHint": True})
            ),
            types.Tool(
                name="spotify_save_shows_to_user_library",
                description="Save podcast shows to the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify show IDs to save"
                        },
                    },
                    "required": ["show_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW"})
            ),
            types.Tool(
                name="spotify_remove_shows_from_user_library",
                description="Remove podcast shows from the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify show IDs to remove"
                        },
                    },
                    "required": ["show_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW"})
            ),
            types.Tool(
                name="spotify_check_user_saved_shows",
                description="Check if a podcast show or multiple shows is saved in the user's library",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "show_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Spotify show IDs to check"
                        },
                    },
                    "required": ["show_ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "SPOTIFY_SHOW", "readOnlyHint": True})
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Tool called: {name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")

        token = get_spotify_access_token()
        sp = get_spotify_client()
        sp_oauth, user_token = get_user_spotify_client()

        if name == "spotify_search_tracks":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "")
            limit = arguments.get("limit", 10)
            logger.info(f"Searching tracks with query: {query}, type: {search_type}, limit: {limit}")

            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Query parameter is required for search.",
                    )
                ]

            result = search_tracks(query, search_type, limit, sp)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_user_saved_tracks":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user saved tracks with limit: {limit}, offset: {offset}")

            result = get_user_saved_tracks(sp_oauth, limit, offset)
            logger.info(f"User saved tracks result: {result}")

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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

            result = check_user_saved_tracks(track_ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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

            result = save_tracks_for_current_user(track_ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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

            result = remove_user_saved_tracks(track_ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_user_saved_albums":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user saved albums with limit: {limit}, offset: {offset}")

            result = get_user_saved_albums(sp_oauth, limit, offset)
            logger.info(f"User saved albums result: {result}")

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

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

            result = save_albums_for_current_user(album_ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

            
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
    
            result = remove_albums_for_current_user(album_ids, sp_oauth)
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
    
            result = check_user_saved_albums(album_ids, sp_oauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_artists_info":
            artist_ids = arguments.get("artist_ids", [])
            logger.info(f"Getting artists info for IDs: {artist_ids}")
            if not artist_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="artist_ids parameter is required to get artist information.",
                    )
                ]
            result = get_artists_info(artist_ids, sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_artist_albums":
            artist_id = arguments.get("artist_id", "")
            logger.info(f"Getting artist albums for artist_id: {artist_id}")
            if not artist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="artist_id parameter is required to get artist albums.",
                    )
                ]
            result = get_artist_albums(artist_id, sp)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]

            return result
        elif name == "spotify_get_artist_top_tracks":
            artist_id = arguments.get("artist_id", "")
            country = arguments.get("country", None)
            logger.info(f"Getting artist top tracks for artist_id: {artist_id}, country: {country}")
            if not artist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="artist_id parameter is required to get artist top tracks.",
                    )
                ]
            result = get_artist_top_tracks(artist_id, sp, country)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]

            return result
        elif name == "spotify_get_episodes_info":
            episode_ids = arguments.get("episode_ids", [])
            market = arguments.get("market", None)
            logger.info(f"Getting episodes info for IDs: {episode_ids}, market: {market}")
            if not episode_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="episode_ids parameter is required to get episode information.",
                    )
                ]
            result = get_episodes_info(episode_ids, sp, market)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]

            return result
        elif name == "spotify_save_episodes_for_current_user":
            episode_ids = arguments.get("episode_ids", [])
            logger.info(f"Saving episodes for current user: {episode_ids}")
            if not episode_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="episode_ids parameter is required to save episodes.",
                    )
                ]
            result = save_episodes_for_current_user(episode_ids, sp_oauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            return result
        elif name == "spotify_get_user_saved_episodes":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user saved episodes with limit: {limit}, offset: {offset}")
            
            result = get_user_saved_episodes(sp_oauth, limit, offset)
            logger.info(f"User saved episodes result: {result}")
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_remove_episodes_for_current_user":
            episode_ids = arguments.get("episode_ids", [])
            logger.info(f"Removing episodes for current user: {episode_ids}")
            if not episode_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="episode_ids parameter is required to remove episodes.",
                    )
                ]
    
            result = remove_episodes_for_current_user(episode_ids, sp_oauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_check_user_saved_episodes":
            episode_ids = arguments.get("episode_ids", [])
            logger.info(f"Checking user saved episodes for IDs: {episode_ids}")
            if not episode_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="episode_ids parameter is required to check saved episodes.",
                    )
                ]
    
            result = check_user_saved_episodes(episode_ids, sp_oauth)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_playlist_by_id":
            playlist_id = arguments.get("playlist_id", "")
            market = arguments.get("market", None)
            logger.info(f"Getting playlist by ID: {playlist_id}, market: {market}")
            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to get playlist information.",
                    )
                ]
    
            result = get_playlist_by_id(playlist_id, sp, market)
            result = [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
            
            return result
        elif name == "spotify_get_user_owned_playlists":
            user_id = arguments.get("user_id", "")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting user owned playlists for user_id: {user_id}, limit: {limit}, offset: {offset}")

            if not user_id:
                return [
                    types.TextContent(
                        type="text",
                        text="user_id parameter is required to get owned playlists.",
                    )
                ]

            result = get_user_owned_playlists(user_id, sp, limit, offset)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_update_playlist_details":
            playlist_id = arguments.get("playlist_id", "")
            name = arguments.get("name", None)
            public = arguments.get("public", None)
            description = arguments.get("description", None)
            logger.info(
                f"Updating playlist details for playlist_id: {playlist_id}, "
                f"name: {name}, public: {public}, description: {description}"
            )

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to update playlist details.",
                    )
                ]

            result = update_playlist_details(playlist_id, name, public, description, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_current_user_profile":
            logger.info("Getting current user profile")

            result = get_current_user_profile(sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_current_user_top_items":
            item_type = arguments.get("item_type", "artists")
            time_range = arguments.get("time_range", "medium_term")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(
                f"Getting current user top items: type={item_type}, "
                f"time_range={time_range}, limit={limit}, offset={offset}"
            )

            result = get_current_user_top_items(sp_oauth, item_type, time_range, limit, offset)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_spotify_user_public_profile":
            user_id = arguments.get("user_id", "")
            logger.info(f"Getting public profile for user_id: {user_id}")

            if not user_id:
                return [
                    types.TextContent(
                        type="text",
                        text="user_id parameter is required to get public profile.",
                    )
                ]

            result = get_spotify_user_public_profile(user_id, sp)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_follow_playlist":
            playlist_id = arguments.get("playlist_id", "")
            public = arguments.get("public", None)
            logger.info(f"Following playlist with ID: {playlist_id}, public: {public}")

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to follow a playlist.",
                    )
                ]

            result = follow_playlist(playlist_id, public, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_unfollow_playlist":
            playlist_id = arguments.get("playlist_id", "")
            logger.info(f"Unfollowing playlist with ID: {playlist_id}")

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to unfollow a playlist.",
                    )
                ]

            result = unfollow_playlist(playlist_id, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_current_user_followed_artists":
            limit = arguments.get("limit", 20)
            after = arguments.get("after", None)
            logger.info(f"Getting followed artists with limit: {limit}, after: {after}")

            result = get_current_user_followed_artists(sp_oauth, limit, after)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_follow_artists_or_users":
            ids = arguments.get("ids", [])
            logger.info(f"Following artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to follow artists or users.",
                    )
                ]

            result = follow_artists_or_users(ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_unfollow_artists_or_users":
            ids = arguments.get("ids", [])
            type_ = arguments.get("type", "artist")  # or "user"
            logger.info(f"Unfollowing artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to unfollow artists or users.",
                    )
                ]

            result = unfollow_artists_or_users(ids, type_, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_check_user_follows":
            ids = arguments.get("ids", [])
            type_ = arguments.get("type", "artist")  # or "user"
            logger.info(f"Checking if user follows artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to check follows.",
                    )
                ]

            result = check_user_follows(ids, type_, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_add_items_to_playlist":
            playlist_id = arguments.get("playlist_id", "")
            uris = arguments.get("uris", [])
            position = arguments.get("position", None)
            logger.info(f"Adding items to playlist: {playlist_id}, uris: {uris}, position: {position}")

            if not playlist_id or not uris:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id and uris parameters are required to add items to a playlist.",
                    )
                ]

            result = add_items_to_playlist(playlist_id, uris, sp_oauth, position)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_remove_items_from_playlist":
            playlist_id = arguments.get("playlist_id", "")
            uris = arguments.get("uris", [])
            logger.info(f"Removing items from playlist: {playlist_id}, uris: {uris}")

            if not playlist_id or not uris:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id and uris parameters are required to remove items from a playlist.",
                    )
                ]

            result = remove_items_from_playlist(playlist_id, uris, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_current_user_playlists":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting current user playlists with limit: {limit}, offset: {offset}")

            result = get_current_user_playlists(sp_oauth, limit, offset)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_multiple_shows":
            show_ids = arguments.get("show_ids", [])
            logger.info(f"Getting multiple shows for IDs: {show_ids}")

            if not show_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="show_ids parameter is required to get multiple shows.",
                    )
                ]

            result = get_multiple_shows(show_ids, sp)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_show_episodes":
            show_id = arguments.get("show_id", "")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            market = arguments.get("market", "US")
            logger.info(
                f"Getting episodes for show_id: {show_id}, limit: {limit}, "
                f"offset: {offset}, market: {market}"
            )

            if not show_id:
                return [
                    types.TextContent(
                        type="text",
                        text="show_id parameter is required to get show episodes.",
                    )
                ]

            result = get_show_episodes(show_id, sp, limit, offset, market)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]

        elif name == "spotify_get_current_user_saved_shows":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting current user saved shows with limit: {limit}, offset: {offset}")

            result = get_current_user_saved_shows(sp_oauth, limit, offset)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "spotify_save_shows_to_user_library":
            show_ids = arguments.get("show_ids", [])
            logger.info(f"Saving shows to user library: {show_ids}")

            if not show_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="show_ids parameter is required to save shows.",
                    )
                ]

            result = save_shows_to_user_library(show_ids, sp_oauth)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
                )
            ]
        elif name == "spotify_get_user_owned_playlists":
            user_id = arguments.get("user_id", "")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(
                f"Getting user owned playlists for user_id: {user_id}, "
                f"limit: {limit}, offset: {offset}"
            )

            if not user_id:
                return [
                    types.TextContent(
                        type="text",
                        text="user_id parameter is required to get owned playlists.",
                    )
                ]

            result = get_user_owned_playlists(user_id, sp, limit, offset)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_update_playlist_details":
            playlist_id = arguments.get("playlist_id", "")
            name = arguments.get("name", None)
            public = arguments.get("public", None)
            description = arguments.get("description", None)
            logger.info(
                f"Updating playlist details for playlist_id: {playlist_id}, "
                f"name: {name}, public: {public}, description: {description}"
            )

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to update playlist details.",
                    )
                ]

            result = update_playlist_details(playlist_id, name, public, description, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_current_user_profile":
            logger.info("Getting current user profile")

            result = get_current_user_profile(sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_current_user_top_items":
            item_type = arguments.get("item_type", "artists")
            time_range = arguments.get("time_range", "medium_term")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(
                f"Getting current user top items: type={item_type}, "
                f"time_range={time_range}, limit={limit}, offset={offset}"
            )

            result = get_current_user_top_items(sp_oauth, item_type, time_range, limit, offset)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_spotify_user_public_profile":
            user_id = arguments.get("user_id", "")
            logger.info(f"Getting public profile for user_id: {user_id}")

            if not user_id:
                return [
                    types.TextContent(
                        type="text",
                        text="user_id parameter is required to get public profile.",
                    )
                ]

            result = get_spotify_user_public_profile(user_id, sp)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_follow_playlist":
            playlist_id = arguments.get("playlist_id", "")
            public = arguments.get("public", None)
            logger.info(f"Following playlist with ID: {playlist_id}, public: {public}")

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to follow a playlist.",
                    )
                ]

            result = follow_playlist(playlist_id, public, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_unfollow_playlist":
            playlist_id = arguments.get("playlist_id", "")
            type_ = arguments.get("type", "artist")
            logger.info(f"Unfollowing playlist with ID: {playlist_id}")

            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id parameter is required to unfollow a playlist.",
                    )
                ]

            result = unfollow_playlist(playlist_id, type_, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_current_user_followed_artists":
            limit = arguments.get("limit", 20)
            after = arguments.get("after", None)
            logger.info(f"Getting followed artists with limit: {limit}, after: {after}")

            result = get_current_user_followed_artists(sp_oauth, limit, after)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_follow_artists_or_users":
            ids = arguments.get("ids", [])
            logger.info(f"Following artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to follow artists or users.",
                    )
                ]

            result = follow_artists_or_users(ids, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_unfollow_artists_or_users":
            ids = arguments.get("ids", [])
            type_ = arguments.get("type", "artist")  # or "user"
            logger.info(f"Unfollowing artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to unfollow artists or users.",
                    )
                ]

            result = unfollow_artists_or_users(ids, type_, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_check_user_follows":
            ids = arguments.get("ids", [])
            type_ = arguments.get("type", "artist")  # or "user"
            logger.info(f"Checking if user follows artists/users with IDs: {ids}")

            if not ids:
                return [
                    types.TextContent(
                        type="text",
                        text="ids parameter is required to check follows.",
                    )
                ]

            result = check_user_follows(ids, type_, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_add_items_to_playlist":
            playlist_id = arguments.get("playlist_id", "")
            uris = arguments.get("uris", [])
            position = arguments.get("position", None)
            logger.info(
                f"Adding items to playlist: {playlist_id}, uris: {uris}, position: {position}"
            )

            if not playlist_id or not uris:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id and uris parameters are required to add items to a playlist.",
                    )
                ]

            result = add_items_to_playlist(playlist_id, uris, sp_oauth, position)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_remove_items_from_playlist":
            playlist_id = arguments.get("playlist_id", "")
            uris = arguments.get("uris", [])
            logger.info(f"Removing items from playlist: {playlist_id}, uris: {uris}")

            if not playlist_id or not uris:
                return [
                    types.TextContent(
                        type="text",
                        text="playlist_id and uris parameters are required to remove items from a playlist.",
                    )
                ]

            result = remove_items_from_playlist(playlist_id, uris, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_current_user_playlists":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting current user playlists with limit: {limit}, offset: {offset}")

            result = get_current_user_playlists(sp_oauth, limit, offset)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_multiple_shows":
            show_ids = arguments.get("show_ids", [])
            logger.info(f"Getting multiple shows for IDs: {show_ids}")

            if not show_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="show_ids parameter is required to get multiple shows.",
                    )
                ]

            result = get_multiple_shows(show_ids, sp)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_show_episodes":
            show_id = arguments.get("show_id", "")
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            market = arguments.get("market", "US")
            logger.info(
                f"Getting episodes for show_id: {show_id}, limit: {limit}, "
                f"offset: {offset}, market: {market}"
            )

            if not show_id:
                return [
                    types.TextContent(
                        type="text",
                        text="show_id parameter is required to get show episodes.",
                    )
                ]

            result = get_show_episodes(show_id, sp, limit, offset, market)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        elif name == "spotify_get_current_user_saved_shows":
            limit = arguments.get("limit", 20)
            offset = arguments.get("offset", 0)
            logger.info(f"Getting current user saved shows with limit: {limit}, offset: {offset}")

            result = get_current_user_saved_shows(sp_oauth, limit, offset)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]
        elif name == "spotify_remove_shows_from_user_library":
            show_ids = arguments.get("show_ids", [])
            logger.info(f"Removing shows from user library: {show_ids}")

            if not show_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="show_ids parameter is required to remove shows.",
                    )
                ]

            result = remove_shows_from_user_library(show_ids, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
            ]
        elif name == "spotify_check_user_saved_shows":
            show_ids = arguments.get("show_ids", [])
            logger.info(f"Checking user saved shows for IDs: {show_ids}")

            if not show_ids:
                return [
                    types.TextContent(
                        type="text",
                        text="show_ids parameter is required to check saved shows.",
                    )
                ]

            result = check_user_saved_shows(show_ids, sp_oauth)
            return [
                types.TextContent(type="text", text=json.dumps(result, indent=2))
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
        auth_token = request.headers.get("x-auth-token")

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

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")

        # Extract auth token from headers (allow None - will be handled at tool level)
        headers = dict(scope.get("headers", []))
        auth_token = headers.get(b"x-auth-token")
        if auth_token:
            auth_token = auth_token.decode("utf-8")

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