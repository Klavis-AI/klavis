# tools/picker.py
"""
Google Photos Picker API tool implementations for MCP server.
"""
import os
import json
import logging
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError
from utils import get_picker_service, format_picker_media_item

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def get_picker_service_with_credentials(access_token: str):
    return get_picker_service(
        access_token,
        GOOGLE_REFRESH_TOKEN,
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        GOOGLE_TOKEN_URI,
    )

async def google_photos_create_picker_session(access_token: str) -> Dict[str, Any]:
    logger.info("Executing tool: google_photos_create_picker_session")
    try:
        service = get_picker_service_with_credentials(access_token)
        request = service.sessions().create()
        response = request.execute()
        return {
            "sessionId": response.get('id'),
            "pickerUri": response.get('pickerUri'),
            "status": response.get('status')
        }
    except HttpError as e:
        logger.error(f"Google Photos Picker API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Photos Picker API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool google_photos_create_picker_session: {e}")
        raise e

async def google_photos_get_picker_session(access_token: str, sessionId: str) -> Dict[str, Any]:
    logger.info(f"Executing tool: google_photos_get_picker_session with session_id: {sessionId}")
    try:
        service = get_picker_service_with_credentials(access_token)
        request = service.sessions().get(sessionId=sessionId)
        response = request.execute()
        return {
            "sessionId": response.get('id'),
            "status": response.get('status'),
            "mediaItemsSet": response.get('mediaItemsSet', False)
        }
    except HttpError as e:
        logger.error(f"Google Photos Picker API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Photos Picker API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool google_photos_get_picker_session: {e}")
        raise e

async def google_photos_list_picked_media_items(access_token: str, sessionId: str, pageSize: int = 50, pageToken: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"Executing tool: google_photos_list_picked_media_items with session_id: {sessionId}")
    try:
        service = get_picker_service_with_credentials(access_token)
        params = {
            "sessionId": sessionId,
            "pageSize": min(pageSize, 100)
        }
        if pageToken:
            params["pageToken"] = pageToken
        request = service.mediaItems().list(**params)
        response = request.execute()
        media_items = [format_picker_media_item(item) for item in response.get('mediaItems', [])]
        return {
            "sessionId": sessionId,
            "mediaItems": media_items,
            "nextPageToken": response.get('nextPageToken'),
            "totalCount": len(media_items)
        }
    except HttpError as e:
        logger.error(f"Google Photos Picker API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Photos Picker API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool google_photos_list_picked_media_items: {e}")
        raise e

async def google_photos_delete_picker_session(access_token: str, sessionId: str) -> Dict[str, Any]:
    logger.info(f"Executing tool: google_photos_delete_picker_session with session_id: {sessionId}")
    try:
        service = get_picker_service_with_credentials(access_token)
        request = service.sessions().delete(sessionId=sessionId)
        request.execute()
        return {"message": f"Session {sessionId} deleted successfully"}
    except HttpError as e:
        logger.error(f"Google Photos Picker API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Photos Picker API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool google_photos_delete_picker_session: {e}")
        raise e
