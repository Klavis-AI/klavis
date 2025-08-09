import json
from typing import Annotated, List
from pydantic import Field
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_track_tools(app):
    @app.tool(description=tool_desc("Get track details.", "Get detailed track info.", None))
    async def get_track(track_id: Annotated[str, Field(description="Track ID")]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"tracks/{track_id}")
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    @app.tool(description=tool_desc("Compare tracks.", "Compare audio features between tracks.", None))
    async def compare_tracks(track_ids: Annotated[List[str], Field(description="Track IDs (2-5 tracks)")]) -> List[TextContent]:
        if not 2 <= len(track_ids) <= 5:
            return [TextContent(type="text", text="Please provide between 2 and 5 track IDs for comparison")]
        
        # Get features using individual requests to avoid 403 errors
        features = []
        tracks_info = []
        
        for track_id in track_ids:
            # Get track details first
            try:
                track_data = await SpotifyAPI.get(f"tracks/{track_id}")
                track_info = {
                    "id": track_id,
                    "name": track_data.get("name", "Unknown"),
                    "artist": track_data.get("artists", [{}])[0].get("name", "Unknown")
                }
                tracks_info.append(track_info)
                
                # Get audio features for this track
                try:
                    feature_data = await SpotifyAPI.get(f"audio-features/{track_id}")
                    if feature_data and not isinstance(feature_data, str):
                        features.append(feature_data)
                    else:
                        features.append(None)
                except:
                    features.append(None)
                    
            except:
                # If we can't get track details, use a placeholder
                tracks_info.append({
                    "id": track_id,
                    "name": "Unknown Track",
                    "artist": "Unknown Artist"
                })
                features.append(None)
        
        if not any(features) or len(features) < 2:
            return [TextContent(type="text", text="Could not retrieve audio features for the provided tracks. Please verify the track IDs and try again.")]
        
        # Prepare comparison data
        comparison = {}
        for feature_name in ["danceability", "energy", "valence", "tempo", "acousticness", "instrumentalness"]:
            comparison[feature_name] = {}
            for i, feature in enumerate(features):
                if i < len(tracks_info) and feature:  # Ensure we have track info and feature data
                    track_name = f"{tracks_info[i]['name']} by {tracks_info[i]['artist']}"
                    comparison[feature_name][track_name] = feature.get(feature_name)
        
        return [TextContent(type="text", text=json.dumps(comparison, indent=2))]