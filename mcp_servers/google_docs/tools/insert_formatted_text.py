"""Insert formatted text tool for Google Docs MCP Server."""

import logging
from typing import Any

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service, get_document_raw, handle_http_error
from .converters import extract_text_from_document
from .markdown_parser import parse_markdown_text

logger = logging.getLogger(__name__)


async def insert_formatted_text(
    document_id: str,
    anchor_text: str,
    formatted_text: str,
) -> dict[str, Any]:
    """Insert formatted text by replacing anchor text with formatted content.

    The formatted_text should contain the anchor_text. This allows inserting
    formatted content at any position in the document by specifying what text
    to replace.

    Example:
        anchor_text: "Chapter 1"
        formatted_text: "Chapter 1\\n**New bold paragraph**"
        -> Replaces "Chapter 1" with "Chapter 1" + new formatted content

    Supported markup:
    - **bold** or __bold__
    - *italic* or _italic_
    - ~~strikethrough~~
    - `code`
    - [link text](url)
    - # Heading 1 through ###### Heading 6
    - - or * for bullet points
    """
    logger.info(f"Executing tool: insert_formatted_text with document_id: {document_id}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        document = await get_document_raw(document_id)
        document_text = extract_text_from_document(document)

        anchor_pos = document_text.find(anchor_text)
        if anchor_pos == -1:
            return {
                "success": False,
                "document_id": document_id,
                "error": f"Anchor text not found: '{anchor_text}'",
                "hint": "Use get_document_by_id with response_format='plain_text' to view current content."
            }

        # Google Docs uses 1-based indexing
        anchor_start_index = anchor_pos + 1
        anchor_end_index = anchor_start_index + len(anchor_text)

        plain_text, style_ranges, paragraph_styles = parse_markdown_text(formatted_text)

        requests = []
        requests.append({
            'deleteContentRange': {
                'range': {
                    'startIndex': anchor_start_index,
                    'endIndex': anchor_end_index
                }
            }
        })
        requests.append({
            'insertText': {
                'location': {'index': anchor_start_index},
                'text': plain_text
            }
        })

        # Reverse order to maintain correct indices after text insertion
        for style_range in reversed(style_ranges):
            style = style_range["style"]
            start = anchor_start_index + style_range["start"]
            end = anchor_start_index + style_range["end"]

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

        for para_style in reversed(paragraph_styles):
            start = anchor_start_index + para_style["start"]
            end = anchor_start_index + para_style["end"]

            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": para_style["paragraph_style"],
                    "fields": "namedStyleType"
                }
            })

        service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

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
            "anchor_text": anchor_text,
            "inserted_range": {
                "start_index": anchor_start_index,
                "end_index": anchor_start_index + len(plain_text)
            },
            "characters_inserted": len(plain_text),
            "characters_replaced": len(anchor_text),
            "styles_applied": style_counts,
            "message": f"Replaced '{anchor_text}' with {len(plain_text)} characters of formatted text"
        }

    except HttpError as e:
        handle_http_error(e, "Google Docs")
    except Exception as e:
        logger.exception(f"Error executing tool insert_formatted_text: {e}")
        raise e
