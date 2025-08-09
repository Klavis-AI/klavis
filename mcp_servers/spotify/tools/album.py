from .base import SPOTIFY_API_BASE, make_spotify_request

async def get_album_details(album_id: str) -> str:
    """Get detailed information about a specific album."""
    url = f"{SPOTIFY_API_BASE}/albums/{album_id}"
    data = await make_spotify_request(url)

    if not data or "name" not in data:
        return f"Unable to fetch album details. Error: {data.get('error') if data else 'No response'}"

    return f"""
Album: {data['name']}
Artist(s): {', '.join([artist['name'] for artist in data['artists']])}
Release Date: {data.get('release_date')}
Total Tracks: {data.get('total_tracks')}
Spotify URL: {data['external_urls']['spotify']}
"""

async def get_album_tracks(album_id: str) -> str:
    """Get all tracks from a specific album."""
    url = f"{SPOTIFY_API_BASE}/albums/{album_id}/tracks"
    data = await make_spotify_request(url)

    if not data or "items" not in data:
        return f"Unable to fetch album tracks. Error: {data.get('error') if data else 'No response'}"

    return "\n".join([f"{idx+1}. {track['name']}" for idx, track in enumerate(data['items'])])

async def get_albums_by_artist_name(artist_name: str) -> str:
    """Search an artist by name and return their albums."""
    # 1. Search for artist ID
    search_url = f"{SPOTIFY_API_BASE}/search?q={artist_name}&type=artist&limit=1"
    search_data = await make_spotify_request(search_url)

    if not search_data or "artists" not in search_data or not search_data["artists"]["items"]:
        return f"No artist found for '{artist_name}'."

    artist = search_data["artists"]["items"][0]
    artist_id = artist["id"]

    # 2. Fetch albums
    albums_url = f"{SPOTIFY_API_BASE}/artists/{artist_id}/albums?limit=5"
    albums_data = await make_spotify_request(albums_url)

    if not albums_data or "items" not in albums_data:
        return f"Unable to fetch albums for '{artist_name}'."

    return f"Albums by {artist['name']}:\n" + "\n".join(
        [f"{album['name']} ({album['release_date']})" for album in albums_data["items"]]
    )
