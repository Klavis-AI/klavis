from typing import List, Dict, Optional, Union
from spotipy import Spotify
from .base import get_spotify_client, get_user_spotify_client , process_track_info





def get_tracks_info(
    track_ids: List[str],
    sp: Optional[Spotify] = None
) -> Union[List[Dict], Dict]:
    """
    Get detailed information about one or multiple tracks.

    Parameters:
        track_ids (List[str]): Spotify track IDs (max 50 per call).
        sp (Spotify, optional): Spotipy client. If None, uses client-credentials.

    Returns:
        list[dict] | dict: List of simplified tracks, or error dict.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        # Spotipy's tracks() accepts up to 50 IDs
        results = sp.tracks(tracks=track_ids)
        tracks = results.get("tracks", [])
        return [
            t for t in (process_track_info(track) for track in tracks if track is not None)
            if t is not None
        ]
    except Exception as e:
        print(f"An error occurred while getting track info: {e}")
        return {"error": str(e)}


def get_user_saved_tracks(
    sp: Optional[Spotify] = None,
    limit: int = 20,
    offset: int = 0
) -> Union[List[Dict], Dict]:
    """
    Fetch the current user's saved tracks (Liked Songs).

    Parameters:
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.
        limit (int): Number of tracks per request (max 50).
        offset (int): Pagination offset.

    Returns:
        list[dict] | dict: Simplified saved tracks (with 'added_at'), or error dict.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = response.get("items", [])
        saved_tracks: List[Dict] = []

        for item in items:
            track = item.get("track")
            if not track:
                continue
            track_info = process_track_info(track)
            track_info["added_at"] = item.get("added_at")  # Timestamp when saved
            saved_tracks.append(track_info)

        return saved_tracks
    except Exception as e:
        print(f"An error occurred while fetching user saved tracks: {e}")
        return {"error": str(e)}


def save_tracks_for_current_user(
    track_ids: List[str],
    sp: Optional[Spotify] = None
) -> str:
    """
    Save one or more tracks to the current user's library.

    Parameters:
        track_ids (List[str]): Spotify track IDs to save.
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50  # Spotify API limit
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_tracks_add(tracks=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while saving tracks: {e}")
        return f"error: {str(e)}"


def check_user_saved_tracks(
    track_ids: List[str],
    sp: Optional[Spotify] = None
) -> Union[List[bool], Dict]:
    """
    Check if tracks are saved in the current user's library.

    Parameters:
        track_ids (List[str]): Spotify track IDs to check (max 50 per call).
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.

    Returns:
        list[bool] | dict: True/False for each track ID (input order), or error dict.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        saved_statuses: List[bool] = []
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i + MAX_IDS_PER_CALL]
            result = sp.current_user_saved_tracks_contains(tracks=chunk)
            saved_statuses.extend(result)
        return saved_statuses
    except Exception as e:
        print(f"An error occurred while checking saved tracks: {e}")
        return {"error": str(e)}


def remove_user_saved_tracks(
    track_ids: List[str],
    sp: Optional[Spotify] = None
) -> str:
    """
    Remove one or more tracks from the current user's saved tracks.

    Parameters:
        track_ids (List[str]): Spotify track IDs to remove.
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50  # Spotify API limit
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_tracks_delete(tracks=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while removing saved tracks: {e}")
        return f"error: {str(e)}"
