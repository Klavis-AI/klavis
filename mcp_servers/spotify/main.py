from mcp.server.fastmcp import FastMCP
from tools.artist import (
    get_artist_info,
    get_artist_top_tracks,
    get_artist_albums,
    get_artist_info_by_artist_name,
    get_artist_top_tracks_by_artist_name,
    get_artist_albums_by_artist_name
)
from tools.track import (
    search_tracks,
    get_track_details,
    get_tracks_by_artist_name
)
from tools.album import (
    get_album_details,
    get_album_tracks,
    get_albums_by_artist_name
)


mcp = FastMCP("spotify")

@mcp.tool()
async def search_track_tool(track_id: str) -> str:
    return await search_tracks(track_id)

@mcp.tool()
async def get_track_details_tool(track_id: str) -> str:
    return await get_track_details(track_id)

@mcp.tool()
async def get_tracks_by_artist_name_tool(artist_name: str, market: str = "US") -> str:
    return await get_tracks_by_artist_name(artist_name, market)

# Artist tools
@mcp.tool()
async def get_artist_info_tool(artist_id: str) -> str:
    return await get_artist_info(artist_id)

@mcp.tool()
async def get_artist_top_tracks_tool(artist_id: str, market: str = "US") -> str:
    return await get_artist_top_tracks(artist_id, market)

@mcp.tool()
async def get_artist_albums_tool(artist_id: str) -> str:
    return await get_artist_albums(artist_id)

@mcp.tool()
async def get_artist_info_by_artist_name_tool(artist_name: str) -> str:
    return await get_artist_info_by_artist_name(artist_name)

@mcp.tool()
async def get_artist_top_tracks_by_artist_name_tool(artist_name: str, market: str = "US") -> str:
    return await get_artist_top_tracks_by_artist_name(artist_name, market)

@mcp.tool()
async def get_artist_albums_by_artist_name_tool(artist_name: str) -> str:
    return await get_artist_albums_by_artist_name(artist_name)

# Album tools
@mcp.tool()
async def get_album_details_tool(album_id: str) -> str:
    return await get_album_details(album_id)

@mcp.tool()
async def get_album_tracks_tool(album_id: str) -> str:
    return await get_album_tracks(album_id)

@mcp.tool()
async def get_albums_by_artist_name_tool(artist_name: str) -> str:
    return await get_albums_by_artist_name(artist_name)


if __name__ == "__main__":
    mcp.run(transport="stdio")
