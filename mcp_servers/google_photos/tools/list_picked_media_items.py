import json
import logging
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError
from .base import get_picker_service_with_credentials, format_picker_media_item

logger = logging.getLogger(__name__)


async def google_photos_list_picked_media_items(access_token: str, sessionId: str, pageSize: int = 50, pageToken: Optional[str] = None) -> Dict[str, Any]:
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
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
            message = error_detail.get('error', {}).get('message', 'Unknown error')
        except Exception:
            message = str(e)
        raise RuntimeError(f"Google Photos Picker API Error ({getattr(e.resp, 'status', 'HTTP_ERROR')}): {message}")
    except Exception:
        raise
