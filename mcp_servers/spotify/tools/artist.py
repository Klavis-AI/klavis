from .base import SPOTIFY_API_BASE, make_spotify_request, format_track

async def get_artist_info(artist_id: str) -> str:
    """Get information about a Spotify artist."""
    url = f"{SPOTIFY_API_BASE}/artists/{artist_id}"
    data = await make_spotify_request(url)

    if not data or "name" not in data:
        return f"Unable to fetch artist info. Error: {data.get('error') if data else 'No response'}"

    return f"""
Name: {data.get('name')}
Genres: {', '.join(data.get('genres', []))}
Followers: {data['followers']['total']}
Popularity: {data.get('popularity')}
Spotify URL: {data['external_urls']['spotify']}
"""

async def get_artist_info_by_artist_name(artist_name: str) -> str:
    """Get information about a Spotify artist by their name."""
    # Search for the artist to get their ID
    search_url = f"{SPOTIFY_API_BASE}/search?q={artist_name}&type=artist&limit=1"
    search_data = await make_spotify_request(search_url)

    if not search_data or "artists" not in search_data or not search_data["artists"]["items"]:
        return f"Artist '{artist_name}' not found."

    artist = search_data["artists"]["items"][0]
    artist_id = artist["id"]

    # Now get full info using the ID
    return await get_artist_info(artist_id)

async def get_artist_top_tracks(artist_id: str, market: str = "US") -> str:
    """Get top tracks for a Spotify artist.

    Args:
        artist_id: Spotify artist ID
        market: Country code (default "US")
    """
    url = f"{SPOTIFY_API_BASE}/artists/{artist_id}/top-tracks?market={market}"
    data = await make_spotify_request(url)

    if not data or "tracks" not in data:
        return f"Unable to fetch top tracks. Error: {data.get('error') if data else 'No response'}"

    return "\n---\n".join([format_track(track) for track in data["tracks"][:5]])

async def get_artist_top_tracks_by_artist_name(artist_name: str, market: str = "US") -> str:
    """Get top tracks for a Spotify artist by their name."""
    search_url = f"{SPOTIFY_API_BASE}/search?q={artist_name}&type=artist&limit=1"
    search_data = await make_spotify_request(search_url)

    if not search_data or "artists" not in search_data or not search_data["artists"]["items"]:
        return f"Artist '{artist_name}' not found."

    artist_id = search_data["artists"]["items"][0]["id"]
    return await get_artist_top_tracks(artist_id, market)

async def get_artist_albums(artist_id: str) -> str:
    """Get list of albums by a Spotify artist."""
    url = f"{SPOTIFY_API_BASE}/artists/{artist_id}/albums?limit=5"
    data = await make_spotify_request(url)

    if not data or "items" not in data:
        return f"Unable to fetch albums. Error: {data.get('error') if data else 'No response'}"

    return "\n".join([f"{album['name']} ({album['release_date']})" for album in data["items"]])

async def get_artist_albums_by_artist_name(artist_name: str) -> str:
    """Get list of albums by a Spotify artist using their name."""
    search_url = f"{SPOTIFY_API_BASE}/search?q={artist_name}&type=artist&limit=1"
    search_data = await make_spotify_request(search_url)

    if not search_data or "artists" not in search_data or not search_data["artists"]["items"]:
        return f"Artist '{artist_name}' not found."

    artist_id = search_data["artists"]["items"][0]["id"]
    return await get_artist_albums(artist_id)