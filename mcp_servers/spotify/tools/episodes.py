from typing import List, Dict
from spotipy import Spotify
from .base import get_spotify_client, get_user_spotify_client , process_episode_info





def get_episodes_info(
    episode_ids: List[str],
    sp: Spotify = None,
    market: str = None
) -> List[Dict]:
    """
    Get catalog information for multiple episodes.

    Parameters:
        episode_ids (List[str]): Spotify episode IDs (max 50 per request).
        sp (Spotify, optional): Spotipy client. If None, uses get_spotify_client().
        market (str, optional): ISO 3166-1 alpha-2 country code (e.g., 'US').

    Returns:
        List[dict]: Processed episode metadata.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        episodes_result = sp.episodes(episode_ids, market=market)
        episodes = episodes_result.get("episodes", [])
        return [process_episode_info(ep) for ep in episodes if ep]
    except Exception as e:
        print(f"An error occurred while fetching episode info: {e}")
        return {"error": str(e)}


def save_episodes_for_current_user(
    episode_ids: List[str],
    sp: Spotify = None
) -> str:
    """
    Save one or more episodes to the current user's library.

    Parameters:
        episode_ids (List[str]): Spotify episode IDs to save.
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" on success, or error message string on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(episode_ids), MAX_IDS_PER_CALL):
            chunk = episode_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_episodes_add(episodes=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while saving episodes: {e}")
        return f"error: {str(e)}"


def get_user_saved_episodes(
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Fetch episodes saved in the current user's library.

    Parameters:
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.
        limit (int): Number of episodes per request (max 50).
        offset (int): Index of the first episode to return.

    Returns:
        List[dict]: Processed episode metadata with 'added_at' field.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        results = sp.current_user_saved_episodes(limit=limit, offset=offset)
        items = results.get("items", [])

        processed_episodes = []
        for item in items:
            episode = item.get("episode")
            if episode:
                processed = process_episode_info(episode)
                processed["added_at"] = item.get("added_at")  # Timestamp when saved
                processed_episodes.append(processed)

        return processed_episodes
    except Exception as e:
        print(f"An error occurred while fetching user saved episodes: {e}")
        return {"error": str(e)}


def remove_episodes_for_current_user(
    episode_ids: List[str],
    sp: Spotify = None
) -> str:
    """
    Remove one or more episodes from the current user's library.

    Parameters:
        episode_ids (List[str]): Spotify episode IDs to remove.
        sp (Spotify, optional): Authenticated client with 'user-library-modify' scope.

    Returns:
        str: "Success" on success, or error message string on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(episode_ids), MAX_IDS_PER_CALL):
            chunk = episode_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_episodes_delete(episodes=chunk)

        return "Success"
    except Exception as e:
        print(f"An error occurred while removing episodes: {e}")
        return f"error: {str(e)}"


def check_user_saved_episodes(
    episode_ids: List[str],
    sp: Spotify = None
) -> List[bool] | dict:
    """
    Check if one or more episodes are saved in the user's library.

    Parameters:
        episode_ids (List[str]): Spotify episode IDs to check (max 50 per call).
        sp (Spotify, optional): Authenticated client with 'user-library-read' scope.

    Returns:
        List[bool]: True/False for each episode ID in order.
        dict: Error message if something goes wrong.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        saved_statuses = []
        for i in range(0, len(episode_ids), MAX_IDS_PER_CALL):
            chunk = episode_ids[i:i + MAX_IDS_PER_CALL]
            result = sp.current_user_saved_episodes_contains(episodes=chunk)
            saved_statuses.extend(result)
        return saved_statuses
    except Exception as e:
        print(f"An error occurred while checking saved episodes: {e}")
        return {"error": str(e)}
