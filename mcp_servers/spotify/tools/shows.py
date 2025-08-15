from typing import List, Dict, Optional
from spotipy import Spotify
from .base import get_spotify_client, get_user_spotify_client , process_shows , process_episodes , process_saved_shows



def get_multiple_shows(
    show_ids: List[str],
    sp: Optional[Spotify] = None,
    market: str = "US"
) -> List[Dict]:
    """
    Get Spotify catalog information for several shows by their Spotify IDs.

    Parameters:
        show_ids (List[str]): Spotify show IDs (max 50 per call).
        sp (Spotify, optional): Spotipy client. If None, uses client-credentials.
        market (str): ISO 3166-1 alpha-2 country code.

    Returns:
        List[Dict]: Simplified show information.
    """
    if not sp:
        sp = get_spotify_client()

    MAX_IDS_PER_CALL = 50
    shows: List[Dict] = []
    try:
        for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
            chunk = show_ids[i:i + MAX_IDS_PER_CALL]
            response = sp.shows(shows=chunk, market=market)
            shows.extend(response.get("shows", []))
        return process_shows(shows)
    except Exception as e:
        print(f"Error fetching shows: {e}")
        return [  # Return minimal error stub list to match signature
            {"error": str(e)}
        ]




def get_show_episodes(
    show_id: str,
    sp: Optional[Spotify] = None,
    limit: int = 20,
    offset: int = 0,
    market: str = "US"
) -> List[Dict]:
    """
    Get Spotify catalog information about a show's episodes.

    Parameters:
        show_id (str): Spotify show ID.
        sp (Spotify, optional): Spotipy client. If None, uses client-credentials.
        limit (int): Number of episodes per request (1–50).
        offset (int): Pagination offset.
        market (str): ISO 3166-1 alpha-2 country code.

    Returns:
        List[Dict]: Simplified episode information.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        response = sp.show_episodes(
            show_id=show_id,
            limit=limit,
            offset=offset,
            market=market
        )
        episodes = response.get("items", [])
        return process_episodes(episodes)
    except Exception as e:
        print(f"Error fetching show episodes: {e}")
        return [{"error": str(e)}]







def get_current_user_saved_shows(
    sp: Optional[Spotify] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Get shows saved in the current Spotify user's library.

    Parameters:
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.
        limit (int): Number of shows per request (1–50).
        offset (int): Pagination offset.

    Returns:
        List[Dict]: Simplified saved-show information.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        response = sp.current_user_saved_shows(limit=limit, offset=offset)
        return process_saved_shows(response.get("items"))
    except Exception as e:
        print(f"Error getting saved shows: {e}")
        return [{"error": str(e)}]


def save_shows_to_user_library(
    show_ids: List[str],
    sp: Optional[Spotify] = None
) -> str:
    """
    Save one or more shows to the current user's library.

    Parameters:
        show_ids (List[str]): Spotify show IDs/URIs/URLs (max 50 per call).
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        # Spotify limits: up to 50 show IDs per request
        MAX_IDS_PER_CALL = 50
        for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
            batch = show_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_shows_add(shows=batch)
        return "Success"
    except Exception as e:
        print(f"Error saving shows to library: {e}")
        return f"error: {str(e)}"


def remove_shows_from_user_library(
    show_ids: List[str],
    sp: Optional[Spotify] = None
) -> str:
    """
    Remove one or more shows from the current user's library.

    Parameters:
        show_ids (List[str]): Spotify show IDs (max 50 per call).
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
            chunk = show_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_shows_delete(shows=chunk)
        return "Success"
    except Exception as e:
        print(f"Error removing shows from library: {e}")
        return f"error: {str(e)}"


def check_user_saved_shows(
    show_ids: List[str],
    sp: Optional[Spotify] = None
) -> List[bool]:
    """
    Check if one or more shows are saved in the current user's library.

    Parameters:
        show_ids (List[str]): Spotify show IDs to check (max 50 per call).
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.

    Returns:
        List[bool]: Saved status for each show ID (in input order).
    """
    if not sp:
        sp, _ = get_user_spotify_client()

    results: List[bool] = []
    MAX_IDS_PER_CALL = 50
    for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
        chunk = show_ids[i:i + MAX_IDS_PER_CALL]
        res = sp.current_user_saved_shows_contains(shows=chunk)
        results.extend(res)
    return results
