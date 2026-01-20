"""Create blank document tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service

logger = logging.getLogger(__name__)


async def create_blank_document(title: str) -> Dict[str, Any]:
    """Create a new blank Google Docs document with a title."""
    logger.info(f"Executing tool: create_blank_document with title: {title}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        body = {"title": title}

        request = service.documents().create(body=body)
        response = request.execute()

        return {
            "title": response["title"],
            "id": response["documentId"],
            "url": f"https://docs.google.com/document/d/{response['documentId']}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_blank_document: {e}")
        raise e
