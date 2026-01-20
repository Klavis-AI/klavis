"""Unit tests for markdown parsing helper functions."""

import pytest


class TestParseInlineFormatting:
    """Tests for parse_inline_formatting function."""

    def test_plain_text_unchanged(self):
        """Test that plain text without formatting is unchanged."""
        from server import parse_inline_formatting

        text = "Hello World"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "Hello World"
        assert len(style_ranges) == 0

    def test_bold_double_asterisk(self):
        """Test that **text** is parsed as bold."""
        from server import parse_inline_formatting

        text = "**bold text**"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert style_ranges[0]["start"] == 0
        assert style_ranges[0]["end"] == 9

    def test_bold_double_underscore(self):
        """Test that __text__ is parsed as bold."""
        from server import parse_inline_formatting

        text = "__bold text__"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True

    def test_italic_single_asterisk(self):
        """Test that *text* is parsed as italic."""
        from server import parse_inline_formatting

        text = "*italic text*"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "italic text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["italic"] is True

    def test_italic_single_underscore(self):
        """Test that _text_ is parsed as italic."""
        from server import parse_inline_formatting

        text = "_italic text_"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "italic text"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["italic"] is True

    def test_bold_italic_triple_asterisk(self):
        """Test that ***text*** is parsed as bold and italic."""
        from server import parse_inline_formatting

        text = "***bold italic***"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "bold italic"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert style_ranges[0]["style"]["italic"] is True

    def test_strikethrough(self):
        """Test that ~~text~~ is parsed as strikethrough."""
        from server import parse_inline_formatting

        text = "~~strikethrough~~"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "strikethrough"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["strikethrough"] is True

    def test_link(self):
        """Test that [text](url) is parsed as link."""
        from server import parse_inline_formatting

        text = "[click here](https://example.com)"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "click here"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["link"]["url"] == "https://example.com"

    def test_inline_code(self):
        """Test that `code` is parsed as code."""
        from server import parse_inline_formatting

        text = "`inline code`"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "inline code"
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["code"] is True

    def test_escaped_underscore(self):
        """Test that \\_ produces literal underscore."""
        from server import parse_inline_formatting

        text = "access\\_token"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "access_token"
        assert len(style_ranges) == 0

    def test_escaped_asterisk(self):
        """Test that \\* produces literal asterisk."""
        from server import parse_inline_formatting

        text = "\\*not bold\\*"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "*not bold*"
        assert len(style_ranges) == 0

    def test_escaped_backtick(self):
        """Test that \\` produces literal backtick."""
        from server import parse_inline_formatting

        text = "\\`not code\\`"
        result_text, style_ranges = parse_inline_formatting(text, 0)

        assert result_text == "`not code`"
        assert len(style_ranges) == 0

    def test_mixed_formatting(self):
        """Test mixed formatting in same line."""
        from server import parse_inline_formatting

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
        from server import parse_inline_formatting

        text = "**bold**"
        result_text, style_ranges = parse_inline_formatting(text, 100)

        assert style_ranges[0]["start"] == 100
        assert style_ranges[0]["end"] == 104


class TestParseMarkdownText:
    """Tests for parse_markdown_text function."""

    def test_heading_1(self):
        """Test that # Heading is parsed as HEADING_1."""
        from server import parse_markdown_text

        text = "# Heading 1"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        assert plain_text == "Heading 1"
        assert len(paragraph_styles) == 1
        assert paragraph_styles[0]["paragraph_style"]["namedStyleType"] == "HEADING_1"

    def test_heading_levels(self):
        """Test that different heading levels are parsed correctly."""
        from server import parse_markdown_text

        heading_map = {
            "# H1": "HEADING_1",
            "## H2": "HEADING_2",
            "### H3": "HEADING_3",
            "#### H4": "HEADING_4",
            "##### H5": "HEADING_5",
            "###### H6": "HEADING_6",
        }

        for markdown, expected_style in heading_map.items():
            plain_text, style_ranges, paragraph_styles = parse_markdown_text(markdown)
            assert len(paragraph_styles) == 1
            assert paragraph_styles[0]["paragraph_style"]["namedStyleType"] == expected_style

    def test_bullet_point_dash(self):
        """Test that - item is parsed as bullet point."""
        from server import parse_markdown_text

        text = "- Item 1"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        # Bullet is converted to bullet character
        assert "• Item 1" in plain_text or "Item 1" in plain_text

    def test_bullet_point_asterisk(self):
        """Test that * item is parsed as bullet point."""
        from server import parse_markdown_text

        text = "* Item 1"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        assert "• Item 1" in plain_text or "Item 1" in plain_text

    def test_inline_formatting_in_heading(self):
        """Test that inline formatting works within headings."""
        from server import parse_markdown_text

        text = "# **Bold** Heading"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        assert "Bold Heading" in plain_text
        assert len(style_ranges) == 1
        assert style_ranges[0]["style"]["bold"] is True
        assert len(paragraph_styles) == 1

    def test_multiple_lines(self):
        """Test that multiple lines are parsed correctly."""
        from server import parse_markdown_text

        text = "Line 1\nLine 2\nLine 3"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

        assert plain_text == "Line 1\nLine 2\nLine 3"

    def test_multiline_with_formatting(self):
        """Test multiline text with various formatting."""
        from server import parse_markdown_text

        text = "# Title\n\nSome **bold** text\n- A bullet"
        plain_text, style_ranges, paragraph_styles = parse_markdown_text(text)

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
        from server import hex_to_rgb

        result = hex_to_rgb("#FF0000")
        assert result["red"] == 1.0
        assert result["green"] == 0.0
        assert result["blue"] == 0.0

    def test_pure_green(self):
        """Test #00FF00 converts to green."""
        from server import hex_to_rgb

        result = hex_to_rgb("#00FF00")
        assert result["red"] == 0.0
        assert result["green"] == 1.0
        assert result["blue"] == 0.0

    def test_pure_blue(self):
        """Test #0000FF converts to blue."""
        from server import hex_to_rgb

        result = hex_to_rgb("#0000FF")
        assert result["red"] == 0.0
        assert result["green"] == 0.0
        assert result["blue"] == 1.0

    def test_white(self):
        """Test #FFFFFF converts to white."""
        from server import hex_to_rgb

        result = hex_to_rgb("#FFFFFF")
        assert result["red"] == 1.0
        assert result["green"] == 1.0
        assert result["blue"] == 1.0

    def test_black(self):
        """Test #000000 converts to black."""
        from server import hex_to_rgb

        result = hex_to_rgb("#000000")
        assert result["red"] == 0.0
        assert result["green"] == 0.0
        assert result["blue"] == 0.0

    def test_without_hash(self):
        """Test that hex color without # is handled."""
        from server import hex_to_rgb

        result = hex_to_rgb("FF0000")
        assert result["red"] == 1.0

    def test_lowercase(self):
        """Test that lowercase hex is handled."""
        from server import hex_to_rgb

        result = hex_to_rgb("#ff0000")
        assert result["red"] == 1.0

    def test_mixed_color(self):
        """Test a mixed color value."""
        from server import hex_to_rgb

        # #808080 = gray (128, 128, 128)
        result = hex_to_rgb("#808080")
        assert 0.5 <= result["red"] <= 0.51  # ~0.502
        assert 0.5 <= result["green"] <= 0.51
        assert 0.5 <= result["blue"] <= 0.51

    def test_invalid_hex_raises_error(self):
        """Test that invalid hex raises ValueError."""
        from server import hex_to_rgb

        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("invalid")

    def test_short_hex_raises_error(self):
        """Test that short hex raises ValueError."""
        from server import hex_to_rgb

        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FFF")


class TestFormatDocumentResponse:
    """Tests for format_document_response function."""

    def test_raw_format_returns_unchanged(self):
        """Test that raw format returns document unchanged."""
        from server import format_document_response

        document = {"documentId": "doc123", "title": "Test", "body": {"content": []}}
        result = format_document_response(document, "raw")

        assert result == document

    def test_unknown_format_returns_raw(self):
        """Test that unknown format defaults to raw."""
        from server import format_document_response

        document = {"documentId": "doc123", "title": "Test", "body": {"content": []}}
        result = format_document_response(document, "unknown_format")

        assert result == document


class TestExtractTextFromDocument:
    """Tests for extract_text_from_document function."""

    def test_extracts_text_from_paragraphs(self):
        """Test that text is extracted from paragraph elements."""
        from server import extract_text_from_document

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
        from server import extract_text_from_document

        document = {"body": {"content": []}}
        result = extract_text_from_document(document)

        assert result == ""

    def test_handles_missing_body(self):
        """Test that missing body returns empty string."""
        from server import extract_text_from_document

        document = {}
        result = extract_text_from_document(document)

        assert result == ""


class TestConvertDocumentToMarkdown:
    """Tests for convert_document_to_markdown function."""

    def test_heading_conversion(self):
        """Test that headings are converted to markdown."""
        from server import convert_document_to_markdown

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
        from server import convert_document_to_markdown

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
        from server import convert_document_to_markdown

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
        from server import convert_document_to_markdown

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
