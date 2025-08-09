from typing import Any
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_API_BASE = os.getenv("SPOTIFY_API_BASE", "https://api.spotify.com/v1")
ACCESS_TOKEN = os.getenv("SPOTIFY_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise ValueError("ACCESS_TOKEN is missing! Please set SPOTIFY_ACCESS_TOKEN in your .env file.")

async def make_spotify_request(url: str) -> dict[str, Any] | None:
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code} {e.response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

def format_track(track: dict) -> str:
    return f"""
Track: {track.get('name')}
Artist(s): {', '.join([artist['name'] for artist in track['artists']])}
Album: {track['album']['name']}
Preview URL: {track.get('preview_url') or 'N/A'}
"""
