from spotipy import Spotify
from typing import List, Dict
from .base import get_spotify_client , process_artists_info , process_artist_albums , process_artist_top_tracks






def get_artists_info(artist_ids: List[str], sp: Spotify = None) -> List[Dict]:
    """
    Get catalog information for multiple artists by their Spotify IDs.

    Parameters:
        artist_ids (List[str]): Spotify artist IDs (max 50 per call).
        sp (Spotify, optional): Spotipy client instance. If None, creates one.

    Returns:
        List[dict]: Processed artist information.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        # Spotify's `artists()` method accepts up to 50 IDs per request
        results = sp.artists(artist_ids)
        artists = results.get("artists", [])
        return process_artists_info(artists)
    except Exception as e:
        print(f"An error occurred while getting artist info: {e}")
        return {"error": str(e)}


def get_artist_albums(
    artist_id: str,
    sp: Spotify = None,
    include_groups: str = None,
    limit: int = 20,
    offset: int = 0,
    market: str = None
) -> List[Dict]:
    """
    Retrieve information about an artist's albums.

    Parameters:
        artist_id (str): Spotify Artist ID or URI.
        sp (Spotify, optional): Spotipy client instance.
        include_groups (str, optional): One or more of 'album', 'single', 'compilation', 'appears_on'.
        limit (int): Number of albums per request (max 50).
        offset (int): Index of the first album to return.
        market (str, optional): ISO 3166-1 alpha-2 country code for market filtering.

    Returns:
        List[dict]: Processed list of album metadata.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        results = sp.artist_albums(
            artist_id=artist_id,
            album_type=include_groups,  # Maps to Spotify API's 'include_groups'
            limit=limit,
            offset=offset,
            country=market
        )
        albums = results.get("items", [])
        return process_artist_albums(albums)
    except Exception as e:
        print(f"An error occurred while fetching artist albums: {e}")
        return {"error": str(e)}



def get_artist_top_tracks(
    artist_id: str,
    sp: Spotify = None,
    country: str = None
) -> List[Dict]:
    """
    Get an artist's top tracks by country.

    Parameters:
        artist_id (str): Spotify artist ID.
        sp (Spotify, optional): Spotipy client instance.
        country (str, optional): Two-letter country code (e.g., 'US', 'GB', 'IN').

    Returns:
        List[dict]: Processed list of top track metadata.
    """
    try:
        if not sp:
            sp = get_spotify_client()

        results = sp.artist_top_tracks(artist_id, country=country)
        tracks = results.get("tracks", [])
        return process_artist_top_tracks(tracks)
    except Exception as e:
        print(f"An error occurred while fetching artist top tracks: {e}")
        return {"error": str(e)}
