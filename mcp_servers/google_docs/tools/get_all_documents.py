"""Get all documents tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_drive_service

logger = logging.getLogger(__name__)


async def get_all_documents() -> Dict[str, Any]:
    """Get all Google Docs documents from the user's Drive."""
    logger.info("Executing tool: get_all_documents")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)

        # Query for Google Docs files
        query = "mimeType='application/vnd.google-apps.document'"

        request = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc"
        )
        response = request.execute()

        documents = []
        for file in response.get('files', []):
            documents.append({
                'id': file['id'],
                'name': file['name'],
                'createdAt': file.get('createdTime'),
                'modifiedAt': file.get('modifiedTime'),
                'url': file.get('webViewLink')
            })

        return {
            'documents': documents,
            'total_count': len(documents)
        }
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_all_documents: {e}")
        raise e
