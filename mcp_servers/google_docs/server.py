import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict
import re
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_DOCS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_DOCS_MCP_SERVER_PORT", "5000"))

# Context variable to store the access token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def extract_access_token(request_or_scope) -> str:
    """Extract access token from x-auth-data header."""
    auth_data = os.getenv("AUTH_DATA")
    
    if not auth_data:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
    
    if not auth_data:
        return ""
    
    try:
        # Parse the JSON auth data to extract access_token
        auth_json = json.loads(auth_data)
        return auth_json.get('access_token', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""

def get_docs_service(access_token: str):
    """Create Google Docs service with access token."""
    credentials = Credentials(token=access_token)
    return build('docs', 'v1', credentials=credentials)

def get_drive_service(access_token: str):
    """Create Google Drive service with access token."""
    credentials = Credentials(token=access_token)
    return build('drive', 'v3', credentials=credentials)

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")


# ============================================================================
# Document Format Conversion Helpers
# ============================================================================

def extract_text_from_document(document: dict[str, Any]) -> str:
    """Extract plain text from a Google Docs document structure."""
    text_parts = []
    body = document.get("body", {})
    content = body.get("content", [])

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            for elem in paragraph.get("elements", []):
                if "textRun" in elem:
                    text_parts.append(elem["textRun"].get("content", ""))

    return "".join(text_parts)


def get_paragraph_heading_type(paragraph: dict[str, Any]) -> str:
    """Get the heading type of a paragraph."""
    style = paragraph.get("paragraphStyle", {})
    return style.get("namedStyleType", "NORMAL_TEXT")


def convert_document_to_markdown(document: dict[str, Any]) -> str:
    """Convert a Google Docs document to markdown format."""
    markdown_parts = []
    body = document.get("body", {})
    content = body.get("content", [])

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            heading_type = get_paragraph_heading_type(paragraph)

            # Build paragraph text with inline formatting
            para_text = ""
            for elem in paragraph.get("elements", []):
                if "textRun" in elem:
                    text_run = elem["textRun"]
                    text = text_run.get("content", "")
                    style = text_run.get("textStyle", {})

                    # Apply inline formatting
                    if text.strip():  # Don't format whitespace-only content
                        if style.get("bold") and style.get("italic"):
                            text = f"***{text.strip()}***"
                            if text_run.get("content", "").endswith(" "):
                                text += " "
                        elif style.get("bold"):
                            text = f"**{text.strip()}**"
                            if text_run.get("content", "").endswith(" "):
                                text += " "
                        elif style.get("italic"):
                            text = f"*{text.strip()}*"
                            if text_run.get("content", "").endswith(" "):
                                text += " "
                        if style.get("strikethrough"):
                            text = f"~~{text.strip()}~~"
                            if text_run.get("content", "").endswith(" "):
                                text += " "

                        # Handle links
                        link = style.get("link", {})
                        if link.get("url"):
                            text = f"[{text.strip()}]({link['url']})"
                            if text_run.get("content", "").endswith(" "):
                                text += " "

                    para_text += text

            # Apply heading formatting
            para_text = para_text.rstrip("\n")
            if para_text.strip():
                if heading_type == "TITLE":
                    para_text = f"# {para_text}"
                elif heading_type == "SUBTITLE":
                    para_text = f"## {para_text}"
                elif heading_type == "HEADING_1":
                    para_text = f"# {para_text}"
                elif heading_type == "HEADING_2":
                    para_text = f"## {para_text}"
                elif heading_type == "HEADING_3":
                    para_text = f"### {para_text}"
                elif heading_type == "HEADING_4":
                    para_text = f"#### {para_text}"
                elif heading_type == "HEADING_5":
                    para_text = f"##### {para_text}"
                elif heading_type == "HEADING_6":
                    para_text = f"###### {para_text}"

                # Handle bullet points
                bullet = paragraph.get("bullet")
                if bullet:
                    para_text = f"- {para_text}"

                markdown_parts.append(para_text)
            else:
                markdown_parts.append("")  # Preserve empty lines

    return "\n".join(markdown_parts)


def convert_document_to_structured(document: dict[str, Any]) -> dict[str, Any]:
    """Convert a Google Docs document to structured format with indices."""
    elements = []
    body = document.get("body", {})
    content = body.get("content", [])

    for element in content:
        if "paragraph" in element:
            paragraph = element["paragraph"]
            start_index = element.get("startIndex", 0)
            end_index = element.get("endIndex", 0)
            heading_type = get_paragraph_heading_type(paragraph)

            # Extract text runs with styles
            text_runs = []
            full_content = ""
            for elem in paragraph.get("elements", []):
                if "textRun" in elem:
                    text_run = elem["textRun"]
                    run_content = text_run.get("content", "")
                    run_style = text_run.get("textStyle", {})
                    run_start = elem.get("startIndex", 0)
                    run_end = elem.get("endIndex", 0)

                    # Simplify style to only include set properties
                    simplified_style = {}
                    if run_style.get("bold"):
                        simplified_style["bold"] = True
                    if run_style.get("italic"):
                        simplified_style["italic"] = True
                    if run_style.get("underline"):
                        simplified_style["underline"] = True
                    if run_style.get("strikethrough"):
                        simplified_style["strikethrough"] = True
                    if run_style.get("link", {}).get("url"):
                        simplified_style["link_url"] = run_style["link"]["url"]

                    text_runs.append({
                        "content": run_content,
                        "start_index": run_start,
                        "end_index": run_end,
                        "style": simplified_style
                    })
                    full_content += run_content

            elements.append({
                "type": "paragraph",
                "start_index": start_index,
                "end_index": end_index,
                "content": full_content.rstrip("\n"),
                "paragraph_style": {"heading_type": heading_type},
                "text_runs": text_runs
            })

    return {
        "document_id": document.get("documentId", ""),
        "title": document.get("title", ""),
        "elements": elements
    }


def format_document_response(
    document: dict[str, Any],
    response_format: str = "raw"
) -> dict[str, Any]:
    """Format document response based on requested format."""
    if response_format == "raw":
        return document

    elif response_format == "plain_text":
        text = extract_text_from_document(document)
        return {
            "document_id": document.get("documentId", ""),
            "title": document.get("title", ""),
            "content": text,
            "word_count": len(text.split())
        }

    elif response_format == "markdown":
        markdown = convert_document_to_markdown(document)
        return {
            "document_id": document.get("documentId", ""),
            "title": document.get("title", ""),
            "content": markdown,
            "word_count": len(extract_text_from_document(document).split())
        }

    elif response_format == "structured":
        return convert_document_to_structured(document)

    elif response_format == "normalized":
        return normalize_document_response(document)

    else:
        # Default to raw if unknown format
        return document


def normalize_document_response(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize the Google Docs API response to a simplified structure.
    Reduces complexity while preserving important information.
    Includes table processing, page info, and list definitions.
    """
    
    def extract_text_from_paragraph(paragraph: Dict) -> Dict[str, Any]:
        """Extract text content and styling from a paragraph."""
        elements = paragraph.get('elements', [])
        text_parts = []
        
        for element in elements:
            if 'textRun' in element:
                text_run = element['textRun']
                content = text_run.get('content', '')
                text_style = text_run.get('textStyle', {})
                
                part = {'text': content}
                if text_style.get('bold'):
                    part['bold'] = True
                if text_style.get('italic'):
                    part['italic'] = True
                if text_style.get('underline'):
                    part['underline'] = True
                
                text_parts.append(part)
        
        # Combine text for simple display
        full_text = ''.join(p['text'] for p in text_parts).strip()
        
        result = {'text': full_text}
        
        # Add paragraph style info
        para_style = paragraph.get('paragraphStyle', {})
        named_style = para_style.get('namedStyleType')
        if named_style and named_style != 'NORMAL_TEXT':
            result['style'] = named_style
        
        heading_id = para_style.get('headingId')
        if heading_id:
            result['headingId'] = heading_id
        
        # Add bullet info if present
        if 'bullet' in paragraph:
            bullet = paragraph['bullet']
            result['isBullet'] = True
            result['listId'] = bullet.get('listId')
            if bullet.get('nestingLevel', 0) > 0:
                result['nestingLevel'] = bullet['nestingLevel']
        
        # Include rich text parts if there's formatting
        has_formatting = any(
            p.get('bold') or p.get('italic') or p.get('underline')
            for p in text_parts
        )
        if has_formatting:
            result['formattedParts'] = [p for p in text_parts if p['text'].strip()]
        
        return result
    
    def extract_table(table: Dict) -> Dict[str, Any]:
        """Extract table content in a simplified format."""
        rows = table.get('rows', 0)
        columns = table.get('columns', 0)
        table_rows = table.get('tableRows', [])
        
        extracted_rows = []
        for table_row in table_rows:
            cells = []
            for cell in table_row.get('tableCells', []):
                cell_content = []
                for content_item in cell.get('content', []):
                    if 'paragraph' in content_item:
                        para_data = extract_text_from_paragraph(content_item['paragraph'])
                        if para_data['text']:
                            cell_content.append(para_data['text'])
                cells.append(' '.join(cell_content))
            extracted_rows.append(cells)
        
        return {
            'type': 'table',
            'rows': rows,
            'columns': columns,
            'data': extracted_rows
        }
    
    def process_content(content_list: list) -> list:
        """Process the document content into a simplified structure."""
        processed = []
        
        for item in content_list:
            # Skip section breaks
            if 'sectionBreak' in item:
                continue
            
            # Process paragraphs
            if 'paragraph' in item:
                para_data = extract_text_from_paragraph(item['paragraph'])
                if para_data['text']:  # Only include non-empty paragraphs
                    processed.append({
                        'type': 'paragraph',
                        **para_data
                    })
            
            # Process tables
            elif 'table' in item:
                table_data = extract_table(item['table'])
                processed.append(table_data)
        
        return processed
    
    # Build the normalized response
    normalized = {
        'documentId': raw_response.get('documentId'),
        'title': raw_response.get('title'),
        'revisionId': raw_response.get('revisionId'),
    }
    
    # Process body content
    body = raw_response.get('body', {})
    content = body.get('content', [])
    normalized['content'] = process_content(content)
    
    # Extract document metadata
    doc_style = raw_response.get('documentStyle', {})
    if doc_style:
        page_size = doc_style.get('pageSize', {})
        normalized['pageInfo'] = {
            'width': page_size.get('width', {}).get('magnitude'),
            'height': page_size.get('height', {}).get('magnitude'),
            'unit': page_size.get('width', {}).get('unit', 'PT'),
            'margins': {
                'top': doc_style.get('marginTop', {}).get('magnitude'),
                'bottom': doc_style.get('marginBottom', {}).get('magnitude'),
                'left': doc_style.get('marginLeft', {}).get('magnitude'),
                'right': doc_style.get('marginRight', {}).get('magnitude'),
            }
        }
    
    # Include list definitions (simplified)
    lists = raw_response.get('lists', {})
    if lists:
        normalized['lists'] = {
            list_id: {
                'type': 'bullet' if props.get('listProperties', {}).get('nestingLevels', [{}])[0].get('glyphSymbol') else 'numbered'
            }
            for list_id, props in lists.items()
        }
    
    return normalized


# ============================================================================
# Markdown Parsing Helpers
# ============================================================================

def parse_markdown_text(text: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse markdown-like text and extract plain text with style ranges.

    Returns:
        tuple: (plain_text, style_ranges, paragraph_styles)
        - plain_text: Text with markdown syntax removed
        - style_ranges: List of dicts with 'start', 'end', 'style' keys
        - paragraph_styles: List of paragraph-level style dicts
    """
    style_ranges = []
    plain_text = ""
    lines = text.split('\n')
    current_index = 0
    paragraph_styles = []  # Track paragraph-level styles

    for line_num, line in enumerate(lines):
        line_start_index = current_index

        # Check for headings at line start
        heading_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if heading_match:
            heading_level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            heading_types = {
                1: "HEADING_1",
                2: "HEADING_2",
                3: "HEADING_3",
                4: "HEADING_4",
                5: "HEADING_5",
                6: "HEADING_6"
            }
            # Process inline formatting within heading
            processed_text, inline_styles = parse_inline_formatting(heading_text, current_index)
            style_ranges.extend(inline_styles)
            plain_text += processed_text

            # Mark paragraph style for this line
            paragraph_styles.append({
                "start": line_start_index,
                "end": current_index + len(processed_text) + 1,  # +1 for newline
                "paragraph_style": {"namedStyleType": heading_types[heading_level]}
            })
            current_index += len(processed_text)
        # Check for bullet points
        elif re.match(r'^[\-\*]\s+', line):
            bullet_text = re.sub(r'^[\-\*]\s+', '', line)
            processed_text, inline_styles = parse_inline_formatting(bullet_text, current_index)
            # Adjust for bullet marker we're preserving
            plain_text += "• " + processed_text
            # Adjust inline style indices
            for style in inline_styles:
                style["start"] += 2  # "• " is 2 characters
                style["end"] += 2
            style_ranges.extend(inline_styles)
            current_index += 2 + len(processed_text)
        else:
            # Regular line - process inline formatting
            processed_text, inline_styles = parse_inline_formatting(line, current_index)
            style_ranges.extend(inline_styles)
            plain_text += processed_text
            current_index += len(processed_text)

        # Add newline between lines (except last line)
        if line_num < len(lines) - 1:
            plain_text += '\n'
            current_index += 1

    return plain_text, style_ranges, paragraph_styles


def parse_inline_formatting(text: str, base_index: int) -> tuple[str, list[dict[str, Any]]]:
    """Parse inline markdown formatting (bold, italic, links, strikethrough, code).

    Supports escape sequences:
    - \\_  -> literal underscore (not interpreted as italic)
    - \\*  -> literal asterisk (not interpreted as bold/italic)
    - \\`  -> literal backtick (not interpreted as code)

    Returns:
        tuple: (plain_text, style_ranges)
    """
    style_ranges = []
    result = ""
    i = 0

    while i < len(text):
        # Escape sequences: \_ \* \` -> literal characters
        if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in '_*`':
            result += text[i + 1]
            i += 2
            continue

        # Inline code: `code` -> monospace font with gray background
        match = re.match(r'`([^`]+)`', text[i:])
        if match:
            content = match.group(1)
            start_pos = base_index + len(result)
            result += content
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(content),
                "style": {"code": True}
            })
            i += len(match.group(0))
            continue

        # Bold + Italic: ***text*** or ___text___
        match = re.match(r'\*\*\*(.+?)\*\*\*|___(.+?)___', text[i:])
        if match:
            content = match.group(1) or match.group(2)
            start_pos = base_index + len(result)
            result += content
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(content),
                "style": {"bold": True, "italic": True}
            })
            i += len(match.group(0))
            continue

        # Bold: **text** or __text__
        match = re.match(r'\*\*(.+?)\*\*|__(.+?)__', text[i:])
        if match:
            content = match.group(1) or match.group(2)
            start_pos = base_index + len(result)
            result += content
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(content),
                "style": {"bold": True}
            })
            i += len(match.group(0))
            continue

        # Italic: *text* or _text_
        match = re.match(r'\*([^*]+?)\*|_([^_]+?)_', text[i:])
        if match:
            content = match.group(1) or match.group(2)
            start_pos = base_index + len(result)
            result += content
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(content),
                "style": {"italic": True}
            })
            i += len(match.group(0))
            continue

        # Strikethrough: ~~text~~
        match = re.match(r'~~(.+?)~~', text[i:])
        if match:
            content = match.group(1)
            start_pos = base_index + len(result)
            result += content
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(content),
                "style": {"strikethrough": True}
            })
            i += len(match.group(0))
            continue

        # Links: [text](url)
        match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', text[i:])
        if match:
            link_text = match.group(1)
            url = match.group(2)
            start_pos = base_index + len(result)
            result += link_text
            style_ranges.append({
                "start": start_pos,
                "end": start_pos + len(link_text),
                "style": {"link": {"url": url}}
            })
            i += len(match.group(0))
            continue

        # Regular character
        result += text[i]
        i += 1

    return result, style_ranges


# ============================================================================
# Hex Color Conversion Helper
# ============================================================================

def hex_to_rgb(hex_color: str) -> dict[str, float]:
    """Convert hex color to Google Docs RGB format (0.0-1.0 range)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}


# ============================================================================
# Core Document Operations
# ============================================================================

async def _get_document_raw(document_id: str) -> Dict[str, Any]:
    """Internal function to get raw Google Docs API response."""
    access_token = get_auth_token()
    service = get_docs_service(access_token)
    request = service.documents().get(documentId=document_id)
    response = request.execute()
    return dict(response)


async def get_document_by_id(document_id: str, response_format: str = "raw") -> Dict[str, Any]:
    """Get the latest version of the specified Google Docs document.
    
    Args:
        document_id: The ID of the Google Docs document.
        response_format: Output format - 'raw', 'plain_text', 'markdown', or 'structured'.
                        Default is 'raw' for backward compatibility.
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

async def create_blank_document(title: str) -> Dict[str, Any]:
    """Create a new blank Google Docs document with a title."""
    logger.info(f"Executing tool: create_blank_document with title: {title}")
    try:
        access_token = get_auth_token()
        service = get_docs_service(access_token)
        
        body = {"title": title}
        
        request = service.documents().create(body=body)
        response = request.execute()
        
        return {
            "title": response["title"],
            "id": response["documentId"],
            "url": f"https://docs.google.com/document/d/{response['documentId']}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_blank_document: {e}")
        raise e

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
            "url": f"https://docs.google.com/document/d/{document["id"]}/edit",
        }
    except HttpError as e:
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool create_document_from_text: {e}")
        raise e

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

        # Handle append to end case
        if append_to_end and old_text == "":
            document = await _get_document_raw(document_id)
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

        # Handle normal replace case
        if not old_text:
            return {
                "success": False,
                "error": "old_text is required for replace operations. Use append_to_end=true to insert at end.",
                "hint": "Provide the text you want to find and replace."
            }

        # Use replaceAllText for the replacement
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

        # Count replacements from response
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
        logger.error(f"Google Docs API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Docs API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool edit_text: {e}")
        raise e


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
) -> dict[str, Any]:
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


async def insert_formatted_text(
    document_id: str,
    formatted_text: str,
    position: str = "end"
) -> dict[str, Any]:
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


async def get_all_documents() -> Dict[str, Any]:
    """Get all Google Docs documents from the user's Drive."""
    logger.info(f"Executing tool: get_all_documents")
    try:
        access_token = get_auth_token()
        service = get_drive_service(access_token)
        
        # Query for Google Docs files
        query = "mimeType='application/vnd.google-apps.document'"
        
        request = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc"
        )
        response = request.execute()
        
        documents = []
        for file in response.get('files', []):
            documents.append({
                'id': file['id'],
                'name': file['name'],
                'createdAt': file.get('createdTime'),
                'modifiedAt': file.get('modifiedTime'),
                'url': file.get('webViewLink')
            })
        
        return {
            'documents': documents,
            'total_count': len(documents)
        }
    except HttpError as e:
        logger.error(f"Google Drive API error: {e}")
        error_detail = json.loads(e.content.decode('utf-8'))
        raise RuntimeError(f"Google Drive API Error ({e.resp.status}): {error_detail.get('error', {}).get('message', 'Unknown error')}")
    except Exception as e:
        logger.exception(f"Error executing tool get_all_documents: {e}")
        raise e

@click.command()
@click.option("--port", default=GOOGLE_DOCS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("google-docs-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_docs_get_document_by_id",
                description="""Retrieve a Google Docs document by ID.

Response formats:
- 'raw': Full API response with all metadata (default, backward compatible)
- 'plain_text': Text content only, no formatting
- 'markdown': Text with formatting converted to markdown syntax
- 'structured': JSON with text runs and style information, including character indices for editing
- 'normalized': Simplified structure with tables, page info, and list definitions
""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document to retrieve.",
                        },
                        "response_format": {
                            "type": "string",
                            "enum": ["raw", "plain_text", "markdown", "structured", "normalized"],
                            "description": "Output format. Default: 'raw' (for backward compatibility)",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_docs_get_all_documents",
                description="Get all Google Docs documents from the user's Drive.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="google_docs_insert_text_at_end",
                description="Insert text at the end of a Google Docs document.",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document to modify.",
                        },
                        "text": {
                            "type": "string",
                            "description": "The text content to insert at the end of the document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_create_blank_document",
                description="Create a new blank Google Docs document with a title.",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title for the new document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_create_document_from_text",
                description="Create a new Google Docs document with specified text content.",
                inputSchema={
                    "type": "object",
                    "required": ["title", "text_content"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title for the new document.",
                        },
                        "text_content": {
                            "type": "string",
                            "description": "The text content to include in the new document.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            # New tools
            types.Tool(
                name="google_docs_edit_text",
                description="""Edit text in a Google Docs document by replacing old text with new text.

This single operation handles insert, delete, and replace:

- **Insert after anchor**:
  old_text: "# Introduction"
  new_text: "# Introduction\\n\\nThis is the new paragraph."

- **Delete**:
  old_text: "Remove this sentence."
  new_text: ""

- **Replace**:
  old_text: "old word"
  new_text: "new word"

- **Insert at end**:
  old_text: "" (empty)
  new_text: "Appended text"
  append_to_end: true
""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "old_text", "new_text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "old_text": {
                            "type": "string",
                            "description": "The text to find and replace. Use empty string with append_to_end=true to insert at end.",
                        },
                        "new_text": {
                            "type": "string",
                            "description": "The replacement text. Use empty string to delete.",
                        },
                        "match_case": {
                            "type": "boolean",
                            "description": "Whether to match case when finding old_text. Default: true",
                        },
                        "replace_all": {
                            "type": "boolean",
                            "description": "Replace all occurrences or just the first one. Default: false (Note: Google Docs API always replaces all)",
                        },
                        "append_to_end": {
                            "type": "boolean",
                            "description": "If true and old_text is empty, append new_text to the end of document. Default: false",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_apply_style",
                description="""Apply formatting styles to a specified range in a Google Docs document.

Supports both character-level styles (bold, italic, etc.) and paragraph-level styles (headings, alignment, etc.).

To find the correct indices, use google_docs_get_document_by_id with response_format='structured'.
""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "start_index", "end_index"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "start_index": {
                            "type": "integer",
                            "description": "Start position of the range (1-based, inclusive).",
                        },
                        "end_index": {
                            "type": "integer",
                            "description": "End position of the range (exclusive).",
                        },
                        # Character styles
                        "bold": {
                            "type": "boolean",
                            "description": "Apply bold formatting.",
                        },
                        "italic": {
                            "type": "boolean",
                            "description": "Apply italic formatting.",
                        },
                        "underline": {
                            "type": "boolean",
                            "description": "Apply underline formatting.",
                        },
                        "strikethrough": {
                            "type": "boolean",
                            "description": "Apply strikethrough formatting.",
                        },
                        "font_size": {
                            "type": "number",
                            "description": "Font size in points (e.g., 12, 14, 18).",
                        },
                        "font_family": {
                            "type": "string",
                            "description": "Font family name (e.g., 'Arial', 'Times New Roman').",
                        },
                        "foreground_color": {
                            "type": "string",
                            "description": "Text color in hex format (e.g., '#FF0000' for red).",
                        },
                        "background_color": {
                            "type": "string",
                            "description": "Background/highlight color in hex format.",
                        },
                        "link_url": {
                            "type": "string",
                            "description": "URL to create a hyperlink.",
                        },
                        # Paragraph styles
                        "heading_type": {
                            "type": "string",
                            "enum": ["NORMAL_TEXT", "TITLE", "SUBTITLE", "HEADING_1", "HEADING_2", "HEADING_3", "HEADING_4", "HEADING_5", "HEADING_6"],
                            "description": "Paragraph heading style.",
                        },
                        "alignment": {
                            "type": "string",
                            "enum": ["START", "CENTER", "END", "JUSTIFIED"],
                            "description": "Text alignment.",
                        },
                        "line_spacing": {
                            "type": "number",
                            "description": "Line spacing (100 = single, 150 = 1.5, 200 = double).",
                        },
                        "space_above": {
                            "type": "number",
                            "description": "Space above paragraph in points.",
                        },
                        "space_below": {
                            "type": "number",
                            "description": "Space below paragraph in points.",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
            types.Tool(
                name="google_docs_insert_formatted_text",
                description="""Insert formatted text into a Google Docs document using markdown-like syntax.

Supported markup:
- **bold** or __bold__ for bold text
- *italic* or _italic_ for italic text
- ~~strikethrough~~ for strikethrough
- [link text](url) for hyperlinks
- `code` for inline code (monospace font with gray background)
- # Heading 1, ## Heading 2, ... ###### Heading 6 (must be at line start)
- - item or * item for bullet points

Escape sequences (to prevent formatting):
- \\_  -> literal underscore
- \\*  -> literal asterisk
- \\`  -> literal backtick

Example:
```
# Meeting Notes

**Important**: This is a _critical_ update.
Use `access_token` for authentication.

## Action Items
- Review the ~~old~~ new proposal
- Contact [John](mailto:john@example.com)
```

This high-level API internally:
1. Parses the markdown syntax
2. Inserts plain text
3. Applies styles (bold, italic, headings, code, etc.)
4. Executes all as a single atomic batchUpdate
""",
                inputSchema={
                    "type": "object",
                    "required": ["document_id", "formatted_text"],
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "The ID of the Google Docs document.",
                        },
                        "formatted_text": {
                            "type": "string",
                            "description": "Text with markdown-like syntax for formatting.",
                        },
                        "position": {
                            "type": "string",
                            "enum": ["end", "beginning"],
                            "description": "Where to insert the text. Default: 'end'",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "GOOGLE_DOCS_DOCUMENT"}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:     
        if name == "google_docs_get_document_by_id":
            document_id = arguments.get("document_id")
            if not document_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id parameter is required",
                    )
                ]

            # Get response_format with default 'raw' for backward compatibility
            response_format = arguments.get("response_format", "raw")

            try:
                result = await get_document_by_id(document_id, response_format)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, dict) else str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "google_docs_get_all_documents":            
            try:
                result = await get_all_documents()
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "google_docs_insert_text_at_end":
            document_id = arguments.get("document_id")
            text = arguments.get("text")
            if not document_id or not text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id and text parameters are required",
                    )
                ]
            
            try:
                result = await insert_text_at_end(document_id, text)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "google_docs_create_blank_document":
            title = arguments.get("title")
            if not title:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title parameter is required",
                    )
                ]
            
            try:
                result = await create_blank_document(title)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "google_docs_create_document_from_text":
            title = arguments.get("title")
            text_content = arguments.get("text_content")
            if not title or not text_content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: title and text_content parameters are required",
                    )
                ]
            
            try:
                result = await create_document_from_text(title, text_content)
                return [
                    types.TextContent(
                        type="text",
                        text=str(result),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "google_docs_edit_text":
            document_id = arguments.get("document_id")
            old_text = arguments.get("old_text")
            new_text = arguments.get("new_text")

            if not document_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id parameter is required",
                    )
                ]

            # old_text and new_text can be empty strings, so check for None explicitly
            if old_text is None or new_text is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: old_text and new_text parameters are required",
                    )
                ]

            match_case = arguments.get("match_case", True)
            replace_all = arguments.get("replace_all", False)
            append_to_end = arguments.get("append_to_end", False)

            try:
                result = await edit_text(
                    document_id=document_id,
                    old_text=old_text,
                    new_text=new_text,
                    match_case=match_case,
                    replace_all=replace_all,
                    append_to_end=append_to_end
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "google_docs_apply_style":
            document_id = arguments.get("document_id")
            start_index = arguments.get("start_index")
            end_index = arguments.get("end_index")

            if not document_id or start_index is None or end_index is None:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id, start_index, and end_index parameters are required",
                    )
                ]

            try:
                result = await apply_style(
                    document_id=document_id,
                    start_index=start_index,
                    end_index=end_index,
                    bold=arguments.get("bold"),
                    italic=arguments.get("italic"),
                    underline=arguments.get("underline"),
                    strikethrough=arguments.get("strikethrough"),
                    font_size=arguments.get("font_size"),
                    font_family=arguments.get("font_family"),
                    foreground_color=arguments.get("foreground_color"),
                    background_color=arguments.get("background_color"),
                    link_url=arguments.get("link_url"),
                    heading_type=arguments.get("heading_type"),
                    alignment=arguments.get("alignment"),
                    line_spacing=arguments.get("line_spacing"),
                    space_above=arguments.get("space_above"),
                    space_below=arguments.get("space_below")
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        elif name == "google_docs_insert_formatted_text":
            document_id = arguments.get("document_id")
            formatted_text = arguments.get("formatted_text")

            if not document_id or not formatted_text:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: document_id and formatted_text parameters are required",
                    )
                ]

            position = arguments.get("position", "end")

            try:
                result = await insert_formatted_text(
                    document_id=document_id,
                    formatted_text=formatted_text,
                    position=position
                )
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]

        return [
            types.TextContent(
                type="text",
                text=f"Unknown tool: {name}",
            )
        ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract auth token from headers
        auth_token = extract_access_token(request)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract auth token from headers
        auth_token = extract_access_token(scope)
        
        # Set the auth token in context for this request
        token = auth_token_context.set(auth_token)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main() 
