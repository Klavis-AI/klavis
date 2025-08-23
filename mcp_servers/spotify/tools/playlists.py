from typing import List, Optional, Dict
from spotipy import Spotify
from .base import get_user_spotify_client, get_spotify_client , process_playlists


def get_playlist_by_id(
    playlist_id: str,
    sp: Spotify = None,
    market: str = None
) -> dict:
    """
    Get a Spotify playlist's full metadata and contents by its Spotify ID.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        sp (Spotify, optional): Authenticated Spotipy client.
                                Required 'playlist-read-private' for private playlists.
        market (str, optional): ISO 3166-1 alpha-2 country code to filter track availability.

    Returns:
        dict: Full playlist object from Spotify.
    """
    try:
        if not sp:
            sp = get_spotify_client()
        return sp.playlist(playlist_id, market=market)
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return {"error": str(e)}


def get_user_owned_playlists(
    user_id: str,
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> list:
    """
    Get playlists owned by a specific Spotify user.

    Parameters:
        user_id (str): Spotify user ID.
        sp (Spotify, optional): Authenticated Spotipy client.
        limit (int): Playlists per request (max 50).
        offset (int): Pagination offset.

    Returns:
        list: Playlist dictionaries owned by the given user.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        playlists = sp.user_playlists(user=user_id, limit=limit, offset=offset).get("items", [])
        return process_playlists(playlists)
    except Exception as e:
        print(f"Error fetching user playlists: {e}")
        return {"error": str(e)}


def get_current_user_playlists(
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Get playlists owned or followed by the current Spotify user.

    Parameters:
        sp (Spotify, optional): Authenticated Spotipy client.
                                Requires 'playlist-read-private' and/or 'playlist-read-collaborative' scopes.
        limit (int): Max number of playlists to return (1-50).
        offset (int): Pagination offset.

    Returns:
        List[dict]: Simplified playlist info.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        playlists_response = sp.current_user_playlists(limit=limit, offset=offset)
        playlists = playlists_response.get("items", [])
        return process_playlists(playlists)
    except Exception as e:
        print(f"Error fetching current user's playlists: {e}")
        return {"error": str(e)}


def update_playlist_details(
    playlist_id: str,
    name: str = None,
    public: bool = None,
    description: str = None,
    sp: Spotify = None
) -> str:
    """
    Update a playlist's name, description, or visibility.
    Must be called by the playlist owner.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        name (str, optional): New playlist name.
        public (bool, optional): True for public, False for private.
        description (str, optional): Playlist description.
        sp (Spotify, optional): Authenticated Spotipy client.

    Returns:
        str: "success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

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
    Add one or more tracks or episodes to a playlist.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        item_uris (List[str]): Spotify URIs or IDs of items to add.
        sp (Spotify, optional): Authenticated Spotipy client.
        position (int, optional): Position to insert items. Appends if omitted.

    Returns:
        dict: Spotify API response (contains 'snapshot_id') or error.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_ITEMS_PER_REQUEST = 100
        results = {"snapshot_id": None}

        for i in range(0, len(item_uris), MAX_ITEMS_PER_REQUEST):
            chunk = item_uris[i:i + MAX_ITEMS_PER_REQUEST]
            results = sp.playlist_add_items(
                playlist_id=playlist_id,
                items=chunk,
                position=position
            )

        return results
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
    Remove one or more tracks or episodes from a playlist.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        item_uris (List[str]): Spotify URIs of items to remove.
        sp (Spotify, optional): Authenticated Spotipy client.
        snapshot_id (str, optional): Snapshot ID for concurrency control.

    Returns:
        dict: Spotify API response (contains 'snapshot_id') or error.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        return sp.playlist_remove_all_occurrences_of_items(
            playlist_id=playlist_id,
            items=item_uris,
            snapshot_id=snapshot_id
        )
    except Exception as e:
        print(f"Error removing items from playlist: {e}")
        return {"error": f"{str(e)} - {playlist_id} - {item_uris}"}