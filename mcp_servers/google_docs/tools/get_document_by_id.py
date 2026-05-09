"""Get document by ID tool for Google Docs MCP Server."""

import logging
from typing import Any

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service, handle_http_error
from .converters import format_document_response

logger = logging.getLogger(__name__)


async def get_document_by_id(
    document_id: str,
    response_format: str = "normalized",
    start_paragraph: int | None = None,
    end_paragraph: int | None = None
) -> dict[str, Any]:
    """Get the latest version of the specified Google Docs document.

    Args:
        document_id: The ID of the Google Docs document.
        response_format: Output format - 'raw', 'plain_text', 'markdown', 'structured', or 'normalized'.
                        Default is 'normalized' for backward compatibility.
        start_paragraph: Optional start paragraph number (1-based, inclusive) to retrieve partial content.
                        Example: start_paragraph=5 retrieves from the 5th paragraph.
        end_paragraph: Optional end paragraph number (1-based, inclusive) to retrieve partial content.
                      Example: end_paragraph=10 retrieves up to and including the 10th paragraph.
                      If start_paragraph is provided but end_paragraph is not, retrieves to end of document.
    """
    logger.info(f"Executing tool: get_document_by_id with document_id: {document_id}, format: {response_format}, paragraphs: [{start_paragraph}, {end_paragraph}]")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        request = service.documents().get(documentId=document_id)
        response = request.execute()

        return format_document_response(
            document=dict(response),
            response_format=response_format,
            start_paragraph=start_paragraph,
            end_paragraph=end_paragraph
        )
    except HttpError as e:
        handle_http_error(e, "Google Docs")
    except Exception as e:
        logger.exception(f"Error executing tool get_document_by_id: {e}")
        raise e
