"""Unit tests for document format conversion functions.

This file tests LOCAL conversion logic (not API calls):
- format_document_response: Dispatch to correct converter based on format
- extract_text_from_document: Extract plain text from API response
- convert_document_to_markdown: Convert API response to markdown (LOCAL, not API)
- convert_document_to_structured: Convert to structured format with indices
- normalize_document_response: Simplify API response structure
- parse_markdown_text / parse_inline_formatting: Markdown parsing for insert_formatted_text
- hex_to_rgb: Color conversion helper

NOTE: 'markdown' format is NOT a Google Docs API feature.
It's a local conversion from the API's JSON response to markdown syntax.
"""

import pytest

from tools import (
    convert_document_to_markdown,
    extract_text_from_document,
    format_document_response,
    hex_to_rgb,
    parse_inline_formatting,
    parse_markdown_text,
)


class TestParseInlineFormatting:
    """Tests for parse_inline_formatting function."""

    def test_plain_text_unchanged(self):
        """Test that plain text without formatting is unchanged."""
        text = "Hello World"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "Hello World"
        assert len(style_ranges) == 0

    def test_bold_double_asterisk(self):
        """Test that **text** is parsed as bold."""
        text = "**bold text**"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert style_ranges[0]["start"] == 0
        assert style_ranges[0]["end"] == 9

    def test_bold_double_underscore(self):
        """Test that __text__ is parsed as bold."""
        text = "__bold text__"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True

    def test_italic_single_asterisk(self):
        """Test that *text* is parsed as italic."""
        text = "*italic text*"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "italic text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["italic"] is True

    def test_italic_single_underscore(self):
        """Test that _text_ is parsed as italic."""
        text = "_italic text_"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "italic text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["italic"] is True

    def test_bold_italic_triple_asterisk(self):
        """Test that ***text*** is parsed as bold and italic."""
        text = "***bold italic***"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold italic"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert style_ranges[0]["style"]["italic"] is True

    def test_strikethrough(self):
        """Test that ~~text~~ is parsed as strikethrough."""
        text = "~~strikethrough~~"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "strikethrough"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["strikethrough"] is True

    def test_link(self):
        """Test that [text](url) is parsed as link."""
        text = "[click here](https://example.com)"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "click here"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["link"]["url"] == "https://example.com"

    def test_inline_code(self):
        """Test that `code` is parsed as code."""
        text = "`inline code`"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "inline code"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["code"] is True

    def test_escaped_underscore(self):
        """Test that \\_ produces literal underscore."""
        text = "access\\_token"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "access_token"
        assert len(style_ranges) == 0

    def test_escaped_asterisk(self):
        """Test that \\* produces literal asterisk."""
        text = "\\*not bold\\*"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "*not bold*"
        assert len(style_ranges) == 0

    def test_escaped_backtick(self):
        """Test that \\` produces literal backtick."""
        text = "\\`not code\\`"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "`not code`"
        assert len(style_ranges) == 0

    def test_mixed_formatting(self):
        """Test mixed formatting in same line."""
        text = "**bold** and *italic* and `code`"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold and italic and code"
        assert len(style_ranges) == 3

        # Check bold
        bold_range = next(r for r in style_ranges if r["style"].get("bold"))
        assert bold_range["start"] == 0
        assert bold_range["end"] == 4

        # Check italic
        italic_range = next(r for r in style_ranges if r["style"].get("italic"))
        assert italic_range is not None

        # Check code
        code_range = next(r for r in style_ranges if r["style"].get("code"))
        assert code_range is not None

    def test_base_index_offset(self):
        """Test that base_index offsets all ranges."""
        text = "**bold**"
        _, style_ranges = parse_inline_formatting(text, 100)

        assert style_ranges[0]["start"] == 100
        assert style_ranges[0]["end"] == 104


class TestParseMarkdownText:
    """Tests for parse_markdown_text function."""

    def test_heading_1(self):
        """Test that # Heading is parsed as HEADING_1."""
        text = "# Heading 1"
        plain_text, _, paragraph_styles = parse_markdown_text(text)

        assert plain_text == "Heading 1"
        assert len(paragraph_styles) == 1
        assert paragraph_styles[0]["paragraph_style"]["namedStyleType"] == "HEADING_1"

    def test_heading_levels(self):
        """Test that different heading levels are parsed correctly."""
        heading_map = {
            "# H1": "HEADING_1",
            "## H2": "HEADING_2",
            "### H3": "HEADING_3",
            "#### H4": "HEADING_4",
            "##### H5": "HEADING_5",
            "###### H6": "HEADING_6",
        }

        for markdown, expected_style in heading_map.items():
            _, _, paragraph_styles = parse_markdown_text(markdown)
            assert len(paragraph_styles) == 1
            assert paragraph_styles[0]["paragraph_style"]["namedStyleType"] == expected_style

    def test_bullet_point_dash(self):
        """Test that - item is parsed as bullet point."""
        text = "- Item 1"
        plain_text, _, _ = parse_markdown_text(text)

        # Bullet is converted to bullet character
        assert "• Item 1" in plain_text or "Item 1" in plain_text

    def test_bullet_point_asterisk(self):
        """Test that * item is parsed as bullet point."""
        text = "* Item 1"
        plain_text, _, _ = parse_markdown_text(text)

        assert "• Item 1" in plain_text or "Item 1" in plain_text

    def test_inline_formatting_in_heading(self):
        """Test that inline formatting works within headings."""
        text = "# **Bold** Heading"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        assert "Bold Heading" in plain_text
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert len(paragraph_styles) == 1

    def test_multiple_lines(self):
        """Test that multiple lines are parsed correctly."""
        text = "Line 1\nLine 2\nLine 3"
        plain_text, _, _ = parse_markdown_text(text)

        assert plain_text == "Line 1\nLine 2\nLine 3"

    def test_multiline_with_formatting(self):
        """Test multiline text with various formatting."""
        text = "# Title\n\nSome **bold** text\n- A bullet"
        _, style_ranges, paragraph_styles = parse_markdown_text(text)

        # Should have heading style
        assert len(paragraph_styles) >= 1
        assert paragraph_styles[0]["paragraph_style"]["namedStyleType"] == "HEADING_1"

        # Should have bold style
        bold_ranges = [r for r in style_ranges if r["style"].get("bold")]
        assert len(bold_ranges) == 1


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_pure_red(self):
        """Test #FF0000 converts to red."""
        result = hex_to_rgb("#FF0000")
        assert result["red"] == 1.0
        assert result["green"] == 0.0
        assert result["blue"] == 0.0

    def test_pure_green(self):
        """Test #00FF00 converts to green."""
        result = hex_to_rgb("#00FF00")
        assert result["red"] == 0.0
        assert result["green"] == 1.0
        assert result["blue"] == 0.0

    def test_pure_blue(self):
        """Test #0000FF converts to blue."""
        result = hex_to_rgb("#0000FF")
        assert result["red"] == 0.0
        assert result["green"] == 0.0
        assert result["blue"] == 1.0

    def test_white(self):
        """Test #FFFFFF converts to white."""
        result = hex_to_rgb("#FFFFFF")
        assert result["red"] == 1.0
        assert result["green"] == 1.0
        assert result["blue"] == 1.0

    def test_black(self):
        """Test #000000 converts to black."""
        result = hex_to_rgb("#000000")
        assert result["red"] == 0.0
        assert result["green"] == 0.0
        assert result["blue"] == 0.0

    def test_without_hash(self):
        """Test that hex color without # is handled."""
        result = hex_to_rgb("FF0000")
        assert result["red"] == 1.0

    def test_lowercase(self):
        """Test that lowercase hex is handled."""
        result = hex_to_rgb("#ff0000")
        assert result["red"] == 1.0

    def test_mixed_color(self):
        """Test a mixed color value."""
        # #808080 = gray (128, 128, 128)
        result = hex_to_rgb("#808080")
        assert 0.5 <= result["red"] <= 0.51  # ~0.502
        assert 0.5 <= result["green"] <= 0.51
        assert 0.5 <= result["blue"] <= 0.51

    def test_invalid_hex_raises_error(self):
        """Test that invalid hex raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("invalid")

    def test_short_hex_raises_error(self):
        """Test that short hex raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FFF")


class TestFormatDocumentResponse:
    """Tests for format_document_response function.

    This function dispatches to the correct converter based on format parameter.
    All conversions happen LOCALLY - not via API.
    """

    def test_raw_format_returns_unchanged(self):
        """Test that raw format returns document unchanged."""
        document = {"documentId": "doc123", "title": "Test", "body": {"content": []}}
        result = format_document_response(document, "raw")

        assert result == document

    def test_unknown_format_returns_raw(self):
        """Test that unknown format defaults to raw."""
        document = {"documentId": "doc123", "title": "Test", "body": {"content": []}}
        result = format_document_response(document, "unknown_format")

        assert result == document

    def test_plain_text_format_calls_extract_text(self):
        """Test that plain_text format uses extract_text_from_document."""
        document = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Hello"}}]
                        }
                    }
                ]
            }
        }
        result = format_document_response(document, "plain_text")

        assert result["document_id"] == "doc123"
        assert result["title"] == "Test"
        assert result["content"] == "Hello"
        assert "word_count" in result

    def test_markdown_format_calls_convert_to_markdown(self):
        """Test that markdown format uses convert_document_to_markdown (LOCAL conversion)."""
        document = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Bold", "textStyle": {"bold": True}}}],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }
        result = format_document_response(document, "markdown")

        assert result["document_id"] == "doc123"
        # Local conversion adds ** for bold
        assert "**Bold**" in result["content"]

    def test_structured_format_calls_convert_to_structured(self):
        """Test that structured format uses convert_document_to_structured."""
        document = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {
                        "startIndex": 1,
                        "endIndex": 6,
                        "paragraph": {
                            "elements": [
                                {
                                    "startIndex": 1,
                                    "endIndex": 6,
                                    "textRun": {"content": "Hello", "textStyle": {}}
                                }
                            ],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }
        result = format_document_response(document, "structured")

        assert result["document_id"] == "doc123"
        assert "elements" in result
        assert result["elements"][0]["start_index"] == 1

    def test_normalized_format_calls_normalize(self):
        """Test that normalized format uses normalize_document_response."""
        document = {
            "documentId": "doc123",
            "title": "Test",
            "revisionId": "rev456",
            "body": {"content": []}
        }
        result = format_document_response(document, "normalized")

        assert result["documentId"] == "doc123"
        assert result["title"] == "Test"
        assert result["revisionId"] == "rev456"
        assert "content" in result


class TestExtractTextFromDocument:
    """Tests for extract_text_from_document function."""

    def test_extracts_text_from_paragraphs(self):
        """Test that text is extracted from paragraph elements."""
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Hello "}}
                            ]
                        }
                    },
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "World"}}
                            ]
                        }
                    }
                ]
            }
        }

        result = extract_text_from_document(document)
        assert result == "Hello World"

    def test_handles_empty_document(self):
        """Test that empty document returns empty string."""
        document = {"body": {"content": []}}
        result = extract_text_from_document(document)

        assert result == ""

    def test_handles_missing_body(self):
        """Test that missing body returns empty string."""
        document = {}
        result = extract_text_from_document(document)

        assert result == ""


class TestConvertDocumentToMarkdown:
    """Tests for convert_document_to_markdown function."""

    def test_heading_conversion(self):
        """Test that headings are converted to markdown."""
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Title", "textStyle": {}}}],
                            "paragraphStyle": {"namedStyleType": "HEADING_1"}
                        }
                    }
                ]
            }
        }

        result = convert_document_to_markdown(document)
        assert result.startswith("# ")
        assert "Title" in result

    def test_bold_conversion(self):
        """Test that bold text is converted to markdown."""
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "bold", "textStyle": {"bold": True}}}],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = convert_document_to_markdown(document)
        assert "**bold**" in result

    def test_italic_conversion(self):
        """Test that italic text is converted to markdown."""
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "italic", "textStyle": {"italic": True}}}],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = convert_document_to_markdown(document)
        assert "*italic*" in result

    def test_link_conversion(self):
        """Test that links are converted to markdown."""
        document = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{
                                "textRun": {
                                    "content": "click",
                                    "textStyle": {"link": {"url": "https://example.com"}}
                                }
                            }],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = convert_document_to_markdown(document)
        assert "[click](https://example.com)" in result
