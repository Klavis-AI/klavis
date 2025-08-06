import json
from typing import Annotated, List
from pydantic import Field
from mcp import McpError
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_recommendation_tools(app):
    @app.tool(description=tool_desc("Get recommendations.", "Get track recommendations.", None))
    async def get_recommendations(
        limit: Annotated[int, Field(default=10)], 
        seed_artists: Annotated[List[str], Field(description="Artist IDs")] = [],
        seed_tracks: Annotated[List[str], Field(description="Track IDs")] = [],
        seed_genres: Annotated[List[str], Field(description="Genre names")] = []
    ) -> List[TextContent]:
        params = {"limit": limit}
        
        # Check if at least one seed parameter is provided
        if not (seed_artists or seed_tracks or seed_genres):
            return [TextContent(type="text", text="Error: At least one seed parameter (artists, tracks, or genres) is required")]
            
        if seed_artists: params["seed_artists"] = ",".join(seed_artists)
        if seed_tracks: params["seed_tracks"] = ",".join(seed_tracks)
        if seed_genres: params["seed_genres"] = ",".join(seed_genres)
        
        try:
            data = await SpotifyAPI.get("recommendations", params)
            return [TextContent(type="text", text=json.dumps(data.get("tracks", []), indent=2))]
        except McpError as e:
            return [TextContent(type="text", text=f"Error getting recommendations: {str(e)}")]

    @app.tool(description=tool_desc("Get available genre seeds.", "List genres for recommendations.", None))
    async def get_genre_seeds() -> List[TextContent]:
        try:
            data = await SpotifyAPI.get("recommendations/available-genre-seeds")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        except McpError:
            # Fallback to hardcoded common genre seeds if the API call fails
            fallback_genres = {
                "genres": [
                    "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "blues",
                    "classical", "country", "dance", "electronic", "folk", "funk", "hip-hop",
                    "house", "indie", "jazz", "metal", "pop", "r-n-b", "reggae", "rock", "soul"
                ]
            }
            return [TextContent(type="text", text=json.dumps(fallback_genres, indent=2))]