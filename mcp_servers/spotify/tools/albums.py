from spotipy import Spotify
from typing import List, Dict
from .base import get_spotify_client, get_user_spotify_client ,process_album_info, process_album_tracks





def get_albums_info(album_ids: List[str], sp: Spotify = None) -> List[Dict]:
    """
    Get detailed information about one or multiple albums.

    Parameters:
        album_ids (list[str]): Album IDs to look up in Spotify's catalog.
        sp (spotipy.Spotify, optional): Spotipy client to use.

    Returns:
        list[dict]: Simplified album info for each requested album.
    """
    try:
        if not sp:
            sp = get_spotify_client()
        # Spotipy's albums() accepts up to 20 album IDs per call
        results = sp.albums(albums=album_ids)
        albums = results.get("albums", [])
        cleaned_results = [process_album_info(album) for album in albums if album is not None]
        return cleaned_results
    except Exception as e:
        print(f"An error occurred while getting album info: {e}")
        return {"error": str(e)}





def get_album_tracks(
    album_id: str,
    sp: Spotify = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    Get catalog information for tracks in a Spotify album.

    Parameters:
        album_id (str): Spotify Album ID.
        sp (spotipy.Spotify, optional): Spotipy client to use. If None, creates with get_spotify_client().
        limit (int): Max number of tracks to return per page (default 50, max 50).
        offset (int): Index of first track to return (for albums with >50 tracks).

    Returns:
        list[dict]: List of dicts, each dict contains info about a track.
    """
    try:
        if not sp:
            sp = get_spotify_client()
        results = sp.album_tracks(album_id=album_id, limit=limit, offset=offset)
        items = results.get("items", [])
        return process_album_tracks(items)
    except Exception as e:
        print(f"An error occurred while getting album tracks: {e}")
        return {"error": str(e)}


def get_user_saved_albums(
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Fetch the albums saved in the current Spotify user's library.

    Parameters:
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-read' scope.
        limit (int): Number of albums to return (max 50 per request, default 20).
        offset (int): Start index for pagination.

    Returns:
        list[dict]: List of dicts with album metadata.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        results = sp.current_user_saved_albums(limit=limit, offset=offset)
        items = results.get("items", [])
        return [process_album_info(item.get("album")) for item in items if item is not None]
    except Exception as e:
        print(f"An error occurred while fetching user saved albums: {e}")
        return {"error": str(e)}


def save_albums_for_current_user(album_ids: List[str], sp: Spotify = None) -> str:
    """
    Save one or more albums to the current user's library ("Your Music").

    Parameters:
        album_ids (List[str]): List of Spotify album IDs to save.
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-modify' scope.

    Returns:
        str: "Success" on success, or error message on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(album_ids), MAX_IDS_PER_CALL):
            chunk = album_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_albums_add(albums=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while saving albums: {e}")
        return f"error: {str(e)}"


def remove_albums_for_current_user(album_ids: List[str], sp: Spotify = None) -> str:
    """
    Remove one or more albums from the current user's library ("Your Music").

    Parameters:
        album_ids (List[str]): List of Spotify album IDs to remove.
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-modify' scope.

    Returns:
        str: "Success" on success, or error message on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(album_ids), MAX_IDS_PER_CALL):
            chunk = album_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_albums_delete(albums=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while removing albums: {e}")
        return f"error: {str(e)}"


def check_user_saved_albums(album_ids: List[str], sp: Spotify = None) -> List[bool] | Dict:
    """
    Check if one or more albums are saved in the current user's Spotify library.

    Parameters:
        album_ids (List[str]): List of Spotify album IDs to check (max 50 per call).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-read' scope.

    Returns:
        list[bool]: Saved status for each album ID.
        dict: Error message if an exception occurs.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        saved_statuses = []
        for i in range(0, len(album_ids), MAX_IDS_PER_CALL):
            chunk = album_ids[i:i + MAX_IDS_PER_CALL]
            result = sp.current_user_saved_albums_contains(albums=chunk)
            saved_statuses.extend(result)
        return saved_statuses
    except Exception as e:
        print(f"An error occurred while checking saved albums: {e}")
        return {"error": str(e)}
