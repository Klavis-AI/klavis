"""Get document by ID tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service
from .converters import format_document_response

logger = logging.getLogger(__name__)


async def _get_document_raw(document_id: str) -> Dict[str, Any]:
    """Internal function to get raw Google Docs API response."""
    access_token = get_auth_token()
    service = get_docs_service(access_token)
    request = service.documents().get(documentId=document_id)
    response = request.execute()
    return dict(response)


async def get_document_by_id(document_id: str, response_format: str = "normalized") -> Dict[str, Any]:
    """Get the latest version of the specified Google Docs document.

    Args:
        document_id: The ID of the Google Docs document.
        response_format: Output format - 'raw', 'plain_text', 'markdown', 'structured', or 'normalized'.
                        Default is 'normalized' for backward compatibility.
    """
    logger.info(f"Executing tool: get_document_by_id with document_id: {document_id}, format: {response_format}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        request = service.documents().get(documentId=document_id)
        response = request.execute()

        # Format the response based on requested format
        return format_document_response(dict(response), response_format)
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_document_by_id: {e}")
        raise e
