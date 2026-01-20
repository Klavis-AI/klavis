"""Unit tests for google_docs_create_blank_document tool."""

import pytest
from unittest.mock import patch, MagicMock


class TestCreateBlankDocumentInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_title_is_required(self):
        """Test that title parameter is required."""
        from server import create_blank_document

        with pytest.raises(TypeError):
            await create_blank_document()


class TestCreateBlankDocumentApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_create_called_with_title_in_body(self):
        """Test that documents().create() is called with title in body."""
        from server import create_blank_document, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.create.return_value.execute.return_value = {
            "documentId": "new_doc_123",
            "title": "My New Document"
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                await create_blank_document("My New Document")

                # Verify create was called with correct body
                mock_service.documents.return_value.create.assert_called_once_with(
                    body={"title": "My New Document"}
                )
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_preserves_title_with_special_characters(self):
        """Test that titles with special characters are preserved."""
        from server import create_blank_document, auth_token_context

        test_titles = [
            "Document with spaces",
            "Document_with_underscores",
            "Document-with-dashes",
            "Document (with parentheses)",
            "日本語のタイトル",
            "Title with 'quotes'",
            'Title with "double quotes"',
        ]

        mock_service = MagicMock()

        token = auth_token_context.set("test_token")
        try:
            for title in test_titles:
                mock_service.reset_mock()
                mock_service.documents.return_value.create.return_value.execute.return_value = {
                    "documentId": "doc123",
                    "title": title
                }

                with patch('server.get_docs_service', return_value=mock_service):
                    await create_blank_document(title)

                    call_args = mock_service.documents.return_value.create.call_args
                    assert call_args.kwargs["body"]["title"] == title
        finally:
            auth_token_context.reset(token)


class TestCreateBlankDocumentResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_document_info(self):
        """Test that response contains document info."""
        from server import create_blank_document, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.create.return_value.execute.return_value = {
            "documentId": "abc123xyz",
            "title": "Test Document"
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await create_blank_document("Test Document")

                assert result["title"] == "Test Document"
                assert result["id"] == "abc123xyz"
                assert result["url"] == "https://docs.google.com/document/d/abc123xyz/edit"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_url_format_is_correct(self):
        """Test that the returned URL follows correct format."""
        from server import create_blank_document, auth_token_context

        mock_service = MagicMock()
        mock_service.documents.return_value.create.return_value.execute.return_value = {
            "documentId": "1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ",
            "title": "Test"
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                result = await create_blank_document("Test")

                expected_url = "https://docs.google.com/document/d/1rcwYn0czFTu-88s5h88gqWw5nSB2WVYbo6zPvCFjPiQ/edit"
                assert result["url"] == expected_url
        finally:
            auth_token_context.reset(token)


class TestCreateBlankDocumentErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from server import create_blank_document, auth_token_context
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 400
        mock_service.documents.return_value.create.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Invalid request"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await create_blank_document("Test")
        finally:
            auth_token_context.reset(token)
