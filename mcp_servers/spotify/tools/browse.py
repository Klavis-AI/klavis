import json
from typing import Annotated, List
from pydantic import Field
from mcp.types import TextContent
from .utils import tool_desc
from .spotify_api import SpotifyAPI

def register_browse_tools(app):
    @app.tool(description=tool_desc("Get new releases.", "View latest album releases.", None))
    async def get_new_releases(limit: Annotated[int, Field(default=20)], country: Annotated[str, Field(default="US")]) -> List[TextContent]:
        data = await SpotifyAPI.get("browse/new-releases", {"limit": limit, "country": country})
        return [TextContent(type="text", text=json.dumps(data.get("albums", {}), indent=2))]

    @app.tool(description=tool_desc("Get featured playlists.", "View curated featured playlists.", None))
    async def get_featured_playlists(limit: Annotated[int, Field(default=20)], country: Annotated[str, Field(default="US")]) -> List[TextContent]:
        data = await SpotifyAPI.get("browse/featured-playlists", {"limit": limit, "country": country})
        return [TextContent(type="text", text=json.dumps(data.get("playlists", {}), indent=2))]

    @app.tool(description=tool_desc("Get categories.", "Browse content categories.", None))
    async def get_categories(limit: Annotated[int, Field(default=20)], country: Annotated[str, Field(default="US")]) -> List[TextContent]:
        data = await SpotifyAPI.get("browse/categories", {"limit": limit, "country": country})
        return [TextContent(type="text", text=json.dumps(data.get("categories", {}), indent=2))]

    @app.tool(description=tool_desc("Get category playlists.", "View playlists for a category.", None))
    async def get_category_playlists(category_id: Annotated[str, Field(description="Category ID")], limit: Annotated[int, Field(default=20)]) -> List[TextContent]:
        data = await SpotifyAPI.get(f"browse/categories/{category_id}/playlists", {"limit": limit})
        return [TextContent(type="text", text=json.dumps(data.get("playlists", {}), indent=2))]