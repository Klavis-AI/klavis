import os
from contextvars import ContextVar
from typing import Dict, Tuple, Any ,List, Optional , Union

import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

# Context-var cache for the access token (per async context)
auth_token_context: ContextVar[str] = ContextVar("auth_token", default="")

# Scopes required by the app (trimmed and readable)
AUTHORIZATION_SCOPE = (
    "user-library-read "
    "playlist-read-private playlist-read-collaborative "
    "playlist-modify-private playlist-modify-public "
    "user-follow-modify user-follow-read "
    "user-read-playback-position user-top-read user-read-recently-played "
    "user-library-modify"
)

# NOTE: Must be registered in the Spotify Developer Dashboard for your app
DEFAULT_REDIRECT_URI = "https://www.google.com"


def get_user_spotify_client() -> Tuple[Spotify, Dict[str, Any]]:
    """
    Create a user-authenticated Spotipy client (Authorization Code flow).

    On first run (or when no valid cached token exists), this will open a browser
    window for the user to log in and grant permissions.

    Returns:
        Tuple[Spotify, Dict[str, Any]]: (Spotipy client, token info dict)
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", DEFAULT_REDIRECT_URI)

    sp_oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=AUTHORIZATION_SCOPE,
        cache_path=".webassets-cache",
        show_dialog=True,
    )

    token_info = sp_oauth.get_cached_token()
    if not token_info or not sp_oauth.validate_token(token_info):
        # Opens browser for user login/consent if needed
        token_info = sp_oauth.get_access_token(as_dict=True)

    sp = spotipy.Spotify(auth=token_info["access_token"])
    return sp, token_info


def get_spotify_client() -> Spotify:
    """
    Create an app-level Spotipy client (Client Credentials flow).

    Uses SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.

    Returns:
        Spotify: Spotipy client authenticated with client credentials.

    Raises:
        ValueError: If required environment variables are missing.
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Spotify client ID/secret not found. "
            "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
        )

    credentials_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    )
    return Spotify(client_credentials_manager=credentials_manager)


def get_spotify_access_token() -> str:
    """
    Retrieve a (bearer) access token and cache it in a ContextVar.

    For client-credentials usage only. If a token is already cached in the
    current context, it will be returned directly.

    Returns:
        str: Raw access token string.
    """
    token = auth_token_context.get()
    if token:
        return token

    spotify = get_spotify_client()
    # Access underlying auth manager to fetch the raw token string
    access_token = spotify._auth_manager.get_access_token(as_dict=False)  # noqa: SLF001
    auth_token_context.set(access_token)
    return access_token

def process_album_info(album_info):
    """Process album information to extract relevant details."""
    if not album_info:
        return None
    return {
        "album_id": album_info.get("id"),
        "name": album_info.get("name"),
        "artists": [artist.get("name") for artist in album_info.get("artists", [])],
        "release_date": album_info.get("release_date"),
        "total_tracks": album_info.get("total_tracks"),
        "album_type": album_info.get("album_type"),
        "genres": album_info.get("genres", []),
        "label": album_info.get("label"),
        "popularity": album_info.get("popularity"),
        "external_url": album_info.get("external_urls", {}).get("spotify"),
    }

def process_album_tracks(tracks):
    """Process album's track items to extract relevant details."""
    output = []
    for track in tracks:
        output.append({
            "track_id": track.get("id"),
            "name": track.get("name"),
            "artists": [artist.get("name") for artist in track.get("artists", [])],
            "duration_ms": track.get("duration_ms"),
            "track_number": track.get("track_number"),
            "disc_number": track.get("disc_number"),
            "explicit": track.get("explicit"),
            "preview_url": track.get("preview_url"),
            "external_url": track.get("external_urls", {}).get("spotify"),
        })
    return output

def process_artists_info(artists: List[dict]) -> List[dict]:
    """
    Process a list of Spotify artist objects to extract key metadata.

    Parameters:
        artists (List[dict]): Raw artist data from Spotify API.

    Returns:
        List[dict]: Processed list of artist metadata.
    """
    output = []
    for artist in artists:
        output.append({
            "artist_id": artist.get("id"),
            "name": artist.get("name"),
            "genres": artist.get("genres", []),
            "followers": artist.get("followers", {}).get("total"),
            "popularity": artist.get("popularity"),
            "images": artist.get("images", []),  # List of image dicts: {url, width, height}
            "external_url": artist.get("external_urls", {}).get("spotify"),
            "type": artist.get("type"),
            "uri": artist.get("uri"),
        })
    return output

def process_artist_albums(albums: List[dict]) -> List[dict]:
    """
    Process a list of Spotify album objects to extract key metadata.

    Parameters:
        albums (List[dict]): Raw album data from Spotify API.

    Returns:
        List[dict]: Processed album metadata.
    """
    output = []
    for album in albums:
        output.append({
            "album_id": album.get("id"),
            "name": album.get("name"),
            "album_type": album.get("album_type"),
            "release_date": album.get("release_date"),
            "total_tracks": album.get("total_tracks"),
            "artists": [artist["name"] for artist in album.get("artists", [])],
            "images": album.get("images", []),  # Album cover images
            "external_url": album.get("external_urls", {}).get("spotify"),
            "available_markets": album.get("available_markets", []),
        })
    return output


def process_artist_top_tracks(tracks: List[dict]) -> List[dict]:
    """
    Process a list of Spotify track objects to extract top track metadata.

    Parameters:
        tracks (List[dict]): Raw track data from Spotify API.

    Returns:
        List[dict]: Processed track metadata.
    """
    output = []
    for track in tracks:
        output.append({
            "track_id": track.get("id"),
            "name": track.get("name"),
            "artists": [artist["name"] for artist in track.get("artists", [])],
            "album": track.get("album", {}).get("name"),
            "album_id": track.get("album", {}).get("id"),
            "duration_ms": track.get("duration_ms"),
            "popularity": track.get("popularity"),
            "explicit": track.get("explicit"),
            "preview_url": track.get("preview_url"),
            "external_url": track.get("external_urls", {}).get("spotify"),
        })
    return output

def process_episode_info(episode: dict) -> dict:
    """
    Extract relevant metadata from a Spotify episode object.

    Parameters:
        episode (dict): Raw episode data from Spotify API.

    Returns:
        dict: Processed episode metadata, or None if input is empty.
    """
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
        "images": episode.get("images", []),  # Episode cover art
        "is_externally_hosted": episode.get("is_externally_hosted"),
        "type": episode.get("type"),
        "uri": episode.get("uri"),
    }

def process_playlists(playlists: List[Dict]) -> List[Dict]:
    """
    Extract relevant info from a list of Spotify playlists.

    Parameters:
        playlists (List[dict]): Raw Spotify playlist objects.

    Returns:
        List[dict]: Simplified playlist metadata.
    """
    processed = []
    for pl in playlists:
        processed.append({
            "id": pl.get("id"),
            "name": pl.get("name"),
            "description": pl.get("description", ""),
            "owner_id": pl.get("owner", {}).get("id"),
            "owner_name": pl.get("owner", {}).get("display_name"),
            "public": pl.get("public"),
            "collaborative": pl.get("collaborative"),
            "tracks_total": pl.get("tracks", {}).get("total"),
            "images": pl.get("images", []),
            "external_url": pl.get("external_urls", {}).get("spotify"),
            "uri": pl.get("uri"),
            "href": pl.get("href"),
            "snapshot_id": pl.get("snapshot_id"),
        })
    return processed

def process_spotify_items(items: List[dict], type: str) -> List[dict]:
    """
    Process Spotify API items and extract relevant fields based on type.

    Parameters:
        items (list[dict]): List of Spotify API item dictionaries.
        type (str): One of 'track', 'album', 'artist', 'episode',
                    'show', 'playlist', or 'audiobook'.

    Returns:
        list[dict]: List of simplified dictionaries with relevant metadata
                    for each item.
    """
    output = []
    if not items:
        return output

    for item in items:
        if not item:
            continue

        if type == "track":
            output.append({
                "track_id": item.get("id"),
                "name": item.get("name"),
                "artists": [artist.get("name") for artist in item.get("artists", [])],
                "album": item.get("album", {}).get("name"),
                "duration_ms": item.get("duration_ms"),
                "popularity": item.get("popularity"),
                "explicit": item.get("explicit"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "album":
            output.append({
                "album_id": item.get("id"),
                "name": item.get("name"),
                "artists": [artist.get("name") for artist in item.get("artists", [])],
                "release_date": item.get("release_date"),
                "total_tracks": item.get("total_tracks"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "artist":
            output.append({
                "artist_id": item.get("id"),
                "name": item.get("name"),
                "genres": item.get("genres"),
                "popularity": item.get("popularity"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "episode":
            output.append({
                "episode_id": item.get("id"),
                "name": item.get("name"),
                "release_date": item.get("release_date"),
                "duration_ms": item.get("duration_ms"),
                "show_name": item.get("show", {}).get("name"),
                "explicit": item.get("explicit"),
                "description": item.get("description"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "show":
            output.append({
                "show_id": item.get("id"),
                "name": item.get("name"),
                "publisher": item.get("publisher"),
                "total_episodes": item.get("total_episodes"),
                "description": item.get("description"),
                "languages": item.get("languages"),
                "explicit": item.get("explicit"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "playlist":
            output.append({
                "playlist_id": item.get("id"),
                "name": item.get("name"),
                "owner": item.get("owner", {}).get("display_name"),
                "tracks_count": item.get("tracks", {}).get("total"),
                "description": item.get("description"),
                "public": item.get("public"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        elif type == "audiobook":
            output.append({
                "audiobook_id": item.get("id"),
                "name": item.get("name"),
                "authors": [author.get("name") for author in item.get("authors", [])] if item.get("authors") else [],
                "narrators": [narrator.get("name") for narrator in item.get("narrators", [])] if item.get("narrators") else [],
                "release_date": item.get("release_date"),
                "publisher": item.get("publisher"),
                "description": item.get("description"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

        else:
            # Fallback: minimal fields
            output.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

    return output

def process_shows(shows: List[Dict]) -> List[Dict]:
    """
    Extract relevant information from a list of Spotify show objects.

    Parameters:
        shows (List[Dict]): Raw show objects from Spotify API.

    Returns:
        List[Dict]: Simplified show information.
    """
    processed = []
    for show in shows or []:
        processed.append({
            "id": show.get("id"),
            "name": show.get("name"),
            "publisher": show.get("publisher"),
            "description": show.get("description", ""),
            "languages": show.get("languages", []),
            "media_type": show.get("media_type"),
            "explicit": show.get("explicit"),
            "total_episodes": show.get("total_episodes"),
            "images": show.get("images", []),  # Cover art
            "external_url": show.get("external_urls", {}).get("spotify"),
            "uri": show.get("uri"),
            "type": show.get("type"),
            "href": show.get("href"),
            "is_externally_hosted": show.get("is_externally_hosted", False),
        })
    return processed

def process_episodes(episodes: List[Dict]) -> List[Dict]:
    """
    Extract relevant information from a list of Spotify episode objects.

    Parameters:
        episodes (List[Dict]): Raw episode objects from Spotify API.

    Returns:
        List[Dict]: Simplified episode information.
    """
    processed = []
    for ep in episodes or []:
        if ep is None:
            continue  # Skip invalid entries
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


def process_saved_shows(input_data: List[Dict]) -> List[Dict]:
    """
    Process a list of saved shows, extracting relevant information.

    Parameters:
        input_data (List[Dict]): Each item has 'added_at' and a 'show' object.

    Returns:
        List[Dict]: Simplified saved-show information with 'added_at'.
    """
    processed = []
    for item in input_data or []:
        show = item.get("show", {}) or {}
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

def process_track_info(track_info: Dict) -> Optional[Dict]:
    """
    Extract relevant details from a Spotify track object.

    Parameters:
        track_info (dict): Raw track data from Spotify API.

    Returns:
        dict | None: Simplified track info, or None if input is falsy.
    """
    if not track_info:
        return None

    return {
        "track_id": track_info.get("id"),
        "name": track_info.get("name"),
        "artists": [a.get("name") for a in track_info.get("artists", [])],
        "album": track_info.get("album", {}).get("name"),
        "release_date": track_info.get("album", {}).get("release_date"),
        "duration_ms": track_info.get("duration_ms"),
        "popularity": track_info.get("popularity"),
        "track_number": track_info.get("track_number"),
        "external_url": track_info.get("external_urls", {}).get("spotify"),
    }


def process_top_artist_info(artist: Dict) -> Dict:
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
        "type": artist.get("type"),
    }