"""Document format conversion utilities for Google Docs MCP Server."""

from typing import Any, Dict


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


def hex_to_rgb(hex_color: str) -> dict[str, float]:
    """Convert hex color to Google Docs RGB format (0.0-1.0 range)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return {"red": r, "green": g, "blue": b}
