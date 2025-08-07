from spotipy import Spotify
from .base import get_user_spotify_client, get_spotify_client
from typing import List, Dict, Union
def get_current_user_profile(sp: Spotify = None) -> dict:
    """
    Get the current Spotify user's profile details (including username).

    Parameters:
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
                                        If None, uses your own client creation logic.

    Returns:
        dict: Detailed user profile info as returned by Spotify.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Replace with your Spotipy client setup
        return sp.current_user()
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return {"error": str(e)}
    
def process_top_artist_info(artist: dict) -> Dict:
    """Extract relevant info from a Spotify artist object."""
    return {
        "id": artist.get("id"),
        "name": artist.get("name"),
        "genres": artist.get("genres", []),
        "popularity": artist.get("popularity"),
        "followers": artist.get("followers", {}).get("total"),
        "external_url": artist.get("external_urls", {}).get("spotify"),
        "images": artist.get("images", []),
        "uri": artist.get("uri"),
        "type": artist.get("type")
    }

def process_top_track_info(track: dict) -> Dict:
    """Extract relevant info from a Spotify track object."""
    return {
        "id": track.get("id"),
        "name": track.get("name"),
        "album": {
            "id": track.get("album", {}).get("id"),
            "name": track.get("album", {}).get("name"),
            "images": track.get("album", {}).get("images", [])
        },
        "artists": [{"id": a.get("id"), "name": a.get("name")} for a in track.get("artists", [])],
        "popularity": track.get("popularity"),
        "duration_ms": track.get("duration_ms"),
        "explicit": track.get("explicit"),
        "external_url": track.get("external_urls", {}).get("spotify"),
        "uri": track.get("uri"),
        "type": track.get("type")
    }

def get_current_user_top_items(
    sp: Spotify = None,
    item_type: str = "artists",    # or "tracks"
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0
) -> List[Dict]:
    """Returns a processed list of the current user's top artists or tracks (id, name, etc)."""
    if not sp:
        sp, _ = get_user_spotify_client(scope="user-top-read")
    if item_type == "artists":
        results = sp.current_user_top_artists(
            time_range=time_range,
            limit=limit,
            offset=offset
        )
        return [process_top_artist_info(a) for a in results["items"]]
    elif item_type == "tracks":
        results = sp.current_user_top_tracks(
            time_range=time_range,
            limit=limit,
            offset=offset
        )
        return [process_top_track_info(t) for t in results["items"]]
    else:
        raise ValueError(f"item_type must be 'artists' or 'tracks', got {item_type}")

def get_spotify_user_public_profile(user_id: str, sp: Spotify = None) -> dict:
    """
    Get public profile information about a Spotify user by their user ID.

    Parameters:
        user_id (str): The Spotify User ID (username).
        sp (spotipy.Spotify, optional): Spotipy client. If None, initialize with your client creation method.

    Returns:
        dict: Public profile information as returned by Spotify or error dictionary.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Replace with your Spotipy client setup function

        profile = sp.user(user_id)
        return profile
    except Exception as e:
        print(f"Error fetching public profile for user {user_id}: {e}")
        return {"error": str(e)}

def follow_playlist(
    playlist_id: str,
    public: bool = True,
    sp: Spotify = None
    
) -> str:
    """
    Add the current authenticated user as a follower of a playlist.

    Parameters:
        playlist_id (str): Spotify ID of the playlist to follow.
        sp (spotipy.Spotify, optional): An authenticated Spotipy client.
        public (bool): If True, add as public follower; else, private. Defaults to True.

    Returns:
        dict: Empty dict on success, or error dictionary on failure.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Replace with your Spotipy client setup
        sp.current_user_follow_playlist(playlist_id, public=public)
        return "Success"  # Success
    except Exception as e:
        print(f"Error following playlist: {e}")
        return f"error: {str(e)}"


def unfollow_playlist(
    playlist_id: str,
    sp: Spotify = None
) -> dict:
    """
    Remove the current authenticated user as a follower of a playlist.

    Parameters:
        playlist_id (str): Spotify ID of the playlist to unfollow.
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
                                        If None, provide one according to your setup.

    Returns:
        dict: Empty dict {} on success, or error dictionary.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()  # Replace with your Spotipy client setup
        sp.current_user_unfollow_playlist(playlist_id)
        return "Success"  # Success
    except Exception as e:
        print(f"Error unfollowing playlist: {e}")
        return f"error: {str(e)}"

def get_current_user_followed_artists(
    sp: Spotify = None,
    limit: int = 20,
    after: str = None
) -> list:
    """
    Retrieve the current user's followed artists.

    Parameters:
        sp (spotipy.Spotify, optional): An authenticated Spotipy client with 'user-follow-read' scope.
        limit (int): Max number of artists per request (max 50).
        after (str, optional): The last artist ID retrieved from a previous page (for pagination).

    Returns:
        list: A list of artist objects with metadata.
    """
    try:
        if not sp:
            sp = get_user_spotify_client()
        results = sp.current_user_followed_artists(limit=limit, after=after)
        # 'artists' attribute contains paging info and the artists list
        return results["artists"]["items"]
    except Exception as e:
        print(f"Error retrieving followed artists: {e}")
        return {"error": str(e)}

def follow_artists_or_users(
    ids: List[str],
    sp: Spotify = None,
    type_: str = "artist"  # must be 'artist' or 'user'
) -> str:
    """
    Add the current authenticated user as a follower of one or more artists or Spotify users.

    Parameters:
        ids (List[str]): List of Spotify artist or user IDs to follow (max 50).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client.
        type_ (str): 'artist' or 'user' indicating the type of IDs in the list.

    Returns:
        str: "Success" on success, or error message.
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
    type_: str = "artist",  # or "user"
    sp: Spotify = None
) -> str:
    """
    Remove the current authenticated user as a follower of one or more artists or Spotify users.

    Parameters:
        ids (List[str]): List of Spotify artist or user IDs to unfollow (max 50).
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-follow-modify' scope.
                                        If None, the function will create one with that scope.

    Returns:
        dict: Empty dict on success, or dict with "error" key on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()  # Your auth helper with that scope

        MAX_IDS_PER_CALL = 50
        for i in range(0, len(ids), MAX_IDS_PER_CALL):
            chunk = ids[i:i + MAX_IDS_PER_CALL]
            if type_ == "artist":
                sp.user_unfollow_artists(chunk)
            elif type_ == "user":
                sp.user_unfollow_users(chunk)
            else:
                raise ValueError("type_ must be 'artist' or 'user'.")

        return "Success"  # Success
    except Exception as e:
        print(f"An error occurred while unfollowing artists/users: {e}")
        return f"error: {str(e)}"


def check_user_follows(
    ids: List[str],
    follow_type: str = "artist",  # or "user"
    sp: Spotify = None
) -> Union[List[bool], Dict]:
    """
    Check if the current Spotify user is following one or more artists or Spotify users.

    Parameters:
        ids (List[str]): List of Spotify artist or user IDs (max 50).
        follow_type (str): "artist" or "user".
        sp (spotipy.Spotify, optional): Authenticated Spotipy client with 'user-follow-read' scope if None, create one.

    Returns:
        List[bool]: Per-ID result, True if following, False if not.
        Or
        Dict: Error dictionary on failure.
    """
    try:
        if not sp:
            sp, _ = get_user_spotify_client()

        if follow_type == "artist":
            # Returns a list of booleans
            return sp.current_user_following_artists(ids)
        elif follow_type == "user":
            # Returns a list of booleans
            return sp.current_user_following_users(ids)
        else:
            raise ValueError('follow_type must be "artist" or "user"')
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}