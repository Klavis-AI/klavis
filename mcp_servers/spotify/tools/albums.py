import json
from typing import Annotated, List
from pydantic import Field
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_album_tools(app):
    @app.tool(description=tool_desc("Get album details.", "View album info.", None))
    async def get_album(album_id: Annotated[str, Field(description="Album ID")]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"albums/{album_id}")
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    @app.tool(description=tool_desc("Get album tracks.", "View tracks in an album.", None))
    async def get_album_tracks(album_id: Annotated[str, Field(description="Album ID")], limit: Annotated[int, Field(default=20)]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"albums/{album_id}/tracks", {"limit": limit})
        return [TextContent(type="text", text=json.dumps(data, indent=2))]