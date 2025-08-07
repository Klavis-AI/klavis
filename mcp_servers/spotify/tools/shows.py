from spotipy import Spotify
from typing import List, Dict
from typing import List, Dict
from .base import get_spotify_client, get_user_spotify_client
def process_shows(shows: List[Dict]) -> List[Dict]:
    """
    Extract and return relevant information from a list of Spotify show objects.

    Parameters:
        shows (List[Dict]): List of raw show objects from Spotify API.

    Returns:
        List[Dict]: List of simplified show information dictionaries.
    """
    processed = []
    for show in shows:
        processed.append({
            "id": show.get("id"),
            "name": show.get("name"),
            "publisher": show.get("publisher"),
            "description": show.get("description", ""),
            "languages": show.get("languages", []),
            "media_type": show.get("media_type"),
            "explicit": show.get("explicit"),
            "total_episodes": show.get("total_episodes"),
            "images": show.get("images", []),  # List of image dicts (cover art)
            "external_url": show.get("external_urls", {}).get("spotify"),
            "uri": show.get("uri"),
            "type": show.get("type"),
            "href": show.get("href"),
            "is_externally_hosted": show.get("is_externally_hosted", False),
        })
    return processed

def get_multiple_shows(
    show_ids: List[str],
    sp: Spotify = None,
    market: str = "US"
) -> List[Dict]:
    """
    Get Spotify catalog information for several shows by their Spotify IDs.

    Parameters:
        show_ids (List[str]): List of Spotify show IDs (maximum 50).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
        market (str, optional): Country code (ISO 3166-1 alpha-2) to filter available shows.

    Returns:
        List[Dict]: List of show metadata dictionaries as returned by Spotify.
    """
    if not sp:
        sp = get_spotify_client()  # Replace with your client initialization

    MAX_IDS_PER_CALL = 50
    shows = []
    try:
        for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
            chunk = show_ids[i:i + MAX_IDS_PER_CALL]
            # Correct call with actual chunk of show IDs and market
            response = sp.shows(shows=chunk, market=market)
            shows.extend(response.get("shows", []))


        return process_shows(shows)
    except Exception as e:
        print(f"Error fetching shows: {e}")
        return f"error: {str(e)}"
def process_episodes(episodes: List[Dict]) -> List[Dict]:
    """
    Extract and return relevant information from a list of Spotify episode objects.

    Parameters:
        episodes (List[Dict]): List of raw episode objects from Spotify API.

    Returns:
        List[Dict]: List of simplified episode information dictionaries.
    """
    processed = []
    for ep in episodes or []:
        if ep is None:
            continue  # skip invalid None entries
        processed.append({
            "id": ep.get("id"),
            "name": ep.get("name"),
            "description": ep.get("description", ""),
            "show_name": ep.get("show", {}).get("name"),
            "show_id": ep.get("show", {}).get("id"),
            "release_date": ep.get("release_date"),
            "duration_ms": ep.get("duration_ms"),
            "explicit": ep.get("explicit"),
            "languages": ep.get("languages", []),
            "audio_preview_url": ep.get("audio_preview_url"),
            "external_url": ep.get("external_urls", {}).get("spotify"),
            "images": ep.get("images", []),
            "is_externally_hosted": ep.get("is_externally_hosted"),
            "type": ep.get("type"),
            "uri": ep.get("uri"),
        })
    return processed

def get_show_episodes(
    show_id: str,
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0,
    market: str = "US"
) -> List[Dict]:
    """
    Get Spotify catalog information about a show's episodes.

    Parameters:
        show_id (str): Spotify Show ID.
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
        limit (int): Number of episodes to return (1-50).
        offset (int): Index of the first episode to return (for pagination).
        market (str, optional): Country code (ISO 3166-1 alpha-2) to filter episodes.

    Returns:
        List[Dict]: List of episode metadata dictionaries.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Replace with your Spotipy client init

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
        return []


from typing import List, Dict

def process_saved_shows(input_data: List[Dict]) -> List[Dict]:
    """
    Process a list of saved Spotify shows data, extracting relevant information.

    Parameters:
        input_data (List[Dict]): List of dictionaries each containing 'added_at' and 'show' info.

    Returns:
        List[Dict]: List of processed show dictionaries with key details.
    """
    processed = []
    for item in input_data or []:
        show = item.get("show", {})
        processed.append({
            "added_at": item.get("added_at"),
            "id": show.get("id"),
            "name": show.get("name"),
            "publisher": show.get("publisher"),
            "description": show.get("description", ""),
            "languages": show.get("languages", []),
            "media_type": show.get("media_type"),
            "explicit": show.get("explicit"),
            "total_episodes": show.get("total_episodes"),
            "images": show.get("images", []),
            "external_url": show.get("external_urls", {}).get("spotify"),
            "uri": show.get("uri"),
            "type": show.get("type"),
            "href": show.get("href"),
            "is_externally_hosted": show.get("is_externally_hosted", False),
            "available_markets": show.get("available_markets", []),
        })
    return processed

# Example usage:
# saved_shows_input = [ ... ]  # your JSON-like list
# processed_shows = process_saved_shows(saved_shows_input)
# for show in processed_shows:
#     print(show)

def get_current_user_saved_shows(
    sp: Spotify = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """
    Get a list of shows saved in the current Spotify user's library.

    Parameters:
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
        limit (int): Number of shows to return (1-50).
        offset (int): Index of first show to return (for pagination).

    Returns:
        List[Dict]: List of saved show metadata.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()
        response = sp.current_user_saved_shows(limit=limit, offset=offset)
        # return response
        return process_saved_shows(response.get("items"))
    except Exception as e:
        print(f"Error getting saved shows: {e}")
        return []
    


def save_shows_to_user_library(
    show_ids: List[str],
    sp: Spotify = None
) -> str:
    """
    Save one or more shows to the current Spotify user's library.

    Parameters:
        show_ids (List[str]): List of Spotify show IDs, URIs, or URLs to save (max 50).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-modify' scope.
                                        If None, will create one internally.

    Returns:
        str: "Success" if saved successfully, or an error message.
    """
    try:
        if sp is None:
            sp, _ = get_user_spotify_client()  # Your auth helper function

        # Spotify API allows up to 50 shows per call; batches automatically if needed
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
    sp: Spotify = None
) -> str:
    """
    Remove one or more shows from the current Spotify user's library.

    Parameters:
        show_ids (List[str]): List of Spotify show IDs to remove (maximum 50).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-library-modify' scope.
                                        If None, creates one internally.

    Returns:
        str: "Success" if removal succeeded, otherwise an error message.
    """
    try:
        if sp is None:
            sp, _ = get_user_spotify_client(scope="user-library-modify")  # Your auth helper

        # Spotify API allows up to 50 show IDs per request; batch if needed
        MAX_IDS_PER_CALL = 50
        for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
            chunk = show_ids[i:i + MAX_IDS_PER_CALL]
            sp.current_user_saved_shows_delete(shows=chunk)

        return "Success"
    except Exception as e:
        print(f"Error removing shows from library: {e}")
        return f"error: {str(e)}"

def check_user_saved_shows(show_ids: List[str],sp: Spotify ) -> List[bool]:
    """
    Check if one or more shows are saved in the current Spotify user's library.

    Parameters:
        sp (Spotify): Authenticated Spotipy client with 'user-library-read' scope.
        show_ids (List[str]): List of Spotify show IDs to check.

    Returns:
        List[bool]: Boolean list where each element indicates if the corresponding show is saved.
    """
    results = []
    MAX_IDS_PER_CALL = 50  # Spotify API supports up to 50 IDs per request
    for i in range(0, len(show_ids), MAX_IDS_PER_CALL):
        chunk = show_ids[i:i + MAX_IDS_PER_CALL]
        res = sp.current_user_saved_shows_contains(shows=chunk)
        results.extend(res)
    return results