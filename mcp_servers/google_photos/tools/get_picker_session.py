import json
import logging
from typing import Any, Dict
from googleapiclient.errors import HttpError
from .base import get_picker_service_with_credentials

logger = logging.getLogger(__name__)


async def google_photos_get_picker_session(access_token: str, sessionId: str) -> Dict[str, Any]:
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
        try:
            error_detail = json.loads(e.content.decode('utf-8'))
            message = error_detail.get('error', {}).get('message', 'Unknown error')
        except Exception:
            message = str(e)
        raise RuntimeError(f"Google Photos Picker API Error ({getattr(e.resp, 'status', 'HTTP_ERROR')}): {message}")
    except Exception:
        raise
