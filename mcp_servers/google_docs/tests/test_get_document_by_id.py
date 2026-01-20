"""Unit tests for google_docs_get_document_by_id tool."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestGetDocumentByIdInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        from server import get_document_by_id, auth_token_context

        token = auth_token_context.set("test_token")
        try:
            # document_id is a required positional argument
            with pytest.raises(TypeError):
                await get_document_by_id()
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_response_format_defaults_to_raw(self):
        """Test that response_format defaults to 'raw' when not specified."""
        from server import get_document_by_id, auth_token_context

        mock_response = {
            "documentId": "doc123",
            "title": "Test Doc",
            "body": {"content": []}
        }

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = mock_response

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123")
                # When format is 'raw', the response should be the full API response
                assert result == mock_response
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_called_with_correct_document_id(self):
        """Test that documents().get() is called with correct documentId."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "my_doc_id",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
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
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = {
            "documentId": "1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ",
            "title": "Test",
            "body": {"content": []}
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await get_document_by_id("1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ")

                mock_service.documents.return_value.get.assert_called_once_with(
                    documentId="1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ"
                )
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdResponseFormats:
    """Tests for different response formats."""

    @pytest.fixture
    def sample_document(self):
        """Sample Google Docs API response for testing."""
        return {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "startIndex": 1,
                        "endIndex": 12,
                        "paragraph": {
                            "elements": [
                                {
                                    "startIndex": 1,
                                    "endIndex": 12,
                                    "textRun": {
                                        "content": "Hello World",
                                        "textStyle": {"bold": True}
                                    }
                                }
                            ],
                            "paragraphStyle": {"namedStyleType": "HEADING_1"}
                        }
                    }
                ]
            }
        }

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raw_format_returns_full_response(self, sample_document):
        """Test that 'raw' format returns the complete API response."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = sample_document

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "raw")
                assert result == sample_document
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_plain_text_format_extracts_text(self, sample_document):
        """Test that 'plain_text' format extracts text content."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = sample_document

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "plain_text")

                assert result["document_id"] == "doc123"
                assert result["title"] == "Test Document"
                assert "content" in result
                assert result["content"] == "Hello World"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_markdown_format_includes_formatting(self, sample_document):
        """Test that 'markdown' format converts to markdown syntax."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = sample_document

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "markdown")

                assert result["document_id"] == "doc123"
                assert "content" in result
                # HEADING_1 should be converted to # prefix
                assert result["content"].startswith("# ")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_structured_format_includes_indices(self, sample_document):
        """Test that 'structured' format includes character indices."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = sample_document

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "structured")

                assert result["document_id"] == "doc123"
                assert "elements" in result
                assert len(result["elements"]) > 0
                # Check indices are present
                assert "start_index" in result["elements"][0]
                assert "end_index" in result["elements"][0]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_normalized_format_simplifies_structure(self, sample_document):
        """Test that 'normalized' format returns simplified structure."""
        from server import get_document_by_id, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.get.return_value.execute.return_value = sample_document

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await get_document_by_id("doc123", "normalized")

                assert result["documentId"] == "doc123"
                assert result["title"] == "Test Document"
                assert "content" in result
        finally:
            auth_token_context.reset(token)


class TestGetDocumentByIdErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from server import get_document_by_id, auth_token_context
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
            with patch('server.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await get_document_by_id("nonexistent_doc")
        finally:
            auth_token_context.reset(token)
