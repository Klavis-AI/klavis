import json
from typing import Annotated, List
from pydantic import Field
from mcp import McpError
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_playlist_tools(app):
    @app.tool(description=tool_desc("Get playlist details.", "Fetch playlist info.", None))
    async def get_playlist(playlist_id: Annotated[str, Field(description="Playlist ID")]) -> List[TextContent]:
        try:
            data = await SpotifyAPI.get(f"playlists/{playlist_id}")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        except McpError as e:
            error_message = str(e)
            # Check if this is a 404 error
            if "404" in error_message and "Resource not found" in error_message:
                message = (
                    f"Unable to access playlist {playlist_id}. Spotify requires user authorization to access playlists.\n\n"
                    f"To fix this:\n"
                    f"1. You need to set up a refresh token with the proper scopes\n"
                    f"2. Add it to your .env file as SPOTIFY_REFRESH_TOKEN\n\n"
                    f"Alternative: Try searching for public playlists instead."
                )
                return [TextContent(type="text", text=message)]
            # For other errors, re-raise
            raise e

    @app.tool(description=tool_desc("Get playlist tracks.", "Fetch playlist items.", None))
    async def get_playlist_tracks(playlist_id: Annotated[str, Field(description="Playlist ID")], limit: Annotated[int, Field(default=20)]) -> List[TextContent]:
        try:
            data = await SpotifyAPI.get(f"playlists/{playlist_id}/tracks", {"limit": limit})
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        except McpError as e:
            error_message = str(e)
            # Check if this is a 404 error
            if "404" in error_message and "Resource not found" in error_message:
                message = (
                    f"Unable to access tracks for playlist {playlist_id}. Spotify requires user authorization to access playlist tracks.\n\n"
                    f"To fix this:\n"
                    f"1. You need to set up a refresh token with the proper scopes\n"
                    f"2. Add it to your .env file as SPOTIFY_REFRESH_TOKEN\n\n"
                    f"Alternative: Try searching for tracks directly or browse featured playlists."
                )
                return [TextContent(type="text", text=message)]
            # For other errors, re-raise
            raise e