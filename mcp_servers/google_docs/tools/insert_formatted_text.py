"""Insert formatted text tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service
from .get_document_by_id import _get_document_raw
from .markdown_parser import parse_markdown_text

logger = logging.getLogger(__name__)


async def insert_formatted_text(
    document_id: str,
    formatted_text: str,
    position: str = "end"
) -> Dict[str, Any]:
    """Insert formatted text using markdown-like syntax.

    Supported markup:
    - **bold** or __bold__
    - *italic* or _italic_
    - ~~strikethrough~~
    - [link text](url)
    - # Heading 1 through ###### Heading 6
    - - or * for bullet points
    """
    logger.info(f"Executing tool: insert_formatted_text with document_id: {document_id}, position: {position}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        # Parse markdown
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(formatted_text)

        # Get document to find insertion point
        document = await _get_document_raw(document_id)

        if position == "beginning":
            insert_index = 1
        else:  # "end"
            insert_index = document["body"]["content"][-1]["endIndex"] - 1

        # Build requests list
        requests = []

        # First, insert the plain text
        requests.append({
            'insertText': {
                'location': {'index': insert_index},
                'text': plain_text
            }
        })

        # Apply text styles (in reverse order to maintain indices)
        # All style indices need to be offset by insert_index
        for style_range in reversed(style_ranges):
            style = style_range["style"]
            start = insert_index + style_range["start"]
            end = insert_index + style_range["end"]

            text_style = {}
            fields = []

            if style.get("bold"):
                text_style["bold"] = True
                fields.append("bold")
            if style.get("italic"):
                text_style["italic"] = True
                fields.append("italic")
            if style.get("strikethrough"):
                text_style["strikethrough"] = True
                fields.append("strikethrough")
            if style.get("link"):
                text_style["link"] = style["link"]
                fields.append("link")
            if style.get("code"):
                # Inline code: monospace font with light gray background
                text_style["weightedFontFamily"] = {"fontFamily": "Courier New"}
                text_style["backgroundColor"] = {
                    "color": {"rgbColor": {"red": 0.94, "green": 0.94, "blue": 0.94}}
                }
                fields.append("weightedFontFamily")
                fields.append("backgroundColor")

            if fields:
                requests.append({
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "textStyle": text_style,
                        "fields": ",".join(fields)
                    }
                })

        # Apply paragraph styles (headings)
        for para_style in reversed(paragraph_styles):
            start = insert_index + para_style["start"]
            end = insert_index + para_style["end"]

            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": para_style["paragraph_style"],
                    "fields": "namedStyleType"
                }
            })

        # Execute all requests in a single batch
        response = service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

        # Count applied styles
        style_counts = {
            "headings": len(paragraph_styles),
            "bold_ranges": sum(1 for s in style_ranges if s["style"].get("bold")),
            "italic_ranges": sum(1 for s in style_ranges if s["style"].get("italic")),
            "strikethrough_ranges": sum(1 for s in style_ranges if s["style"].get("strikethrough")),
            "links": sum(1 for s in style_ranges if s["style"].get("link")),
            "code_ranges": sum(1 for s in style_ranges if s["style"].get("code"))
        }

        return {
            "success": True,
            "document_id": document_id,
            "inserted_range": {
                "start_index": insert_index,
                "end_index": insert_index + len(plain_text)
            },
            "characters_inserted": len(plain_text),
            "styles_applied": style_counts,
            "message": f"Inserted {len(plain_text)} characters with formatting at {position} of document"
        }

    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool insert_formatted_text: {e}")
        raise e
