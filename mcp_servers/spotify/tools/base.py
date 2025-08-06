import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from contextvars import ContextVar
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

auth_token_context: ContextVar[str] = ContextVar('auth_token', default="")
authorization_scope="user-library-read playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-follow-modify user-follow-read user-read-playback-position user-top-read user-read-recently-played user-library-modify user-library-read  "

def get_user_spotify_client():
    """
    Initiates user-authenticated Spotipy client (prompts for login in browser on first run).
    Returns the Spotipy client and tokens dict.
    """
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")      # or hardcode
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")  # or hardcode
    REDIRECT_URI = "https://www.google.com"     # Must be registered in Spotify Dashboard
    
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=authorization_scope,
        cache_path=".webassets-cache",  
        show_dialog=True
    )
    token_info = sp_oauth.get_cached_token()
    if not token_info or not sp_oauth.validate_token(token_info):
        # Opens browser for user to login and/or consent
        token_info = sp_oauth.get_access_token(as_dict=True)

    sp = spotipy.Spotify(auth=token_info["access_token"])
    return sp, token_info


def get_spotify_client() -> Spotify:
    """
    Get a Spotipy Spotify client.
    
    This uses Client Credentials flow with token caching managed by Spotipy.
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Spotify client ID and secret not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

    credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    spotify = Spotify(client_credentials_manager=credentials_manager)
    return spotify


def get_spotify_access_token() -> str:
    """
    Get Spotify access token from Spotipy's credentials manager and cache in contextvar.
    """
    token = auth_token_context.get()
    if token:
        return token

    spotify = get_spotify_client()
    access_token = spotify._auth_manager.get_access_token(as_dict=False)  # get raw access token string
    auth_token_context.set(access_token)
    return access_token





