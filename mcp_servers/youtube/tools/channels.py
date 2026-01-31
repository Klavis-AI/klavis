import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError

from .base import get_auth_token, get_youtube_service, get_youtube_analytics_service

logger = logging.getLogger(__name__)

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
