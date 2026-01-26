"""Unit tests for google_docs_insert_formatted_text tool."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from server import (
    auth_token_context,
    insert_formatted_text,
)


class TestInsertFormattedTextInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        with pytest.raises(TypeError):
            await insert_formatted_text()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_anchor_text_is_required(self):
        """Test that anchor_text parameter is required."""
        with pytest.raises(TypeError):
            await insert_formatted_text("doc123")

    @pytest.mark.asyncio(loop_scope="function")
    async def test_formatted_text_is_required(self):
        """Test that formatted_text parameter is required."""
        with pytest.raises(TypeError):
            await insert_formatted_text("doc123", "anchor")


class TestInsertFormattedTextApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_anchor_text_found_and_replaced(self):
        """Test that anchor text is found and replaced with formatted text."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                # Mock document with "Hello World" content
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "Hello World\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                result = await insert_formatted_text(
                    "doc123",
                    "World",
                    "World **is great**"
                )

                assert result["success"] is True
                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # First request should be deleteContentRange for "World"
                assert "deleteContentRange" in requests[0]
                delete_range = requests[0]["deleteContentRange"]["range"]
                assert delete_range["startIndex"] == 7  # "Hello " = 6 chars, so "World" starts at 7 (1-based)
                assert delete_range["endIndex"] == 12  # 7 + 5 = 12

                # Second request should be insertText
                assert "insertText" in requests[1]
                assert requests[1]["insertText"]["location"]["index"] == 7
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_anchor_text_not_found_returns_error(self):
        """Test that missing anchor text returns an error."""
        mock_service = MagicMock()

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "Hello World\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                result = await insert_formatted_text(
                    "doc123",
                    "NotFound",
                    "NotFound with **bold**"
                )

                assert result["success"] is False
                assert "not found" in result["error"].lower()
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_bold_text_generates_style_request(self):
        """Test that **bold** generates updateTextStyle request."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor text\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "anchor **bold text**")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Should have style request for bold
                style_requests = [r for r in requests if "updateTextStyle" in r]
                assert len(style_requests) > 0

                bold_request = style_requests[0]["updateTextStyle"]
                assert bold_request["textStyle"]["bold"] is True
                assert "bold" in bold_request["fields"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_italic_text_generates_style_request(self):
        """Test that *italic* generates updateTextStyle request."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor text\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "anchor *italic text*")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                style_requests = [r for r in requests if "updateTextStyle" in r]
                assert len(style_requests) > 0

                italic_request = style_requests[0]["updateTextStyle"]
                assert italic_request["textStyle"]["italic"] is True
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_heading_generates_paragraph_style_request(self):
        """Test that # Heading generates updateParagraphStyle request."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "# Heading 1")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                para_requests = [r for r in requests if "updateParagraphStyle" in r]
                assert len(para_requests) > 0

                heading_request = para_requests[0]["updateParagraphStyle"]
                assert heading_request["paragraphStyle"]["namedStyleType"] == "HEADING_1"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_link_generates_style_request_with_url(self):
        """Test that [text](url) generates updateTextStyle request with link."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "anchor [click here](https://example.com)")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                style_requests = [r for r in requests if "updateTextStyle" in r]
                assert len(style_requests) > 0

                link_request = style_requests[0]["updateTextStyle"]
                assert link_request["textStyle"]["link"]["url"] == "https://example.com"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_inline_code_generates_monospace_style(self):
        """Test that `code` generates monospace font style."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "anchor Use `access_token` variable")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                style_requests = [r for r in requests if "updateTextStyle" in r]
                assert len(style_requests) > 0

                code_request = style_requests[0]["updateTextStyle"]
                assert code_request["textStyle"]["weightedFontFamily"]["fontFamily"] == "Courier New"
                assert "backgroundColor" in code_request["textStyle"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_escaped_underscore_not_interpreted_as_italic(self):
        """Test that \\_escaped\\_ underscores are not interpreted as italic."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                await insert_formatted_text("doc123", "anchor", "anchor Use \\_underscore\\_ text")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Insert text should contain literal underscores
                insert_request = requests[1]["insertText"]
                assert "_underscore_" in insert_request["text"]

                # Should not have any italic style requests
                style_requests = [r for r in requests if "updateTextStyle" in r]
                for req in style_requests:
                    if "italic" in req["updateTextStyle"].get("textStyle", {}):
                        pytest.fail("Should not have italic style for escaped underscores")
        finally:
            auth_token_context.reset(token)


class TestInsertFormattedTextResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_success_response_structure(self):
        """Test that success response has correct structure."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                result = await insert_formatted_text("doc123", "anchor", "anchor **bold** and *italic*")

                assert result["success"] is True
                assert result["document_id"] == "doc123"
                assert result["anchor_text"] == "anchor"
                assert "inserted_range" in result
                assert "characters_inserted" in result
                assert "characters_replaced" in result
                assert "styles_applied" in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_style_counts_are_accurate(self):
        """Test that style counts in response are accurate."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                result = await insert_formatted_text(
                    "doc123",
                    "anchor",
                    "# Heading\n**bold** and *italic* with `code`"
                )

                styles = result["styles_applied"]
                assert styles["headings"] == 1
                assert styles["bold_ranges"] == 1
                assert styles["italic_ranges"] == 1
                assert styles["code_ranges"] == 1
        finally:
            auth_token_context.reset(token)


class TestInsertFormattedTextErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 500
        mock_service.documents.return_value.batchUpdate.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Internal error"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.insert_formatted_text.get_docs_service', return_value=mock_service), \
                 patch('tools.insert_formatted_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {"textRun": {"content": "anchor\n"}}
                                    ]
                                }
                            }
                        ]
                    }
                }

                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await insert_formatted_text("doc123", "anchor", "anchor text")
        finally:
            auth_token_context.reset(token)
