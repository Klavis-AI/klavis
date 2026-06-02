"""Create document from text tool for Google Docs MCP Server."""

import logging
from typing import Any

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service, handle_http_error
from .create_blank_document import create_blank_document

logger = logging.getLogger(__name__)


async def create_document_from_text(title: str, text_content: str) -> dict[str, Any]:
    """Create a new Google Docs document with specified text content."""
    logger.info(f"Executing tool: create_document_from_text with title: {title}")
    try:
        document = await create_blank_document(title)

        access_token = get_auth_token()
        service = get_docs_service(access_token)

        requests = [
            {
                "insertText": {
                    "location": {
                        "index": 1,
                    },
                    "text": text_content,
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document["id"], body={"requests": requests}
        ).execute()

        return {
            "title": document["title"],
            "id": document["id"],
            "url": f"https://docs.google.com/document/d/{document['id']}/edit",
        }
    except HttpError as e:
        handle_http_error(e, "Google Docs")
    except Exception as e:
        logger.exception(f"Error executing tool create_document_from_text: {e}")
        raise e
