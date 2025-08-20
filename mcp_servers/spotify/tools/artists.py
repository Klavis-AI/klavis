import json
from typing import Annotated, List
from pydantic import Field
from mcp import McpError
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_artist_tools(app):
    @app.tool(description=tool_desc("Get artist details.", "View artist info.", None))
    async def get_artist(artist_id: Annotated[str, Field(description="Artist ID")]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"artists/{artist_id}")
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    @app.tool(description=tool_desc("Get artist's albums.", "View artist's discography.", None))
    async def get_artist_albums(artist_id: Annotated[str, Field(description="Artist ID")], limit: Annotated[int, Field(default=20)]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"artists/{artist_id}/albums", {"limit": limit})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    @app.tool(description=tool_desc("Get artist's top tracks.", "View artist's popular songs.", None))
    async def get_artist_top_tracks(artist_id: Annotated[str, Field(description="Artist ID")], market: Annotated[str, Field(description="Market code", default="US")]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"artists/{artist_id}/top-tracks", {"market": market})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    @app.tool(description=tool_desc("Get related artists.", "Find similar artists.", None))
    async def get_related_artists(artist_id: Annotated[str, Field(description="Artist ID")]) -> List[TextContent]:
        try:
            # First verify the artist exists
            try:
                artist_data = await SpotifyAPI.get(f"artists/{artist_id}")
                artist_name = artist_data.get("name", "")
                print(f"Found artist: {artist_name} with ID {artist_id}")
            except McpError as e:
                if "404" in str(e):
                    return [TextContent(type="text", text=f"Error: Artist with ID '{artist_id}' not found in Spotify database. Please check the ID and try again.")]
                else:
                    raise e
            
            # Now try to get related artists
            try:
                data = await SpotifyAPI.get(f"artists/{artist_id}/related-artists")
                return [TextContent(type="text", text=json.dumps(data, indent=2))]
            except McpError as e:
                # Fallback to search-based similar artists
                print(f"Related artists endpoint failed, using search fallback: {str(e)}")
                
                # Search for similar artists based on the name
                search_data = await SpotifyAPI.get("search", {"q": f"artist:{artist_name}", "type": "artist", "limit": 10})
                artists = search_data.get("artists", {}).get("items", [])
                
                # Filter out the original artist from results if present
                filtered_artists = [a for a in artists if a.get("id") != artist_id]
                
                if filtered_artists:
                    result = {"artists": filtered_artists}
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                else:
                    return [TextContent(type="text", text=f"No related artists found for {artist_name} (ID: {artist_id})")]
        except Exception as e:
            print(f"Unexpected error in get_related_artists: {str(e)}")
            return [TextContent(type="text", text=f"Error finding related artists: {str(e)}")]