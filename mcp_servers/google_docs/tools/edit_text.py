"""Edit text tool for Google Docs MCP Server."""

import logging
from typing import Any

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service, get_document_raw, handle_http_error

logger = logging.getLogger(__name__)


async def edit_text(
    document_id: str,
    old_text: str,
    new_text: str,
    match_case: bool = True,
    replace_all: bool = False,
    append_to_end: bool = False
) -> dict[str, Any]:
    """Edit text in a Google Docs document by replacing old text with new text.

    This unified operation handles insert, delete, and replace:
    - Insert: old_text="anchor", new_text="anchor + new content"
    - Delete: old_text="text to delete", new_text=""
    - Replace: old_text="old", new_text="new"
    - Append: old_text="", new_text="content", append_to_end=True
    """
    logger.info(f"Executing tool: edit_text with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        if append_to_end and old_text == "":
            document = await get_document_raw(document_id)
            end_index = document["body"]["content"][-1]["endIndex"]

            requests = [
                {
                    'insertText': {
                        'location': {'index': int(end_index) - 1},
                        'text': new_text
                    }
                }
            ]

            response = service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests}
            ).execute()

            return {
                "success": True,
                "document_id": document_id,
                "operation": "append",
                "characters_inserted": len(new_text),
                "message": f"Appended {len(new_text)} characters to end of document"
            }

        if not old_text:
            return {
                "success": False,
                "error": "old_text is required for replace operations. Use append_to_end=true to insert at end.",
                "hint": "Provide the text you want to find and replace."
            }

        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': old_text,
                        'matchCase': match_case
                    },
                    'replaceText': new_text
                }
            }
        ]

        response = service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

        replies = response.get("replies", [])
        occurrences_changed = 0
        if replies and "replaceAllText" in replies[0]:
            occurrences_changed = replies[0]["replaceAllText"].get("occurrencesChanged", 0)

        if occurrences_changed == 0:
            return {
                "success": False,
                "document_id": document_id,
                "error": f"Text not found: '{old_text}' does not exist in the document.",
                "hint": "Check for typos or use get_document_by_id with response_format='plain_text' to view current content."
            }

        # If replace_all is False but multiple occurrences were replaced, note it
        message = f"Replaced '{old_text}' with '{new_text}' at {occurrences_changed} location(s)"
        if not replace_all and occurrences_changed > 1:
            message += " (Note: all occurrences were replaced. Google Docs API replaces all matches.)"

        return {
            "success": True,
            "document_id": document_id,
            "operation": "replace",
            "replacements_made": occurrences_changed,
            "message": message
        }

    except HttpError as e:
        handle_http_error(e, "Google Docs")
    except Exception as e:
        logger.exception(f"Error executing tool edit_text: {e}")
        raise e
