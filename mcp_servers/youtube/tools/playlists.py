import json
import logging
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError

from ..utils import get_auth_token, get_youtube_service

logger = logging.getLogger(__name__)

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


async def list_playlists(channel_id: Optional[str] = None, mine: bool = False, max_results: int = 25) -> Dict[str, Any]:
    """
    List playlists for a channel or the authenticated user.
    
    Args:
        channel_id: Optional channel ID to list playlists for
        mine: Whether to list the authenticated user's playlists (default: False)
        max_results: Maximum number of playlists to return
    """
    logger.info(f"Executing tool: list_playlists")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        kwargs = {
            "part": "snippet,contentDetails",
            "maxResults": min(max_results, 50)
        }
        
        if mine:
            kwargs["mine"] = True
        elif channel_id:
            kwargs["channelId"] = channel_id
        else:
            # Default to mine if nothing specified
            kwargs["mine"] = True
            
        request = service.playlists().list(**kwargs)
        response = request.execute()
        
        playlists = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})
            playlists.append({
                "id": item.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "publishedAt": snippet.get("publishedAt"),
                "itemCount": content_details.get("itemCount"),
                "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "url": f"https://www.youtube.com/playlist?list={item.get('id')}"
            })
            
        return {
            "playlists": playlists,
            "total_count": len(playlists),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool list_playlists: {e}")
        raise e


async def get_playlist_items(playlist_id: str, max_results: int = 25) -> Dict[str, Any]:
    """
    Get items from a playlist.
    
    Args:
        playlist_id: The ID of the playlist
        max_results: Maximum number of items to return
    """
    logger.info(f"Executing tool: get_playlist_items with playlist_id: {playlist_id}")
    try:
        access_token = get_auth_token()
        service = get_youtube_service(access_token)
        
        request = service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        
        items = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            items.append({
                "id": item.get("id"),
                "videoId": video_id,
                "title": snippet.get("title"),
                "description": snippet.get("description", "")[:200] + "..." if len(snippet.get("description", "")) > 200 else snippet.get("description", ""),
                "publishedAt": snippet.get("publishedAt"),
                "position": snippet.get("position"),
                "thumbnailUrl": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None
            })
            
        return {
            "playlist_id": playlist_id,
            "items": items,
            "total_count": len(items),
            "next_page_token": response.get("nextPageToken")
        }
    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"YouTube API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_playlist_items: {e}")
        raise e
