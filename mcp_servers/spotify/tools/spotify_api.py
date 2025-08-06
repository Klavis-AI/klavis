import os
import json
import base64
import time
import httpx
from mcp import ErrorData, McpError
from mcp.types import INTERNAL_ERROR
from typing import Optional, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Load environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

class SpotifyAPI:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    _access_token: str = ""
    _expires_at: float = 0.0
    
    @classmethod
    async def ensure_token(cls) -> str:
        if time.time() < cls._expires_at - 60:
            return cls._access_token
        
        # Debug prints for troubleshooting
        print(f"Authenticating with Spotify API...")
        print(f"Client ID exists: {'Yes' if SPOTIFY_CLIENT_ID else 'No'}")
        print(f"Client Secret exists: {'Yes' if SPOTIFY_CLIENT_SECRET else 'No'}")
        
        # Check if credentials are missing
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            error_msg = "Missing Spotify API credentials. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file."
            print(f"⚠️ {error_msg}")
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))
            
        # For full access with user context (if refresh token available)
        if SPOTIFY_REFRESH_TOKEN:
            print("Using refresh token authentication flow")
            data = {
                "grant_type": "refresh_token",
                "refresh_token": SPOTIFY_REFRESH_TOKEN,
            }
            auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {encoded_auth}"
            }
        else:
            # Client credentials flow
            print("Using client credentials authentication flow")
            data = {
                "grant_type": "client_credentials",
            }
            auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
        async with httpx.AsyncClient() as client:
            try:
                print(f"Making auth request to: {cls.TOKEN_URL}")
                print(f"With headers: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in headers.items()})}")
                print(f"With data: {json.dumps({k: '***' if k in ['refresh_token'] else v for k, v in data.items()})}")
                
                r = await client.post(cls.TOKEN_URL, data=data, headers=headers)
                
                print(f"Auth response status: {r.status_code}")
                if r.status_code != 200:
                    error_detail = f"HTTP {r.status_code}: {r.text}"
                    print(f"Spotify auth failed: {error_detail}")
                    
                    if r.status_code == 400 and "invalid_client" in r.text:
                        error_msg = (
                            "Invalid Spotify client credentials. Please check that:\n"
                            "1. Your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are correct\n"
                            "2. The credentials are for a valid Spotify app\n"
                            "3. The credentials are properly formatted in your .env file with no extra spaces"
                        )
                    else:
                        error_msg = f"Spotify auth failed: {error_detail}"
                        
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))
                
                resp = r.json()
                cls._access_token = resp["access_token"]
                cls._expires_at = time.time() + resp.get("expires_in", 3600)
                print("Authentication successful! Token obtained.")
                return cls._access_token
            except httpx.RequestError as e:
                error_msg = f"Connection error: {str(e)}"
                print(error_msg)
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

    @classmethod
    async def get(cls, path: str, params: Optional[dict] = None) -> Any:
        token = await cls.ensure_token()
        url = f"{cls.API_BASE}/{path}"
        headers = {"Authorization": f"Bearer {token}"}
        
        # Debug logs
        print(f"Making GET request to: {url}")
        if params:
            print(f"With params: {params}")
        
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(url, headers=headers, params=params)
                
                # Debug response
                print(f"Response status: {r.status_code}")
                
                if r.status_code >= 400:
                    error_detail = f"HTTP {r.status_code}: {r.text}"
                    print(f"Spotify API error: {error_detail}")
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Spotify GET {path} failed: {error_detail}"))
                
                return r.json()
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                print(error_msg)
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))

    @classmethod
    async def post(cls, path: str, json_body: dict) -> Any:
        token = await cls.ensure_token()
        url = f"{cls.API_BASE}/{path}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Debug logs
        print(f"Making POST request to: {url}")
        print(f"With body: {json.dumps(json_body)}")
        
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url, headers=headers, json=json_body)
                
                # Debug response
                print(f"Response status: {r.status_code}")
                
                if r.status_code >= 400:
                    error_detail = f"HTTP {r.status_code}: {r.text}"
                    print(f"Spotify API error: {error_detail}")
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Spotify POST {path} failed: {error_detail}"))
                
                return r.json()
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                print(error_msg)
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=error_msg))