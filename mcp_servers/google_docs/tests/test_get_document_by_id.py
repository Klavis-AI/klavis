"""Unit tests for google_docs_get_document_by_id tool.

This file focuses on:
- Input parameter validation
- API call parameters (documents().get())
- Correct dispatch to format_document_response

For detailed format conversion tests, see test_format_converters.py
"""

import pytest
from unittest.mock import patch, MagicMock

from server import (
    auth_token_context,
    get_document_by_id,
)


class TestGetDocumentByIdInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        token = auth_token_context.set("test_token")
        try:
            with pytest.raises(TypeError):
                await get_document_by_id()
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_response_format_defaults_to_normalized(self):
        """Test that response_format defaults to 'normalized' when not specified for backward compatibility."""
        mock_response = {
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": []}
        }

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = mock_response

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123")
                # When format is 'normalized' (default), the response should be normalized
                assert "content" in result  # normalized format has 'content' key
                assert result["documentId"] == "doc123"
                assert result["title"] == "Test Doc"
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_called_with_correct_document_id(self):
        """Test that documents().get() is called with correct documentId."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "my_doc_id",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                await get_document_by_id("my_doc_id")

                # Verify the API was called with correct parameters
                mock_service.documents.return_value.get.assert_called_once_with(
                    documentId="my_doc_id"
                )
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_called_with_special_characters_in_id(self):
        """Test that document IDs with special characters are passed correctly."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                await get_document_by_id("1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ")

                mock_service.documents.return_value.get.assert_called_once_with(
                    documentId="1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ"
                )
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_called_once_regardless_of_format(self):
        """Test that API is called exactly once for any format."""
        formats = ["raw", "plain_text", "markdown", "structured", "normalized"]

        for fmt in formats:
            mock_service = MagicMock()
            mock_service.documents.return_value.get.return_value.execute.return_value = {
                "documentId": "doc123",
                "title": "Test",
                "body": {"content": []}
            }

            token = auth_token_context.set("test_token")
            try:
                with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                    await get_document_by_id("doc123", fmt)

                    # API should be called exactly once
                    mock_service.documents.return_value.get.assert_called_once()
            finally:
                auth_token_context.reset(token)


class TestGetDocumentByIdFormatDispatch:
    """Tests for format_document_response dispatch.

    These tests verify that the correct format is passed to format_document_response.
    Detailed conversion logic tests are in test_format_converters.py.
    """

    @pytest.mark.asyncio(loop_scope="function")
    async def test_format_document_response_called_with_format(self):
        """Test that format_document_response is called with correct format."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        formats_to_test = ["raw", "plain_text", "markdown", "structured", "normalized"]

        for fmt in formats_to_test:
            token = auth_token_context.set("test_token")
            try:
                with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service), \
                     patch('tools.get_document_by_id.format_document_response') as mock_format:
                    mock_format.return_value = {"formatted": True}

                    await get_document_by_id("doc123", fmt)

                    # Verify format_document_response was called with correct format
                    mock_format.assert_called_once()
                    call_args = mock_format.call_args
                    assert call_args.kwargs["response_format"] == fmt, f"Expected format '{fmt}', got '{call_args.kwargs['response_format']}'"
            finally:
                auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raw_format_returns_dict(self):
        """Test that 'raw' format returns a dict (API response)."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "raw")
                assert isinstance(result, dict)
                assert "documentId" in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_plain_text_format_returns_dict_with_content(self):
        """Test that 'plain_text' format returns dict with content key."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "plain_text")
                assert isinstance(result, dict)
                assert "content" in result
                assert "document_id" in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_markdown_format_returns_dict_with_content(self):
        """Test that 'markdown' format returns dict with content key."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "markdown")
                assert isinstance(result, dict)
                assert "content" in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_structured_format_returns_dict_with_elements(self):
        """Test that 'structured' format returns dict with elements key."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured")
                assert isinstance(result, dict)
                assert "elements" in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_normalized_format_returns_dict_with_content(self):
        """Test that 'normalized' format returns dict with content key."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "normalized")
                assert isinstance(result, dict)
                assert "content" in result
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdPartialRetrieval:
    """Tests for partial document retrieval with start_paragraph and end_paragraph."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_with_start_paragraph_only(self):
        """Test partial retrieval with only start_paragraph specified."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 1\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 2\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 3\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured", start_paragraph=2)
                # Should include paragraphs 2 and 3
                assert len(result["elements"]) == 2
                assert result["filtered_range"]["start_paragraph"] == 2
                assert result["filtered_range"]["end_paragraph"] is None
                assert result["filtered_range"]["total_paragraphs"] == 3
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_with_end_paragraph_only(self):
        """Test partial retrieval with only end_paragraph specified."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 1\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 2\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 3\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured", end_paragraph=2)
                # Should include paragraphs 1 and 2
                assert len(result["elements"]) == 2
                assert result["filtered_range"]["start_paragraph"] is None
                assert result["filtered_range"]["end_paragraph"] == 2
                assert result["filtered_range"]["total_paragraphs"] == 3
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_with_both_paragraphs(self):
        """Test partial retrieval with both start_paragraph and end_paragraph."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 1\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 2\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 3\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 4\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 5\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured", start_paragraph=2, end_paragraph=4)
                # Should include paragraphs 2, 3, and 4
                assert len(result["elements"]) == 3
                assert result["filtered_range"]["start_paragraph"] == 2
                assert result["filtered_range"]["end_paragraph"] == 4
                assert result["filtered_range"]["total_paragraphs"] == 5
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_out_of_range(self):
        """Test partial retrieval when range is beyond document length."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 1\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 2\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured", start_paragraph=10, end_paragraph=20)
                # No paragraphs in that range
                assert len(result["elements"]) == 0
                assert result["filtered_range"]["total_paragraphs"] == 2
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_returns_full_doc_when_no_range(self):
        """Test that full document is returned when no range is specified."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 1\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 2\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Paragraph 3\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured")
                # All elements should be included
                assert len(result["elements"]) == 3
                assert "filtered_range" not in result
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_works_with_plain_text_format(self):
        """Test partial retrieval with plain_text format includes filtered_range."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "Hello\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "World\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Test\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "plain_text", start_paragraph=1, end_paragraph=2)
                assert "filtered_range" in result
                assert result["filtered_range"]["start_paragraph"] == 1
                assert result["filtered_range"]["end_paragraph"] == 2
                # Content should only contain paragraphs 1 and 2
                assert "Hello" in result["content"]
                assert "World" in result["content"]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_partial_retrieval_single_paragraph(self):
        """Test retrieving a single paragraph."""
        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "doc123",
            "title": "Test",
            "body": {
                "content": [
                    {"paragraph": {"elements": [{"textRun": {"content": "First\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Second\n"}}]}},
                    {"paragraph": {"elements": [{"textRun": {"content": "Third\n"}}]}}
                ]
            }
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "plain_text", start_paragraph=2, end_paragraph=2)
                # Should only include paragraph 2
                assert "Second" in result["content"]
                assert "First" not in result["content"]
                assert "Third" not in result["content"]
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 404
        mock_service.documents.return_value.get.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Document not found"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await get_document_by_id("nonexistent_doc")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_permission_denied(self):
        """Test that permission denied errors are properly raised."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 403
        mock_service.documents.return_value.get.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Permission denied"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.get_document_by_id.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await get_document_by_id("private_doc")
        finally:
            auth_token_context.reset(token)
