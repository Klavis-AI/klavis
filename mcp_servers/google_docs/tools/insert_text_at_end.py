"""Insert text at end tool for Google Docs MCP Server."""

import logging
from typing import Any

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service, get_document_raw, handle_http_error

logger = logging.getLogger(__name__)


async def insert_text_at_end(document_id: str, text: str) -> dict[str, Any]:
    """Insert text at the end of a Google Docs document."""
    logger.info(f"Executing tool: insert_text_at_end with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        # Need raw response to get endIndex
        document = await get_document_raw(document_id)

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

        (
            service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )

        return {
            "id": document_id,
            "status": "success",
        }
    except HttpError as e:
        handle_http_error(e, "Google Docs")
    except Exception as e:
        logger.exception(f"Error executing tool insert_text_at_end: {e}")
        raise e
