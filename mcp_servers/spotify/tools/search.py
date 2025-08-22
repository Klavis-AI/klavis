from typing import List, Dict, Optional
from spotipy import Spotify
from .base import get_spotify_client , process_spotify_items


def search_tracks(
    query: str,
    type: str = "track",
    limit: int = 10,
    sp: Optional[Spotify] = None
) -> List[Dict]:
    """
    Search Spotify for items of the given type and return simplified metadata.

    Parameters:
        query (str): Search query string.
        type (str): Spotify item type (e.g., 'track', 'album', 'artist').
        limit (int): Max number of items to return (default: 10).
        sp (Spotify, optional): Spotipy client. If None, a new one is created.

    Returns:
        list[dict]: Processed search results or an error dictionary.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        results = sp.search(q=query, type=type, limit=limit)
        items = results.get(f"{type}s", {}).get("items", [])
        return process_spotify_items(items, type)

    except Exception as e:
        print(f"An error occurred while searching for {type}s: {e}")
        return {"error": str(e)}