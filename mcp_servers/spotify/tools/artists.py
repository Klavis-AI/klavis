from spotipy import Spotify
from typing import List, Dict
from .base import get_spotify_client
def process_artists_info(artists: List[dict]) -> List[dict]:
    """
    Given a list of artist objects from Spotify, extract key information.
    """
    output = []
    for artist in artists:
        output.append({
            "artist_id": artist.get("id"),
            "name": artist.get("name"),
            "genres": artist.get("genres", []),
            "followers": artist.get("followers", {}).get("total"),
            "popularity": artist.get("popularity"),
            "images": artist.get("images", []),  # List of image dicts (url, width, height)
            "external_url": artist.get("external_urls", {}).get("spotify"),
            "type": artist.get("type"),
            "uri": artist.get("uri"),
        })
    return output

def get_artists_info(artist_ids: List[str], sp: Spotify = None) -> List[Dict]:
    """
    Get Spotify catalog information for several artists by their Spotify IDs.

    Parameters:
        artist_ids (List[str]): List of Spotify artist IDs (max 50 per call).
        sp (spotipy.Spotify, optional): Authenticated or client-credentials Spotipy client.
                                        If None, your get_spotify_client() function is used.

    Returns:
        List[Dict]: List of processed artist info dicts.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Implement per your project setup

        # Spotipy's artists() method accepts up to 50 IDs per call
        results = sp.artists(artist_ids)
        artists = results.get('artists', [])
        return process_artists_info(artists)
    except Exception as e:
        print(f"An error occurred while getting artist info: {e}")
        return {"error": str(e)}

from spotipy import Spotify
from typing import List, Dict

def process_artist_albums(albums: List[dict]) -> List[dict]:
    """
    Extract relevant metadata from a list of album objects.
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
            "images": album.get("images", []),  # List of cover art dicts (url, height, width)
            "external_url": album.get("external_urls", {}).get("spotify"),
            "available_markets": album.get("available_markets", []),
        })
    return output

def get_artist_albums(
    artist_id: str,
    sp: Spotify = None,
    include_groups: str = None,
    limit: int = 20,
    offset: int = 0,
    market: str = None
) -> List[Dict]:
    """
    Retrieve Spotify catalog information about an artist's albums.

    Parameters:
        artist_id (str): Spotify Artist ID or URI.
        sp (spotipy.Spotify, optional): Spotipy client.
        include_groups (str, optional): One or more of 'album', 'single', 'compilation', 'appears_on' (comma-separated).
        limit (int, optional): Number of albums to return (max 50 per call).
        offset (int, optional): The index of the first album to return.
        market (str, optional): ISO 3166-1 alpha-2 country code for market filtering.

    Returns:
        List[Dict]: List of dicts with key album metadata.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Your project’s helper for client credentials

        results = sp.artist_albums(
            artist_id=artist_id,
            album_type=include_groups,  # Spotipy param maps to API's 'include_groups'
            limit=limit,
            offset=offset,
            country=market
        )
        albums = results.get("items", [])
        return process_artist_albums(albums)
    except Exception as e:
        print(f"An error occurred while fetching artist albums: {e}")
        return {"error": str(e)}


from spotipy import Spotify
from typing import List, Dict

def process_artist_top_tracks(tracks: List[dict]) -> List[dict]:
    """Extract key info from each top track of the artist."""
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

def get_artist_top_tracks(
    artist_id: str,
    sp: Spotify = None,
    country: str = None
) -> List[Dict]:
    """
    Get Spotify catalog information about an artist's top tracks by country.

    Parameters:
        artist_id (str): Spotify artist ID.
        sp (spotipy.Spotify, optional): Your Spotipy client. If None, will use get_spotify_client().
        country Optional (str): 2-letter country code (e.g., 'US', 'GB', 'IN').

    Returns:
        List[Dict]: List of dicts with top track info, or error dict.
    """
    try:
        if not sp:
            sp = get_spotify_client()  # Replace with your project’s Spotipy client factory

        results = sp.artist_top_tracks(artist_id, country=country)
        tracks = results.get("tracks", [])
        return process_artist_top_tracks(tracks)
    except Exception as e:
        print(f"An error occurred while fetching artist top tracks: {e}")
        return {"error": str(e)}
