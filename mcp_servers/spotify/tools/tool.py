from .search import register_search_tools
from .artists import register_artist_tools
from .tracks import register_track_tools
from .albums import register_album_tools
from .playlists import register_playlist_tools
from .browse import register_browse_tools
from .recommendations import register_recommendation_tools
from .audio_analysis import register_audio_analysis_tools

def register_all_tools(app):
    """Register all tool functions with the MCP app"""
    register_search_tools(app)
    register_artist_tools(app)
    register_track_tools(app)
    register_album_tools(app)
    register_playlist_tools(app)
    register_browse_tools(app)
    register_recommendation_tools(app)
    register_audio_analysis_tools(app)