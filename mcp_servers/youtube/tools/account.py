import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from googleapiclient.errors import HttpError

from ..utils import get_auth_token, get_youtube_service
from .channels import get_my_channel_info

logger = logging.getLogger(__name__)

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
