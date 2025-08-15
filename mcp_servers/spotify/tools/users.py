from typing import List, Dict, Union, Optional
from spotipy import Spotify
from .base import get_user_spotify_client, get_spotify_client , process_top_artist_info


def get_current_user_profile(sp: Optional[Spotify] = None) -> Dict:
    """
    Get the current Spotify user's profile details.

    Parameters:
        sp (Spotify, optional): Authenticated Spotipy client. If None, a new one is created.

    Returns:
        dict: Detailed user profile info as returned by Spotify, or {"error": ...} on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        return sp.current_user()
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return {"error": str(e)}





def process_top_track_info(track: Dict) -> Dict:
    """Extract relevant info from a Spotify track object."""
    return {
        "id": track.get("id"),
        "name": track.get("name"),
        "album": {
            "id": track.get("album", {}).get("id"),
            "name": track.get("album", {}).get("name"),
            "images": track.get("album", {}).get("images", []),
        },
        "artists": [{"id": a.get("id"), "name": a.get("name")} for a in track.get("artists", [])],
        "popularity": track.get("popularity"),
        "duration_ms": track.get("duration_ms"),
        "explicit": track.get("explicit"),
        "external_url": track.get("external_urls", {}).get("spotify"),
        "uri": track.get("uri"),
        "type": track.get("type"),
    }


def get_current_user_top_items(
    sp: Optional[Spotify] = None,
    item_type: str = "artists",  # or "tracks"
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    """
    Return the current user's top artists or tracks (processed).

    Parameters:
        sp (Spotify, optional): Authenticated client with 'user-top-read' scope.
        item_type (str): "artists" or "tracks".
        time_range (str): "short_term" | "medium_term" | "long_term".
        limit (int): Items per page (1–50).
        offset (int): Pagination offset.

    Returns:
        List[Dict]: Processed items.
    """
    if not sp:
        sp, _ = get_user_spotify_client()

    if item_type == "artists":
        results = sp.current_user_top_artists(time_range=time_range, limit=limit, offset=offset)
        return [process_top_artist_info(a) for a in results.get("items", [])]
    if item_type == "tracks":
        results = sp.current_user_top_tracks(time_range=time_range, limit=limit, offset=offset)
        return [process_top_track_info(t) for t in results.get("items", [])]
    raise ValueError(f"item_type must be 'artists' or 'tracks', got {item_type}")


def get_spotify_user_public_profile(user_id: str, sp: Optional[Spotify] = None) -> Dict:
    """
    Get public profile information for a Spotify user by user ID.

    Parameters:
        user_id (str): Spotify user ID.
        sp (Spotify, optional): Spotipy client. If None, client-credentials is used.

    Returns:
        dict: Public profile information or {"error": ...} on failure.
    """
    try:
        if not sp:
            sp = get_spotify_client()
        return sp.user(user_id)
    except Exception as e:
        print(f"Error fetching public profile for user {user_id}: {e}")
        return {"error": str(e)}


def follow_playlist(
    playlist_id: str,
    public: bool = True,
    sp: Optional[Spotify] = None,
) -> str:
    """
    Follow a playlist as the current authenticated user.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        public (bool): Add as public follower if True; else private.
        sp (Spotify, optional): Authenticated client.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        sp.current_user_follow_playlist(playlist_id, public=public)
        return "Success"
    except Exception as e:
        print(f"Error following playlist: {e}")
        return f"error: {str(e)}"


def unfollow_playlist(
    playlist_id: str,
    sp: Optional[Spotify] = None,
) -> str:
    """
    Unfollow a playlist as the current authenticated user.

    Parameters:
        playlist_id (str): Spotify playlist ID.
        sp (Spotify, optional): Authenticated client.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        sp.current_user_unfollow_playlist(playlist_id)
        return "Success"
    except Exception as e:
        print(f"Error unfollowing playlist: {e}")
        return f"error: {str(e)}"


def get_current_user_followed_artists(
    sp: Optional[Spotify] = None,
    limit: int = 20,
    after: Optional[str] = None,
) -> Union[List[Dict], Dict]:
    """
    Retrieve artists followed by the current user.

    Parameters:
        sp (Spotify, optional): Authenticated client with 'user-follow-read' scope.
        limit (int): Max artists per request (1–50).
        after (str, optional): Last artist ID from previous page (for pagination).

    Returns:
        list[dict] | dict: Artist objects (from Spotify) or error dict.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()
        results = sp.current_user_followed_artists(limit=limit, after=after)
        return results.get("artists", {}).get("items", [])
    except Exception as e:
        print(f"Error retrieving followed artists: {e}")
        return {"error": str(e)}


def follow_artists_or_users(
    ids: List[str],
    sp: Optional[Spotify] = None,
    type_: str = "artist",  # "artist" or "user"
) -> str:
    """
    Follow one or more artists or Spotify users.

    Parameters:
        ids (List[str]): Spotify IDs to follow (max 50 per call).
        sp (Spotify, optional): Authenticated client.
        type_ (str): "artist" or "user".

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(ids), MAX_IDS_PER_CALL):
            chunk = ids[i:i + MAX_IDS_PER_CALL]
            if type_ == "artist":
                sp.user_follow_artists(chunk)
            elif type_ == "user":
                sp.user_follow_users(chunk)
            else:
                raise ValueError("type_ must be 'artist' or 'user'.")
        return "Success"
    except Exception as e:
        print(f"An error occurred while following artists/users: {e}")
        return f"error: {str(e)}"


def unfollow_artists_or_users(
    ids: List[str],
    type_: str = "artist",  # "artist" or "user"
    sp: Optional[Spotify] = None,
) -> str:
    """
    Unfollow one or more artists or Spotify users.

    Parameters:
        ids (List[str]): Spotify IDs to unfollow (max 50 per call).
        type_ (str): "artist" or "user".
        sp (Spotify, optional): Authenticated client with 'user-follow-modify' scope.

    Returns:
        str: "Success" or error message.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(ids), MAX_IDS_PER_CALL):
            chunk = ids[i:i + MAX_IDS_PER_CALL]
            if type_ == "artist":
                sp.user_unfollow_artists(chunk)
            elif type_ == "user":
                sp.user_unfollow_users(chunk)
            else:
                raise ValueError("type_ must be 'artist' or 'user'.")
        return "Success"
    except Exception as e:
        print(f"An error occurred while unfollowing artists/users: {e}")
        return f"error: {str(e)}"


def check_user_follows(
    ids: List[str],
    follow_type: str = "artist",  # "artist" or "user"
    sp: Optional[Spotify] = None,
) -> Union[List[bool], Dict]:
    """
    Check if the current user follows given artists or users.

    Parameters:
        ids (List[str]): Spotify IDs to check (max 50).
        follow_type (str): "artist" or "user".
        sp (Spotify, optional): Authenticated client with 'user-follow-read' scope.

    Returns:
        list[bool] | dict: Per-ID boolean status, or error dict.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        if follow_type == "artist":
            return sp.current_user_following_artists(ids)
        if follow_type == "user":
            return sp.current_user_following_users(ids)
        raise ValueError('follow_type must be "artist" or "user"')
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}
