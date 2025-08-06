import json
from typing import Annotated, List
from pydantic import Field
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_search_tools(app):
    @app.tool(description=tool_desc("Search tracks by keyword.", "Find tracks matching query.", None))
    async def search_tracks(q: Annotated[str, Field(description="Query text")], limit: Annotated[int, Field(default=10)]) -> List[TextContent]:
        data = await SpotifyAPI.get("search", {"q": q, "type": "track", "limit": limit})
        return [TextContent(type="text", text=json.dumps(data.get("tracks", {}), indent=2))]

    @app.tool(description=tool_desc("Search artists by keyword.", "Find artists matching query.", None))
    async def search_artists(q: Annotated[str, Field(description="Query text")], limit: Annotated[int, Field(default=10)]) -> List[TextContent]:
        data = await SpotifyAPI.get("search", {"q": q, "type": "artist", "limit": limit})
        return [TextContent(type="text", text=json.dumps(data.get("artists", {}), indent=2))]

    @app.tool(description=tool_desc("Search albums by keyword.", "Find albums matching query.", None))
    async def search_albums(q: Annotated[str, Field(description="Query text")], limit: Annotated[int, Field(default=10)]) -> List[TextContent]:
        data = await SpotifyAPI.get("search", {"q": q, "type": "album", "limit": limit})
        return [TextContent(type="text", text=json.dumps(data.get("albums", {}), indent=2))]