from spotipy import Spotify
from typing import List, Dict
from .base import get_spotify_client, get_user_spotify_client
def process_episode_info(episode: dict) -> dict:
    """Extract relevant metadata from a Spotify episode object."""
    if not episode:
        return None
    return {
        "episode_id": episode.get("id"),
        "name": episode.get("name"),
        "description": episode.get("description"),
        "show_name": episode.get("show", {}).get("name"),
        "show_id": episode.get("show", {}).get("id"),
        "release_date": episode.get("release_date"),
        "duration_ms": episode.get("duration_ms"),
        "explicit": episode.get("explicit"),
        "languages": episode.get("languages", []),
        "audio_preview_url": episode.get("audio_preview_url"),
        "external_url": episode.get("external_urls", {}).get("spotify"),
        "images": episode.get("images", []),  # List of image dicts (cover art)
        "is_externally_hosted": episode.get("is_externally_hosted"),
        "type": episode.get("type"),
        "uri": episode.get("uri"),
    }

def get_episodes_info(
    episode_ids: List[str],
    sp: Spotify = None,
    market: str = None
) -> List[Dict]:
    """
    Get Spotify catalog information for several episodes by their Spotify IDs.

    Parameters:
        episode_ids (List[str]): List of Spotify episode IDs (max 50 per request).
        sp (spotipy.Spotify, optional): Spotipy client, will call get_spotify_client() if None.
        market (str, optional): Market filter (ISO 3166-1 alpha-2 code, e.g., 'US').

    Returns:
        List[Dict]: List of dicts with episode details.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Replace with your standard Spotipy client factory
        episodes_result = sp.episodes(episode_ids, market=market)
        episodes = episodes_result.get("episodes", [])
        return [process_episode_info(ep) for ep in episodes if ep]
    except Exception as e:
        print(f"An error occurred while fetching episode info: {e}")
        return {"error": str(e)}




def save_episodes_for_current_user(
    episode_ids: List[str],
    sp: Spotify = None
) -> dict:
    """
    Save one or more episodes to the current user's library.

    Parameters:
        episode_ids (List[str]): List of Spotify episode IDs to save.
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-modify' scope.
                                        If None, the function will create one.

    Returns:
        dict: Empty dict {} on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        # Spotify API allows up to 50 episode IDs per request
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
    Fetch the episodes saved in the current Spotify user's library.

    Parameters:
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-read' scope.
        limit (int): Number of episodes to return (max 50 per request, default 20).
        offset (int): Start index for pagination.

    Returns:
        List[Dict]: List of dicts, each with processed episode metadata.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        results = sp.current_user_saved_episodes(limit=limit, offset=offset)
        items = results.get("items", [])

        # Use process_episode_info on each episode object of each item
        processed_episodes = []
        for item in items:
            episode = item.get("episode")
            if episode:
                processed = process_episode_info(episode)
                # Add 'added_at' from the saved item to keep track of when saved
                processed['added_at'] = item.get('added_at')
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
        episode_ids (List[str]): List of Spotify episode IDs to remove.
        sp (spotipy.Spotify, optional): Authenticated Spotify client with 'user-library-modify' scope.
                                        If None, the function will create one.

    Returns:
        dict: Empty dict {} on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        # Spotify API allows up to 50 episode IDs per request
        MAX_IDS_PER_CALL = 50
        for i in range(0, len(episode_ids), MAX_IDS_PER_CALL):
            chunk = episode_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_episodes_delete(episodes=chunk)

        return "Success"  # Success
    except Exception as e:
        print(f"An error occurred while removing episodes: {e}")
        return f"error: {str(e)}"
    


def check_user_saved_episodes(
    episode_ids: List[str],
    sp: Spotify = None
) -> List[bool] or dict:
    """
    Check if one or more episodes are saved in the current user's Spotify library.

    Parameters:
        episode_ids (List[str]): List of Spotify episode IDs to check (max 50 per call).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-read' scope.
                                        If None, will create one as needed.

    Returns:
        List[bool]: List of booleans indicating saved status for each episode ID (in input order).
        or
        dict: Error dictionary if something goes wrong.
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