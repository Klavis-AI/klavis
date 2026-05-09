"""Markdown parsing utilities for Google Docs MCP Server."""

import re
from typing import Any


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
