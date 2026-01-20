"""Apply style tool for Google Docs MCP Server."""

import json
import logging
from typing import Any, Dict

from googleapiclient.errors import HttpError

from .base import get_auth_token, get_docs_service
from .converters import hex_to_rgb

logger = logging.getLogger(__name__)


async def apply_style(
    document_id: str,
    start_index: int,
    end_index: int,
    # Character styles
    bold: bool | None = None,
    italic: bool | None = None,
    underline: bool | None = None,
    strikethrough: bool | None = None,
    font_size: float | None = None,
    font_family: str | None = None,
    foreground_color: str | None = None,
    background_color: str | None = None,
    link_url: str | None = None,
    # Paragraph styles
    heading_type: str | None = None,
    alignment: str | None = None,
    line_spacing: float | None = None,
    space_above: float | None = None,
    space_below: float | None = None
) -> Dict[str, Any]:
    """Apply formatting styles to a specified range in a Google Docs document."""
    logger.info(f"Executing tool: apply_style with document_id: {document_id}, range: [{start_index}, {end_index})")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)

        requests = []
        applied_styles = []

        # Build text style request
        text_style = {}
        text_style_fields = []

        if bold is not None:
            text_style["bold"] = bold
            text_style_fields.append("bold")
            applied_styles.append("bold" if bold else "no-bold")

        if italic is not None:
            text_style["italic"] = italic
            text_style_fields.append("italic")
            applied_styles.append("italic" if italic else "no-italic")

        if underline is not None:
            text_style["underline"] = underline
            text_style_fields.append("underline")
            applied_styles.append("underline" if underline else "no-underline")

        if strikethrough is not None:
            text_style["strikethrough"] = strikethrough
            text_style_fields.append("strikethrough")
            applied_styles.append("strikethrough" if strikethrough else "no-strikethrough")

        if font_size is not None:
            text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
            text_style_fields.append("fontSize")
            applied_styles.append(f"fontSize:{font_size}pt")

        if font_family is not None:
            text_style["weightedFontFamily"] = {"fontFamily": font_family}
            text_style_fields.append("weightedFontFamily")
            applied_styles.append(f"fontFamily:{font_family}")

        if foreground_color is not None:
            rgb = hex_to_rgb(foreground_color)
            text_style["foregroundColor"] = {"color": {"rgbColor": rgb}}
            text_style_fields.append("foregroundColor")
            applied_styles.append(f"foregroundColor:{foreground_color}")

        if background_color is not None:
            rgb = hex_to_rgb(background_color)
            text_style["backgroundColor"] = {"color": {"rgbColor": rgb}}
            text_style_fields.append("backgroundColor")
            applied_styles.append(f"backgroundColor:{background_color}")

        if link_url is not None:
            text_style["link"] = {"url": link_url}
            text_style_fields.append("link")
            applied_styles.append(f"link:{link_url}")

        if text_style_fields:
            requests.append({
                "updateTextStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index
                    },
                    "textStyle": text_style,
                    "fields": ",".join(text_style_fields)
                }
            })

        # Build paragraph style request
        paragraph_style = {}
        paragraph_style_fields = []

        if heading_type is not None:
            paragraph_style["namedStyleType"] = heading_type
            paragraph_style_fields.append("namedStyleType")
            applied_styles.append(f"heading:{heading_type}")

        if alignment is not None:
            paragraph_style["alignment"] = alignment
            paragraph_style_fields.append("alignment")
            applied_styles.append(f"alignment:{alignment}")

        if line_spacing is not None:
            paragraph_style["lineSpacing"] = line_spacing
            paragraph_style_fields.append("lineSpacing")
            applied_styles.append(f"lineSpacing:{line_spacing}")

        if space_above is not None:
            paragraph_style["spaceAbove"] = {"magnitude": space_above, "unit": "PT"}
            paragraph_style_fields.append("spaceAbove")
            applied_styles.append(f"spaceAbove:{space_above}pt")

        if space_below is not None:
            paragraph_style["spaceBelow"] = {"magnitude": space_below, "unit": "PT"}
            paragraph_style_fields.append("spaceBelow")
            applied_styles.append(f"spaceBelow:{space_below}pt")

        if paragraph_style_fields:
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index
                    },
                    "paragraphStyle": paragraph_style,
                    "fields": ",".join(paragraph_style_fields)
                }
            })

        if not requests:
            return {
                "success": False,
                "error": "No styles specified. Provide at least one style parameter.",
                "hint": "Available styles: bold, italic, underline, strikethrough, font_size, font_family, foreground_color, background_color, link_url, heading_type, alignment, line_spacing, space_above, space_below"
            }

        # Execute batch update
        response = service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests}
        ).execute()

        return {
            "success": True,
            "document_id": document_id,
            "styled_range": {
                "start_index": start_index,
                "end_index": end_index
            },
            "applied_styles": applied_styles,
            "message": f"Applied {len(applied_styles)} style(s) to range [{start_index}, {end_index})"
        }

    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool apply_style: {e}")
        raise e
