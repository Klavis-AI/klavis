from spotipy import Spotify
from .base import get_user_spotify_client, get_spotify_client
from typing import List, Optional, Dict

def get_playlist_by_id(playlist_id: str, sp: Spotify = None, market: str = None) -> dict:
    """
    Get a Spotify playlist's full metadata and contents by its Spotify ID.

    Parameters:
        playlist_id (str): The Spotify ID of the playlist.
        sp (spotipy.Spotify, optional): An authenticated Spotipy client (playlist-read-private scope for private playlists).
        market (str, optional): A market code (e.g., 'US') to filter track availability.

    Returns:
        dict: The full playlist object from Spotify.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Your helper function to return a Spotipy client
        return sp.playlist(playlist_id, market=market)
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return {"error": str(e)}

def get_user_owned_playlists(user_id: str, sp: Spotify = None, limit: int = 20, offset: int = 0) -> list:
    """
    Get playlists owned by a specific user.

    Parameters:
        user_id (str): The Spotify user ID.
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
        limit (int): Playlists per request (max 50).
        offset (int): Pagination offset.

    Returns:
        list: List of playlist dicts owned by the user.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()
        playlists = sp.user_playlists(user=user_id, limit=limit, offset=offset)['items']
        # Filter only playlists where owner.id matches user_id
        return [plist for plist in playlists if plist['owner']['id'] == user_id]
    except Exception as e:
        print(f"Error fetching user playlists: {e}")
        return {"error": str(e)}

def update_playlist_details(
    playlist_id: str,
    name: str = None,
    public: bool = None,
    description: str = None,
    sp=None
):
    """
    Change a playlist's name and/or public/private state.
    Must be called by the playlist owner.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Your client setup with proper auth & scope
        sp.playlist_change_details(
            playlist_id=playlist_id,
            name=name,
            public=public,
            description=description,
        )
        return "success"
    except Exception as e:
        print(f"Error updating playlist: {e}")
        return f"error: {str(e)}"
    
















def add_items_to_playlist(
    playlist_id: str,
    item_uris: List[str],
    sp: Optional[Spotify] = None,
    position: Optional[int] = None
) -> dict:
    """
    Add one or more items to a user's playlist.

    Parameters:
        playlist_id (str): Spotify ID of the playlist to add items to.
        item_uris (List[str]): List of Spotify item URIs or IDs to add (e.g., track or episode URIs).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client. If None, it will be created internally.
        position (int, optional): Zero-based position to insert the items in the playlist.
                                  If omitted, items are appended to the end.

    Returns:
        dict: JSON response from Spotify API on success or error information.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Your function to create a Spotipy client with user auth and appropriate scopes

        # Spotify API limits a maximum of 100 items per request
        MAX_ITEMS_PER_REQUEST = 100
        results = {"snapshot_id": None}
        
        for i in range(0, len(item_uris), MAX_ITEMS_PER_REQUEST):
            chunk = item_uris[i:i + MAX_ITEMS_PER_REQUEST]
            results = sp.playlist_add_items(
                playlist_id=playlist_id,
                items=chunk,
                position=position
            )

        return results  # Contains "snapshot_id" of updated playlist

    except Exception as e:
        print(f"Error adding items to playlist: {e}")
        return {"error": str(e)}
    
def remove_items_from_playlist(
    playlist_id: str,
    item_uris: List[str],
    sp: Spotify = None,
    snapshot_id: str = None
) -> Dict:
    """
    Remove one or more items (tracks or episodes) from a user's playlist.

    Parameters:
        playlist_id (str): Spotify ID of the playlist.
        item_uris (List[str]): List of Spotify URIs for the tracks or episodes to remove.
        sp (spotipy.Spotify, optional): Authenticated Spotipy client. If None, creates one internally.
        snapshot_id (str, optional): Playlist snapshot ID for concurrency control (optional).

    Returns:
        Dict: Response containing new playlist snapshot ID or error information.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Replace with your authenticated Spotipy client setup


        response = sp.playlist_remove_all_occurrences_of_items(
            playlist_id=playlist_id,
            items=item_uris,
            snapshot_id=snapshot_id
        )

        return response  # Contains "snapshot_id" of updated playlist

    except Exception as e:
        print(f"Error removing items from playlist: {e}")
        return {"error": f"{str(e)} - {playlist_id} - {item_uris}"}
    


def get_current_user_playlists(
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Get a list of playlists owned or followed by the current Spotify user.

    Parameters:
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'playlist-read-private' and optionally 'playlist-read-collaborative' scopes.
                                        If None, initializes one with your auth setup.
        limit (int): Maximum number of playlists to return (1-50).
        offset (int): The index of the first playlist to return (for pagination).

    Returns:
        List[Dict]: A list of playlist objects with metadata.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Replace with your client initialization logic

        playlists_response = sp.current_user_playlists(limit=limit, offset=offset)
        playlists = playlists_response.get("items", [])

        # Each item is a playlist dict with keys like id, name, owner, public, tracks, etc.
        return process_playlists(playlists)

    except Exception as e:
        print(f"Error fetching current user's playlists: {e}")
        return {"error": str(e)}
    

def process_playlists(playlists: List[Dict]) -> List[Dict]:
    """
    Extract and return relevant information from a list of Spotify playlists.

    Parameters:
        playlists (List[Dict]): List of raw playlist objects from Spotify API.

    Returns:
        List[Dict]: List of simplified playlist info dictionaries.
    """
    processed = []
    for pl in playlists:
        processed.append({
            "id": pl.get("id"),
            "name": pl.get("name"),
            "description": pl.get("description", ""),
            "owner_id": pl.get("owner", {}).get("id"),
            "owner_name": pl.get("owner", {}).get("display_name"),
            "public": pl.get("public"),  # Boolean or None
            "collaborative": pl.get("collaborative"),
            "tracks_total": pl.get("tracks", {}).get("total"),
            "images": pl.get("images", []),  # List of image dicts
            "external_url": pl.get("external_urls", {}).get("spotify"),
            "uri": pl.get("uri"),
            "href": pl.get("href"),
            "snapshot_id": pl.get("snapshot_id"),  # Useful for playlist updates
        })
    return processed

