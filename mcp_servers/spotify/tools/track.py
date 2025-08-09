from .base import SPOTIFY_API_BASE, make_spotify_request, format_track

async def search_tracks(query: str) -> str:
    """Search for tracks on Spotify by query."""
    url = f"{SPOTIFY_API_BASE}/search?q={query}&type=track&limit=5"
    data = await make_spotify_request(url)
    if not data or "tracks" not in data:
        return f"No tracks found. Error: {data.get('error') if data else 'No response'}"

    return "\n---\n".join([format_track(track) for track in data["tracks"]["items"]])

async def get_track_details(track_id: str) -> str:
    """Get detailed info about a track by ID."""
    url = f"{SPOTIFY_API_BASE}/tracks/{track_id}"
    data = await make_spotify_request(url)
    if not data or "name" not in data:
        return f"Unable to fetch track. Error: {data.get('error') if data else 'No response'}"

    return format_track(data)

async def get_tracks_by_artist_name(artist_name: str, market: str = "US") -> str:
    """Search an artist by name and return their top 5 tracks."""
    # Search for artist ID
    search_url = f"{SPOTIFY_API_BASE}/search?q={artist_name}&type=artist&limit=1"
    search_data = await make_spotify_request(search_url)

    if not search_data or "artists" not in search_data or not search_data["artists"]["items"]:
        return f"No artist found for '{artist_name}'."

    artist = search_data["artists"]["items"][0]
    artist_id = artist["id"]

    # Get top tracks
    top_tracks_url = f"{SPOTIFY_API_BASE}/artists/{artist_id}/top-tracks?market={market}"
    top_tracks_data = await make_spotify_request(top_tracks_url)

    if not top_tracks_data or "tracks" not in top_tracks_data:
        return f"Unable to fetch top tracks for '{artist_name}'."

    return f"Top tracks for {artist['name']}:\n" + "\n---\n".join(
        [format_track(track) for track in top_tracks_data["tracks"][:5]]
    )