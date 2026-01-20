"""Insert text at end tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service
from .get_document_by_id import _get_document_raw

logger = logging.getLogger(__name__)


async def insert_text_at_end(document_id: str, text: str) -> Dict[str, Any]:
    """Insert text at the end of a Google Docs document."""
    logger.info(f"Executing tool: insert_text_at_end with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        # Need raw response to get endIndex
        document = await _get_document_raw(document_id)

        end_index = document["body"]["content"][-1]["endIndex"]

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': int(end_index) - 1
                    },
                    'text': text
                }
            }
        ]

        # Execute the request
        response = (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )

        return {
            "id": document_id,
            "status": "success",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool insert_text_at_end: {e}")
        raise e
