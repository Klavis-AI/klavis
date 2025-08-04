import os
from typing import Optional
from contextvars import ContextVar
import requests
import base64

auth_token_context: ContextVar[str] = ContextVar('auth_token', default="")


def get_spotify_token() -> str:
    """Get Notion client with authentication token from context or environment."""
    # Try to get token from context first (for HTTP requests)
    
    if auth_token_context.get() != "":
        return auth_token_context.get()
  
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Spotify client ID and secret not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")
    
    auth_token = get_auth_token(client_id, client_secret)

    if not auth_token:
        raise ValueError("Failed to retrieve Spotify access token. Check your client ID and secret.")
    
    auth_token_context.set(auth_token)
    return auth_token

def get_auth_token(client_id ,client_secret) -> str:

    # Encode as Base64
    credentials = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    access_token = response.json()["access_token"]
    return access_token