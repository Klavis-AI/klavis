import contextlib
import base64
import logging
import os
import re
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs
from contextvars import ContextVar
from datetime import datetime, timedelta

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from pydantic import Field
from dotenv import load_dotenv
import aiohttp
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

# YouTube API constants and configuration
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_MCP_SERVER_PORT = int(os.getenv("YOUTUBE_MCP_SERVER_PORT", "5000"))
TRANSCRIPT_LANGUAGES = [lang.strip() for lang in os.getenv("TRANSCRIPT_LANGUAGE", "en").split(',')]

# Proxy configuration for transcript API
WEBSHARE_PROXY_USERNAME = os.getenv("WEBSHARE_PROXY_USERNAME")
WEBSHARE_PROXY_PASSWORD = os.getenv("WEBSHARE_PROXY_PASSWORD")


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

async def get_video_details(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific YouTube video."""
    logger.info(f"Executing tool: get_video_details with video_id: {video_id}")
    try:
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id
        }
        
        result = await _make_youtube_request("captions", params)
        
        if not result.get("items"):
            return {"error": f"No video found with ID: {video_id}"}
        
        video = result["items"][0]
        snippet = video.get("snippet", {})
        content_details = video.get("contentDetails", {})
        statistics = video.get("statistics", {})
        
        return {
            "id": video.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "publishedAt": snippet.get("publishedAt"),
            "channelId": snippet.get("channelId"),
            "channelTitle": snippet.get("channelTitle"),
            "thumbnailUrl": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "tags": snippet.get("tags", []),
            "categoryId": snippet.get("categoryId"),
            "duration": content_details.get("duration"),
            "viewCount": statistics.get("viewCount"),
            "likeCount": statistics.get("likeCount"),
            "commentCount": statistics.get("commentCount"),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }
    except Exception as e:
        logger.exception(f"Error executing tool get_video_details: {e}")
        raise e


# ============================================================================
# OAuth-based YouTube API Tools (require user authentication)
# ============================================================================

async def get_liked_videos(max_results: int = 25) -> Dict[str, Any]:
    """Get the user's liked/favorite videos from their YouTube account."""
    logger.info(f"Executing tool: get_liked_videos with max_results: {max_results}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # Get the user's liked videos playlist
        request = service.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        
        videos = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            videos.append({
                "id": item.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                "channelTitle": snippet.get("channelTitle"),
                "publishedAt": snippet.get("publishedAt"),
                "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "viewCount": statistics.get("viewCount"),
                "likeCount": statistics.get("likeCount"),
                "url": f"https://www.youtube.com/watch?v={item.get('id')}"
            })
        
        return {
            "liked_videos": videos,
            "total_count": len(videos),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_liked_videos: {e}")
        raise e


async def get_user_subscriptions(max_results: int = 25) -> Dict[str, Any]:
    """Get the user's channel subscriptions."""
    logger.info(f"Executing tool: get_user_subscriptions with max_results: {max_results}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        request = service.subscriptions().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=min(max_results, 50),
            order="relevance"
        )
        response = request.execute()
        
        subscriptions = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            resource_id = snippet.get("resourceId", {})
            subscriptions.append({
                "subscriptionId": item.get("id"),
                "channelId": resource_id.get("channelId"),
                "channelTitle": snippet.get("title"),
                "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "channelUrl": f"https://www.youtube.com/channel/{resource_id.get('channelId')}"
            })
        
        return {
            "subscriptions": subscriptions,
            "total_count": len(subscriptions),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_user_subscriptions: {e}")
        raise e


async def get_my_channel_info() -> Dict[str, Any]:
    """Get information about the authenticated user's YouTube channel."""
    logger.info("Executing tool: get_my_channel_info")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        request = service.channels().list(
            part="snippet,contentDetails,statistics,brandingSettings",
            mine=True
        )
        response = request.execute()
        
        if not response.get("items"):
            return {"error": "No channel found for this user"}
        
        channel = response["items"][0]
        snippet = channel.get("snippet", {})
        statistics = channel.get("statistics", {})
        content_details = channel.get("contentDetails", {})
        
        return {
            "channelId": channel.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "customUrl": snippet.get("customUrl"),
            "publishedAt": snippet.get("publishedAt"),
            "thumbnailUrl": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "subscriberCount": statistics.get("subscriberCount"),
            "videoCount": statistics.get("videoCount"),
            "viewCount": statistics.get("viewCount"),
            "uploadsPlaylistId": content_details.get("relatedPlaylists", {}).get("uploads"),
            "channelUrl": f"https://www.youtube.com/channel/{channel.get('id')}"
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_my_channel_info: {e}")
        raise e


async def get_my_videos(max_results: int = 25) -> Dict[str, Any]:
    """Get the authenticated user's uploaded videos."""
    logger.info(f"Executing tool: get_my_videos with max_results: {max_results}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # First, get the uploads playlist ID
        channel_info = await get_my_channel_info()
        uploads_playlist_id = channel_info.get("uploadsPlaylistId")
        
        if not uploads_playlist_id:
            return {"error": "Could not find uploads playlist for this channel"}
        
        # Get videos from the uploads playlist
        request = service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        
        video_ids = [item.get("contentDetails", {}).get("videoId") for item in response.get("items", [])]
        
        # Get detailed statistics for each video
        if video_ids:
            videos_request = service.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            )
            videos_response = videos_request.execute()
            
            videos = []
            for video in videos_response.get("items", []):
                snippet = video.get("snippet", {})
                statistics = video.get("statistics", {})
                videos.append({
                    "id": video.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                    "publishedAt": snippet.get("publishedAt"),
                    "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                    "viewCount": statistics.get("viewCount"),
                    "likeCount": statistics.get("likeCount"),
                    "commentCount": statistics.get("commentCount"),
                    "url": f"https://www.youtube.com/watch?v={video.get('id')}"
                })
            
            return {
                "videos": videos,
                "total_count": len(videos),
                "next_page_token": response.get("nextPageToken")
            }
        
        return {"videos": [], "total_count": 0}
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_my_videos: {e}")
        raise e


async def search_videos(query: str, max_results: int = 10, channel_id: Optional[str] = None, 
                        published_after: Optional[str] = None, published_before: Optional[str] = None,
                        order: str = "relevance") -> Dict[str, Any]:
    """
    Search for YouTube videos by query, optionally filtered by channel or date range.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default 10, max 50)
        channel_id: Optional channel ID to search within
        published_after: Optional ISO 8601 date string (e.g., "2024-01-01T00:00:00Z")
        published_before: Optional ISO 8601 date string
        order: Sort order - "relevance", "date", "viewCount", "rating"
    """
    logger.info(f"Executing tool: search_videos with query: {query}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": order
        }
        
        if channel_id:
            search_params["channelId"] = channel_id
        if published_after:
            search_params["publishedAfter"] = published_after
        if published_before:
            search_params["publishedBefore"] = published_before
        
        request = service.search().list(**search_params)
        response = request.execute()
        
        # Get video IDs to fetch additional details
        video_ids = [item.get("id", {}).get("videoId") for item in response.get("items", []) if item.get("id", {}).get("videoId")]
        
        videos = []
        if video_ids:
            # Get detailed statistics
            videos_request = service.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            )
            videos_response = videos_request.execute()
            
            for video in videos_response.get("items", []):
                snippet = video.get("snippet", {})
                statistics = video.get("statistics", {})
                videos.append({
                    "id": video.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                    "channelId": snippet.get("channelId"),
                    "channelTitle": snippet.get("channelTitle"),
                    "publishedAt": snippet.get("publishedAt"),
                    "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                    "viewCount": statistics.get("viewCount"),
                    "likeCount": statistics.get("likeCount"),
                    "commentCount": statistics.get("commentCount"),
                    "url": f"https://www.youtube.com/watch?v={video.get('id')}"
                })
        
        return {
            "query": query,
            "videos": videos,
            "total_count": len(videos),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool search_videos: {e}")
        raise e


async def get_channel_videos(channel_id: str, max_results: int = 25) -> Dict[str, Any]:
    """Get videos from a specific YouTube channel."""
    logger.info(f"Executing tool: get_channel_videos with channel_id: {channel_id}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # First, get channel info to find the uploads playlist
        channel_request = service.channels().list(
            part="contentDetails,snippet",
            id=channel_id
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get("items"):
            return {"error": f"No channel found with ID: {channel_id}"}
        
        channel = channel_response["items"][0]
        channel_title = channel.get("snippet", {}).get("title")
        uploads_playlist_id = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        
        if not uploads_playlist_id:
            return {"error": "Could not find uploads playlist for this channel"}
        
        # Get videos from the uploads playlist
        request = service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        
        video_ids = [item.get("contentDetails", {}).get("videoId") for item in response.get("items", [])]
        
        videos = []
        if video_ids:
            videos_request = service.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            )
            videos_response = videos_request.execute()
            
            for video in videos_response.get("items", []):
                snippet = video.get("snippet", {})
                statistics = video.get("statistics", {})
                videos.append({
                    "id": video.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                    "publishedAt": snippet.get("publishedAt"),
                    "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                    "viewCount": statistics.get("viewCount"),
                    "likeCount": statistics.get("likeCount"),
                    "commentCount": statistics.get("commentCount"),
                    "url": f"https://www.youtube.com/watch?v={video.get('id')}"
                })
        
        return {
            "channelId": channel_id,
            "channelTitle": channel_title,
            "videos": videos,
            "total_count": len(videos),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_channel_videos: {e}")
        raise e


async def search_channels(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for YouTube channels by name or keywords."""
    logger.info(f"Executing tool: search_channels with query: {query}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        request = service.search().list(
            part="snippet",
            q=query,
            type="channel",
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        
        channel_ids = [item.get("id", {}).get("channelId") for item in response.get("items", []) if item.get("id", {}).get("channelId")]
        
        channels = []
        if channel_ids:
            # Get detailed channel info
            channels_request = service.channels().list(
                part="snippet,statistics",
                id=",".join(channel_ids)
            )
            channels_response = channels_request.execute()
            
            for channel in channels_response.get("items", []):
                snippet = channel.get("snippet", {})
                statistics = channel.get("statistics", {})
                channels.append({
                    "channelId": channel.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                    "customUrl": snippet.get("customUrl"),
                    "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                    "subscriberCount": statistics.get("subscriberCount"),
                    "videoCount": statistics.get("videoCount"),
                    "viewCount": statistics.get("viewCount"),
                    "channelUrl": f"https://www.youtube.com/channel/{channel.get('id')}"
                })
        
        return {
            "query": query,
            "channels": channels,
            "total_count": len(channels)
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool search_channels: {e}")
        raise e


async def get_my_channel_analytics(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get analytics for the authenticated user's YouTube channel.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
    """
    logger.info(f"Executing tool: get_my_channel_analytics")
    try:
        access_token = get_auth_token()
        analytics_service = get_youtube_analytics_service(access_token)
        youtube_service = get_youtube_service(access_token)
        
        # Get channel ID first
        channel_request = youtube_service.channels().list(
            part="id",
            mine=True
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get("items"):
            return {"error": "No channel found for this user"}
        
        channel_id = channel_response["items"][0]["id"]
        
        # Set default date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get channel analytics
        request = analytics_service.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes,dislikes,comments,shares,subscribersGained,subscribersLost",
            dimensions="day",
            sort="day"
        )
        response = request.execute()
        
        # Process the response
        column_headers = [header["name"] for header in response.get("columnHeaders", [])]
        rows = response.get("rows", [])
        
        daily_data = []
        for row in rows:
            day_data = dict(zip(column_headers, row))
            daily_data.append(day_data)
        
        # Calculate totals
        totals = {}
        if rows:
            for i, header in enumerate(column_headers):
                if header != "day":
                    totals[header] = sum(row[i] for row in rows if isinstance(row[i], (int, float)))
        
        return {
            "channelId": channel_id,
            "dateRange": {
                "startDate": start_date,
                "endDate": end_date
            },
            "totals": totals,
            "dailyData": daily_data
        }
    except HttpError as e:
        logger.error(f"YouTube Analytics API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube Analytics API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_my_channel_analytics: {e}")
        raise e


async def get_my_video_analytics(video_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get analytics for a specific video on the authenticated user's channel.
    
    Args:
        video_id: The YouTube video ID
        start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
    """
    logger.info(f"Executing tool: get_my_video_analytics with video_id: {video_id}")
    try:
        access_token = get_auth_token()
        analytics_service = get_youtube_analytics_service(access_token)
        youtube_service = get_youtube_service(access_token)
        
        # Get channel ID first
        channel_request = youtube_service.channels().list(
            part="id",
            mine=True
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get("items"):
            return {"error": "No channel found for this user"}
        
        channel_id = channel_response["items"][0]["id"]
        
        # Set default date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get video analytics
        request = analytics_service.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes,dislikes,comments,shares",
            dimensions="day",
            filters=f"video=={video_id}",
            sort="day"
        )
        response = request.execute()
        
        # Process the response
        column_headers = [header["name"] for header in response.get("columnHeaders", [])]
        rows = response.get("rows", [])
        
        daily_data = []
        for row in rows:
            day_data = dict(zip(column_headers, row))
            daily_data.append(day_data)
        
        # Calculate totals
        totals = {}
        if rows:
            for i, header in enumerate(column_headers):
                if header != "day":
                    totals[header] = sum(row[i] for row in rows if isinstance(row[i], (int, float)))
        
        return {
            "videoId": video_id,
            "dateRange": {
                "startDate": start_date,
                "endDate": end_date
            },
            "totals": totals,
            "dailyData": daily_data
        }
    except HttpError as e:
        logger.error(f"YouTube Analytics API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube Analytics API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_my_video_analytics: {e}")
        raise e


async def rate_video(video_id: str, rating: str) -> Dict[str, Any]:
    """
    Rate a video (like, dislike, or remove rating).
    
    Args:
        video_id: The YouTube video ID to rate
        rating: The rating to apply ('like', 'dislike', or 'none' to remove rating)
    """
    logger.info(f"Executing tool: rate_video with video_id: {video_id}, rating: {rating}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # Validate rating
        valid_ratings = ['like', 'dislike', 'none']
        if rating not in valid_ratings:
            raise ValueError(f"Invalid rating '{rating}'. Must be one of: {valid_ratings}")
        
        # Execute the rating
        service.videos().rate(
            id=video_id,
            rating=rating
        ).execute()
        
        return {
            "success": True,
            "video_id": video_id,
            "rating": rating,
            "message": f"Successfully {'removed rating from' if rating == 'none' else f'rated video as {rating}'}"
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool rate_video: {e}")
        raise e


async def create_playlist(title: str, description: str = "", privacy_status: str = "private") -> Dict[str, Any]:
    """
    Create a new YouTube playlist.
    
    Args:
        title: The title of the playlist
        description: The description of the playlist (optional)
        privacy_status: Privacy status ('public', 'private', or 'unlisted')
    """
    logger.info(f"Executing tool: create_playlist with title: {title}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # Validate privacy status
        valid_statuses = ['public', 'private', 'unlisted']
        if privacy_status not in valid_statuses:
            raise ValueError(f"Invalid privacy_status '{privacy_status}'. Must be one of: {valid_statuses}")
        
        # Create the playlist
        request_body = {
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }
        
        response = service.playlists().insert(
            part="snippet,status",
            body=request_body
        ).execute()
        
        playlist_id = response.get("id")
        return {
            "success": True,
            "playlist_id": playlist_id,
            "title": title,
            "description": description,
            "privacy_status": privacy_status,
            "url": f"https://www.youtube.com/playlist?list={playlist_id}",
            "message": f"Successfully created playlist '{title}'"
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_playlist: {e}")
        raise e


async def add_video_to_playlist(playlist_id: str, video_id: str, position: Optional[int] = None) -> Dict[str, Any]:
    """
    Add a video to a playlist.
    
    Args:
        playlist_id: The ID of the playlist to add the video to
        video_id: The YouTube video ID to add
        position: The position in the playlist (0-indexed, optional - adds to end if not specified)
    """
    logger.info(f"Executing tool: add_video_to_playlist with playlist_id: {playlist_id}, video_id: {video_id}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # Build the request body
        request_body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        
        # Add position if specified
        if position is not None:
            request_body["snippet"]["position"] = position
        
        response = service.playlistItems().insert(
            part="snippet",
            body=request_body
        ).execute()
        
        return {
            "success": True,
            "playlist_item_id": response.get("id"),
            "playlist_id": playlist_id,
            "video_id": video_id,
            "position": response.get("snippet", {}).get("position"),
            "message": f"Successfully added video to playlist"
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool add_video_to_playlist: {e}")
        raise e


async def get_recent_uploads(days: int = 14, max_results: int = 25) -> Dict[str, Any]:
    """
    Get videos uploaded within the specified number of days from subscribed channels.
    
    Args:
        days: Number of days to look back (default: 14)
        max_results: Maximum number of results to return (default: 25)
    """
    logger.info(f"Executing tool: get_recent_uploads with days: {days}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        # Calculate the date threshold
        published_after = (datetime.now() - timedelta(days=days)).isoformat() + "Z"
        
        # Get user's subscriptions first
        subs_request = service.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        subs_response = subs_request.execute()
        
        # Get channel IDs from subscriptions
        channel_ids = [
            item.get("snippet", {}).get("resourceId", {}).get("channelId")
            for item in subs_response.get("items", [])
        ]
        
        all_videos = []
        
        # Search for recent videos from each subscribed channel
        for channel_id in channel_ids[:10]:  # Limit to first 10 channels to avoid rate limits
            if not channel_id:
                continue
                
            search_request = service.search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                publishedAfter=published_after,
                order="date",
                maxResults=5
            )
            search_response = search_request.execute()
            
            for item in search_response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    all_videos.append({
                        "id": video_id,
                        "title": snippet.get("title"),
                        "channelTitle": snippet.get("channelTitle"),
                        "channelId": snippet.get("channelId"),
                        "publishedAt": snippet.get("publishedAt"),
                        "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })
        
        # Sort by published date (newest first) and limit results
        all_videos.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        all_videos = all_videos[:max_results]
        
        return {
            "days": days,
            "videos": all_videos,
            "total_count": len(all_videos)
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_recent_uploads: {e}")
        raise e


@click.command()
@click.option("--port", default=YOUTUBE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("youtube-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="get_youtube_video_transcript",
                description="Retrieve the transcript or video details for a given YouTube video. The 'start' time in the transcript is formatted as MM:SS or HH:MM:SS.",
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the YouTube video to retrieve the transcript/subtitles for. (e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_TRANSCRIPT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_liked_videos",
                description="Get the user's liked/favorite videos from their YouTube account. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_subscriptions",
                description="Get the user's channel subscriptions from their YouTube account. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of subscriptions to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_channel",
                description="Get information about the authenticated user's YouTube channel including subscriber count, video count, and total views. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_videos",
                description="Get the authenticated user's uploaded videos with statistics. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_search_videos",
                description="Search for YouTube videos by query, optionally filtered by channel or date range. Use this to find videos about specific topics from any YouTuber.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string (e.g., 'machine learning tutorial')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10, max: 50)",
                            "default": 10
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Optional: Filter results to a specific channel ID",
                        },
                        "published_after": {
                            "type": "string",
                            "description": "Optional: Only return videos published after this date (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')",
                        },
                        "published_before": {
                            "type": "string",
                            "description": "Optional: Only return videos published before this date (ISO 8601 format)",
                        },
                        "order": {
                            "type": "string",
                            "enum": ["relevance", "date", "viewCount", "rating"],
                            "description": "Sort order for results (default: 'relevance')",
                            "default": "relevance"
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_SEARCH", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_channel_videos",
                description="Get videos from a specific YouTube channel. Use this to browse a YouTuber's uploaded videos.",
                inputSchema={
                    "type": "object",
                    "required": ["channel_id"],
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The YouTube channel ID (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of videos to return (default: 25, max: 50)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_CHANNEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_search_channels",
                description="Search for YouTube channels by name or keywords. Use this to find a YouTuber's channel ID.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for channel name or keywords",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10, max: 50)",
                            "default": 10
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_SEARCH", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_my_analytics",
                description="Get analytics for the authenticated user's YouTube channel including views, watch time, likes, comments, and subscriber changes. Requires OAuth authentication with YouTube Analytics scope.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (default: 30 days ago)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (default: today)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_video_analytics",
                description="Get analytics for a specific video on the authenticated user's channel. Requires OAuth authentication with YouTube Analytics scope.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (default: 30 days ago)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (default: today)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ANALYTICS", "readOnlyHint": True}),
            ),
            types.Tool(
                name="youtube_get_recent_uploads",
                description="Get videos uploaded within the specified number of days from your subscribed channels. Great for seeing what's new from channels you follow. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 14)",
                            "default": 14
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 25)",
                            "default": 25
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": True}),
            ),
            # Write tools
            types.Tool(
                name="youtube_rate_video",
                description="Rate a YouTube video (like, dislike, or remove rating). Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "required": ["video_id", "rating"],
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID to rate",
                        },
                        "rating": {
                            "type": "string",
                            "enum": ["like", "dislike", "none"],
                            "description": "The rating to apply: 'like' to like the video, 'dislike' to dislike it, or 'none' to remove your rating",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_ACCOUNT", "readOnlyHint": False}),
            ),
            types.Tool(
                name="youtube_create_playlist",
                description="Create a new YouTube playlist on the authenticated user's channel. Requires OAuth authentication.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the playlist",
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the playlist (optional)",
                            "default": ""
                        },
                        "privacy_status": {
                            "type": "string",
                            "enum": ["public", "private", "unlisted"],
                            "description": "Privacy status of the playlist (default: 'private')",
                            "default": "private"
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": False}),
            ),
            types.Tool(
                name="youtube_add_video_to_playlist",
                description="Add a video to an existing YouTube playlist. Requires OAuth authentication and ownership of the playlist.",
                inputSchema={
                    "type": "object",
                    "required": ["playlist_id", "video_id"],
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "The ID of the playlist to add the video to",
                        },
                        "video_id": {
                            "type": "string",
                            "description": "The YouTube video ID to add to the playlist",
                        },
                        "position": {
                            "type": "integer",
                            "description": "The position in the playlist to insert the video (0-indexed). If not specified, the video is added to the end.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "YOUTUBE_PLAYLISTS", "readOnlyHint": False}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        ctx = app.request_context
        
        if name == "get_youtube_video_transcript":
            url = arguments.get("url")
            if not url:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: URL parameter is required",
                    )
                ]
            
            try:
                result = await get_youtube_video_transcript(url)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_liked_videos":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_liked_videos(max_results)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_subscriptions":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_user_subscriptions(max_results)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_my_channel":
            try:
                result = await get_my_channel_info()
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_my_videos":
            try:
                max_results = arguments.get("max_results", 25)
                result = await get_my_videos(max_results)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_search_videos":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await search_videos(
                    query=query,
                    max_results=arguments.get("max_results", 10),
                    channel_id=arguments.get("channel_id"),
                    published_after=arguments.get("published_after"),
                    published_before=arguments.get("published_before"),
                    order=arguments.get("order", "relevance")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_channel_videos":
            channel_id = arguments.get("channel_id")
            if not channel_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: channel_id parameter is required",
                    )
                ]
            
            try:
                result = await get_channel_videos(
                    channel_id=channel_id,
                    max_results=arguments.get("max_results", 25)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_search_channels":
            query = arguments.get("query")
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            
            try:
                result = await search_channels(
                    query=query,
                    max_results=arguments.get("max_results", 10)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_my_analytics":
            try:
                result = await get_my_channel_analytics(
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_video_analytics":
            video_id = arguments.get("video_id")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await get_my_video_analytics(
                    video_id=video_id,
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_get_recent_uploads":
            try:
                result = await get_recent_uploads(
                    days=arguments.get("days", 14),
                    max_results=arguments.get("max_results", 25)
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_rate_video":
            video_id = arguments.get("video_id")
            rating = arguments.get("rating")
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            if not rating:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: rating parameter is required",
                    )
                ]
            
            try:
                result = await rate_video(
                    video_id=video_id,
                    rating=rating
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_create_playlist":
            title = arguments.get("title")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title parameter is required",
                    )
                ]
            
            try:
                result = await create_playlist(
                    title=title,
                    description=arguments.get("description", ""),
                    privacy_status=arguments.get("privacy_status", "private")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "youtube_add_video_to_playlist":
            playlist_id = arguments.get("playlist_id")
            video_id = arguments.get("video_id")
            if not playlist_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: playlist_id parameter is required",
                    )
                ]
            if not video_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: video_id parameter is required",
                    )
                ]
            
            try:
                result = await add_video_to_playlist(
                    playlist_id=playlist_id,
                    video_id=video_id,
                    position=arguments.get("position")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )
        ]

    async def get_youtube_video_transcript(url: str) -> Dict[str, Any]:
        """
        Retrieve the transcript or video details for a given YouTube video.
        The 'start' time in the transcript is formatted as MM:SS or HH:MM:SS.
        """
        try:
            video_id = _extract_video_id(url)
            logger.info(f"Executing tool: get_video_transcript with video_id: {video_id}")
            
            try:
                # Use the initialized API with or without proxy
                raw_transcript = youtube_transcript_api.fetch(video_id, languages=TRANSCRIPT_LANGUAGES).to_raw_data()

                # Format the start time for each segment
                formatted_transcript = [
                    {**segment, 'start': _format_time(segment['start'])} 
                    for segment in raw_transcript
                ]

                return {
                    "video_id": video_id,
                    "transcript": formatted_transcript
                }
            except Exception as transcript_error:
                logger.warning(f"Error fetching transcript: {transcript_error}. Falling back to video details.")
                # Fall back to get_video_details
                video_details = await get_video_details(video_id)
                return {
                    "video_id": video_id,
                    "video_details": video_details,
                }
        except ValueError as e:
            logger.exception(f"Invalid YouTube URL: {e}")
            return {
                "error": f"Invalid YouTube URL: {str(e)}"
            }
        except Exception as e:
            error_message = str(e)
            logger.exception(f"Error processing video URL {url}: {error_message}")
            return {
                "error": f"Failed to process request: {error_message}"
            }

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers
        auth_token = extract_access_token(request)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers
        auth_token = extract_access_token(scope)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main() 