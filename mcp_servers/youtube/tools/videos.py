import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError

from ..utils import get_auth_token, get_youtube_service, get_youtube_analytics_service, _make_youtube_request

logger = logging.getLogger(__name__)

async def get_video_details(video_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific YouTube video."""
    logger.info(f"Executing tool: get_video_details with video_id: {video_id}")
    try:
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id
        }
        
        result = await _make_youtube_request("videos", params)
        
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


async def get_video_comments(video_id: str, max_results: int = 20, order: str = "relevance") -> Dict[str, Any]:
    """
    Get top-level comments for a video.
    
    Args:
        video_id: The YouTube video ID
        max_results: Maximum number of comments to return (default: 20)
        order: Sort order - "relevance" or "time"
    """
    logger.info(f"Executing tool: get_video_comments with video_id: {video_id}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        request = service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_results, 100),
            order=order,
            textFormat="plainText"
        )
        response = request.execute()
        
        comments = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            comments.append({
                "id": item.get("id"),
                "authorDisplayName": snippet.get("authorDisplayName"),
                "textDisplay": snippet.get("textDisplay"),
                "likeCount": snippet.get("likeCount"),
                "publishedAt": snippet.get("publishedAt"),
                "updatedAt": snippet.get("updatedAt"),
                "totalReplyCount": item.get("snippet", {}).get("totalReplyCount", 0)
            })
            
        return {
            "video_id": video_id,
            "comments": comments,
            "total_count": len(comments),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_video_comments: {e}")
        raise e
