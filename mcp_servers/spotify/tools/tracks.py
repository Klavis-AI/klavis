from .base import get_spotify_client , get_user_spotify_client
from typing import List
import json 
from spotipy import Spotify
def get_tracks_info(track_ids: list[str], sp: Spotify=None) -> list[dict]:
    """ Get detailed information about one or multiple tracks."""
    try:
        if not sp:
            sp = get_spotify_client()
        # Spotipy's tracks() method accepts up to 50 track IDs as a list
        results = sp.tracks(tracks=track_ids)
        tracks = results.get('tracks', [])
        cleaned_results = [process_track_info(track) for track in tracks if track is not None]
        return cleaned_results

    except Exception as e:
        print(f"An error occurred while getting track info: {e}")
        return {"error": str(e)}


def process_track_info(track_info):
    """ Process track information to extract relevant details."""
    if not track_info:
        return None
    
    return {
        'name': track_info.get('name'),
        'artists': [artist.get('name') for artist in track_info.get('artists', [])],
        'album': track_info.get('album', {}).get('name'),
        'release_date': track_info.get('album', {}).get('release_date'),
        'duration_ms': track_info.get('duration_ms'),
        'popularity': track_info.get('popularity'),
        'track_number': track_info.get('track_number'),
        'url': track_info.get('external_urls', {}).get('spotify')
    }


def get_user_saved_tracks(sp:Spotify=None, limit: int = 20, offset: int = 0):
    """
    Fetch the Spotify user's saved tracks (liked/saved songs).

    Parameters:
        access_token (str): Spotify user access token with 'user-library-read' scope.
        limit (int): Max number of tracks to return (max 50, default 20).
        offset (int): The index of the first track to return (for pagination).

    Returns:
        list of dict: Each dict contains simplified info about a saved track.
    """
    try:
        # Create a Spotify client with the user access token
        if not sp:
            sp, _ = get_user_spotify_client(scope="user-library-read")

        # Call the endpoint to get saved tracks
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)

        items = response.get("items", [])
        saved_tracks = []

        for item in items:
            track = item.get("track")
            if track:
                saved_tracks.append({
                    "track_id": track.get("id"),
                    "name": track.get("name"),
                    "artists": [artist["name"] for artist in track.get("artists", [])],
                    "album": track.get("album", {}).get("name"),
                    "duration_ms": track.get("duration_ms"),
                    "popularity": track.get("popularity"),
                    "explicit": track.get("explicit"),
                    "added_at": item.get("added_at"),
                    "external_url": track.get("external_urls", {}).get("spotify"),
                })
        
        return saved_tracks

    except Exception as e:
        print(f"An error occurred while fetching user saved tracks: {e}")
        return {"error": str(e)}

def save_tracks_for_current_user(track_ids: list[str], sp:Spotify=None) -> dict:
    """
    Save one or more tracks to the current user's 'Your Library'.

    Parameters:
        track_ids (list of str): List of Spotify track IDs to save.
        sp (spotipy.Spotify, optional): Authenticated Spotify client.
            If None, will attempt to create one with correct scope.

    Returns:
        dict: Empty dict {} on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            # Create Spotify client with user auth scope to save tracks
            sp, _ = get_user_spotify_client()

        # Spotipy expects max 50 track IDs per call
        MAX_IDS_PER_CALL = 50
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i+MAX_IDS_PER_CALL]
            sp.current_user_saved_tracks_add(tracks=chunk)

        return "Succesfully Saved"  # Success - empty dict

    except Exception as e:
        print(f"An error occurred while saving tracks: {e}")
        return f"error: {str(e)}"
    
def check_user_saved_tracks(track_ids: List[str], sp:Spotify=None) -> List[bool] or dict:
    """
    Check if one or more tracks are saved in the current user's Spotify library.

    Parameters:
        track_ids (List[str]): List of Spotify track IDs to check (max 50 per call).
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-read' scope.
                                       If None, this function will create one.

    Returns:
        List[bool]: List of booleans indicating saved status for each track ID.
        or
        dict: Error dictionary if something goes wrong.
    """
    try:
        if not sp:
            # Create Spotify client with the required scope
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        saved_statuses = []

        # Spotify API allows max 50 track IDs per request
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i+MAX_IDS_PER_CALL]
            result = sp.current_user_saved_tracks_contains(tracks=chunk)
            saved_statuses.extend(result)

        return saved_statuses

    except Exception as e:
        print(f"An error occurred while checking saved tracks: {e}")
        return {"error": str(e)}
    

def save_tracks_for_current_user(track_ids: list[str], sp=None) -> dict:
    """
    Save one or more tracks to the current user's 'Your Library'.

    Parameters:
        track_ids (list of str): List of Spotify track IDs to save.
        sp (spotipy.Spotify, optional): Authenticated Spotify client.
            If None, will attempt to create one with correct scope.

    Returns:
        dict: Empty dict {} on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            # Create Spotify client with user auth scope to save tracks
            sp, _ = get_user_spotify_client()

        # Spotipy expects max 50 track IDs per call
        MAX_IDS_PER_CALL = 50
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i+MAX_IDS_PER_CALL]
            sp.current_user_saved_tracks_add(tracks=chunk)

        return "Success"  

    except Exception as e:
        print(f"An error occurred while saving tracks: {e}")
        return f"error: {str(e)}"

def remove_user_saved_tracks(track_ids: List[str], sp=None) -> dict:
    """
    Remove one or more tracks from the current user's saved tracks (Your Library).

    Parameters:
        track_ids (List[str]): List of Spotify track IDs to remove.
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-modify' scope.
                                       If None, this function will create one.

    Returns:
        dict: Empty dict {} on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            # Create Spotify client with user-library-modify scope
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50  # Spotify API limit per request
        for i in range(0, len(track_ids), MAX_IDS_PER_CALL):
            chunk = track_ids[i:i+MAX_IDS_PER_CALL]
            sp.current_user_saved_tracks_delete(tracks=chunk)

        return "Success"  # Success

    except Exception as e:
        print(f"An error occurred while removing saved tracks: {e}")
        return f"error: {str(e)}"