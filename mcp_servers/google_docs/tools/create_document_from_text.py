"""Create document from text tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service
from .create_blank_document import create_blank_document

logger = logging.getLogger(__name__)


async def create_document_from_text(title: str, text_content: str) -> Dict[str, Any]:
    """Create a new Google Docs document with specified text content."""
    logger.info(f"Executing tool: create_document_from_text with title: {title}")
    try:
        # First, create a blank document
        document = await create_blank_document(title)

        access_token = get_auth_token()
        service = get_docs_service(access_token)

        # Insert the text content
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

        # Execute the batchUpdate method to insert text
        service.documents().batchUpdate(
            documentId=document["id"], body={"requests": requests}
        ).execute()

        return {
            "title": document["title"],
            "id": document["id"],
            "url": f"https://docs.google.com/document/d/{document['id']}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_document_from_text: {e}")
        raise e
