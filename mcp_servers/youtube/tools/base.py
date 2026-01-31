"""
Base utilities for YouTube MCP Server tools.
"""

import base64
import json
import logging
import os
from contextvars import ContextVar
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs

import aiohttp
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# YouTube API constants and configuration
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
TRANSCRIPT_LANGUAGES = [lang.strip() for lang in os.getenv("TRANSCRIPT_LANGUAGE", "en").split(',')]

# Proxy configuration for transcript API
WEBSHARE_PROXY_USERNAME = os.getenv("WEBSHARE_PROXY_USERNAME")
WEBSHARE_PROXY_PASSWORD = os.getenv("WEBSHARE_PROXY_PASSWORD")

# Initialize YouTube Transcript API with proxy if credentials are available
if WEBSHARE_PROXY_USERNAME and WEBSHARE_PROXY_PASSWORD:
    logger.info("Initializing YouTubeTranscriptApi with Webshare proxy")
    youtube_transcript_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=WEBSHARE_PROXY_USERNAME,
            proxy_password=WEBSHARE_PROXY_PASSWORD,
            retries_when_blocked=50
        )
    )
else:
    logger.info("Initializing YouTubeTranscriptApi without proxy")
    youtube_transcript_api = YouTubeTranscriptApi()


def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
    
    if not auth_data:
        return ""
    
    try:
        # Parse the JSON auth data to extract access_token
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""


def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")


def get_youtube_service(access_token: str):
    """Create YouTube Data API service with OAuth access token."""
    credentials = Credentials(token=access_token)
    return build('youtube', 'v3', credentials=credentials)


def get_youtube_analytics_service(access_token: str):
    """Create YouTube Analytics API service with OAuth access token."""
    credentials = Credentials(token=access_token)
    return build('youtubeAnalytics', 'v2', credentials=credentials)


def _format_time(seconds: float) -> str:
    """Converts seconds into HH:MM:SS or MM:SS format."""
    total_seconds = int(seconds)
    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    else:
        return f"{minutes:02d}:{sec:02d}"


def _extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from various URL formats.
    Supports standard youtube.com URLs and youtu.be short URLs.
    
    Args:
        url: YouTube URL in various formats
        
    Returns:
        The video ID extracted from the URL
        
    Raises:
        ValueError: If the URL is not a valid YouTube URL or if video ID couldn't be extracted
    """
    if not url:
        raise ValueError("Empty URL provided")
        
    # Pattern 1: Standard YouTube URL (youtube.com/watch?v=VIDEO_ID)
    if "youtube.com/watch" in url:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_ids = query_params.get("v")
        if video_ids and len(video_ids[0]) > 0:
            return video_ids[0]
            
    # Pattern 2: Short YouTube URL (youtu.be/VIDEO_ID)
    if "youtu.be/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/"):
            return path[1:].split("?")[0]
            
    # Pattern 3: Embedded YouTube URL (youtube.com/embed/VIDEO_ID)
    if "youtube.com/embed/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/embed/"):
            return path[7:].split("?")[0]
            
    # Pattern 4: YouTube shorts URL (youtube.com/shorts/VIDEO_ID)
    if "youtube.com/shorts/" in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and path.startswith("/shorts/"):
            return path[8:].split("?")[0]
    
    raise ValueError(f"Could not extract video ID from URL: {url}")


async def _make_youtube_request(endpoint: str, params: Dict[str, Any], access_token: Optional[str] = None) -> Any:
    """
    Makes an HTTP request to the YouTube Data API using OAuth access token.
    """
    url = f"{YOUTUBE_API_BASE}/{endpoint}"
    
    # Use provided access token or get from context
    if not access_token:
        access_token = get_auth_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                if endpoint == "captions/download":
                    return await response.text()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"YouTube API request failed: {e.status} {e.message} for GET {url}")
            error_details = e.message
            try:
                error_body = await e.response.json()
                error_details = f"{e.message} - {error_body}"
            except Exception:
                pass
            raise RuntimeError(f"YouTube API Error ({e.status}): {error_details}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube API request: {e}")
            raise RuntimeError(f"Unexpected error during API call to {url}") from e
