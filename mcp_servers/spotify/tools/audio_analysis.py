import json
from typing import Annotated, List
from pydantic import Field
from mcp import McpError
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_audio_analysis_tools(app):
    @app.tool(description=tool_desc("Get audio features.", "Retrieve audio features for tracks.", None))
    async def get_audio_features(track_ids: Annotated[List[str], Field(description="Track IDs")]) -> List[TextContent]:
        # Start with dummy features for common attributes if all API calls fail
        dummy_features = {
            "acousticness": "Information not available",
            "danceability": "Information not available",
            "energy": "Information not available",
            "instrumentalness": "Information not available",
            "key": "Information not available",
            "liveness": "Information not available",
            "loudness": "Information not available",
            "mode": "Information not available",
            "speechiness": "Information not available",
            "tempo": "Information not available",
            "time_signature": "Information not available",
            "valence": "Information not available"
        }
        
        try:
            # Try bulk endpoint first
            try:
                data = await SpotifyAPI.get("audio-features", {"ids": ",".join(track_ids[:50])})
                if data and "audio_features" in data:
                    return [TextContent(type="text", text=json.dumps(data["audio_features"], indent=2))]
            except McpError as e:
                print(f"Bulk audio features request failed: {str(e)}")
                
            # Try individual endpoints
            all_features = []
            for track_id in track_ids[:20]:  # Limit to first 20 to avoid too many requests
                track_info = {"id": track_id}
                
                # Get track details first for context
                try:
                    track_data = await SpotifyAPI.get(f"tracks/{track_id}")
                    track_info["track_name"] = track_data.get("name", "Unknown")
                    track_info["artist"] = track_data.get("artists", [{}])[0].get("name", "Unknown")
                    track_info["album"] = track_data.get("album", {}).get("name", "Unknown")
                    track_info["popularity"] = track_data.get("popularity", "Unknown")
                    track_info["duration_ms"] = track_data.get("duration_ms", "Unknown")
                except Exception as e:
                    print(f"Failed to get track info for {track_id}: {str(e)}")
                    
                # Try to get audio features
                try:
                    feature_data = await SpotifyAPI.get(f"audio-features/{track_id}")
                    if feature_data and not isinstance(feature_data, str):
                        # Combine track info and audio features
                        track_info.update(feature_data)
                        all_features.append(track_info)
                        continue
                except Exception as e:
                    print(f"Failed to get audio features for {track_id}: {str(e)}")
                
                # If we reach here, we couldn't get audio features
                # Add track info with dummy features
                track_info.update(dummy_features)
                track_info["note"] = "Audio features unavailable - API permission restrictions"
                all_features.append(track_info)
            
            if all_features:
                return [TextContent(type="text", text=json.dumps(all_features, indent=2))]
            
            # Fall back to explanation if all attempts fail
            message = (
                "⚠️ Unable to access audio features via Spotify API. This is likely due to:\n\n"
                "1. Permission restrictions with client credentials authentication\n"
                "2. The audio-features endpoint requires user authorization\n\n"
                "To fix this:\n"
                "- Set up a refresh token with the 'user-read-private' scope\n"
                "- Add it to your .env file as SPOTIFY_REFRESH_TOKEN\n\n"
                "For now, here's what audio features typically include:\n\n"
                "- danceability: How suitable a track is for dancing (0.0 to 1.0)\n"
                "- energy: Perceptual measure of intensity and activity (0.0 to 1.0)\n"
                "- valence: Musical positiveness conveyed by a track (0.0 to 1.0)\n"
                "- tempo: Estimated tempo in BPM\n"
                "- acousticness: Confidence measure of whether the track is acoustic (0.0 to 1.0)\n"
                "- instrumentalness: Predicts whether a track contains no vocals (0.0 to 1.0)\n"
                "- liveness: Detects presence of audience in the recording (0.0 to 1.0)\n"
                "- speechiness: Presence of spoken words in a track (0.0 to 1.0)"
            )
            return [TextContent(type="text", text=message)]
        
        except Exception as e:
            print(f"Unexpected error in get_audio_features: {str(e)}")
            return [TextContent(type="text", text=f"Error retrieving audio features: {str(e)}\n\nThis endpoint may require user authorization.")]
        
    @app.tool(description=tool_desc("Get audio analysis.", "Get detailed audio analysis for a track.", None))
    async def get_audio_analysis(track_id: Annotated[str, Field(description="Track ID")]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"audio-analysis/{track_id}")
        # Audio analysis data can be large, so we'll return a summary
        summary = {
            "track": data.get("track", {}),
            "sections_count": len(data.get("sections", [])),
            "segments_count": len(data.get("segments", [])),
            "beats_count": len(data.get("beats", [])),
            "bars_count": len(data.get("bars", []))
        }
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]