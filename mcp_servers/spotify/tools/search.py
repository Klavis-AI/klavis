from .base import get_spotify_client
from typing import List
import json 
from spotipy import Spotify
def process_spotify_items(items, type):
    """
    Process Spotify API items and extract relevant fields based on type.
    
    Args:
        items (list): List of Spotify API item dicts.
        type (str): One of 'track', 'album', 'artist', 'episode', 'show', 'playlist', 'audiobook'.

    Returns:
        list: List of simplified dicts with relevant metadata for each item.
    """
    output = []
    for item in items:
        if type == "track":
            output.append({
                "track_id": item.get("id"),
                "name": item.get("name"),
                "artists": [artist["name"] for artist in item.get("artists", [])],
                "album": item.get("album", {}).get("name"),
                "duration_ms": item.get("duration_ms"),
                "popularity": item.get("popularity"),
                "explicit": item.get("explicit"),
                "external_url": item.get("external_urls", {}).get("spotify")
            })

        elif type == "album":
            output.append({
                "album_id": item.get("id"),
                "name": item.get("name"),
                "artists": [artist["name"] for artist in item.get("artists", [])],
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
                "external_url": item.get("external_urls", {}).get("spotify")
            })

        elif type == "playlist":
            output.append({
                "playlist_id": item.get("id"),
                "name": item.get("name"),
                "owner": item.get("owner", {}).get("display_name"),
                "tracks_count": item.get("tracks", {}).get("total"),
                "description": item.get("description"),
                "public": item.get("public"),
                "external_url": item.get("external_urls", {}).get("spotify")
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
                "external_url": item.get("external_urls", {}).get("spotify")
            })

        else:
            # Default fallback: just include id, name and URL
            output.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "external_url": item.get("external_urls", {}).get("spotify"),
            })

    return output


def search_tracks(query: str, type: str = "track", limit: int = 10,sp: Spotify = None) -> list:
    """
    Search Spotify and return processed simplified result dicts.
    """
    try:
        sp = get_spotify_client()
        results = sp.search(q=query, type=type, limit=limit)
        items = results.get(type + "s", {}).get("items", [])

        return process_spotify_items(items, type)

    except Exception as e:
        print(f"An error occurred while searching for {type}s: {e}")
        return {"error": str(e)}


# Example usage (if needed):
# if __name__ == "__main__":
#     results = search_tracks("The Beatles", "artist", 5)
#     for r in results:
#         print(r)
