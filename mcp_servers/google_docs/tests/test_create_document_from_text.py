"""Unit tests for google_docs_create_document_from_text tool."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from server import (
    auth_token_context,
    create_document_from_text,
)


class TestCreateDocumentFromTextInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_title_is_required(self):
        """Test that title parameter is required."""
        with pytest.raises(TypeError):
            await create_document_from_text()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_text_content_is_required(self):
        """Test that text_content parameter is required."""
        with pytest.raises(TypeError):
            await create_document_from_text("My Title")


class TestCreateDocumentFromTextApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_calls_create_blank_document_first(self):
        """Test that create_blank_document is called first with title."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                 patch('server.get_docs_service', return_value=mock_service):
                mock_create_blank.return_value = {
                    "title": "Test Doc",
                    "id": "doc123",
                    "url": "https://docs.google.com/document/d/doc123/edit"
                }

                await create_document_from_text("Test Doc", "Hello world")

                mock_create_blank.assert_called_once_with("Test Doc")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_batch_update_inserts_text_at_index_1(self):
        """Test that batchUpdate inserts text at index 1."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                 patch('server.get_docs_service', return_value=mock_service):
                mock_create_blank.return_value = {
                    "title": "Test Doc",
                    "id": "doc123",
                    "url": "https://docs.google.com/document/d/doc123/edit"
                }

                await create_document_from_text("Test Doc", "Hello world")

                # Verify batchUpdate was called with correct parameters
                mock_service.documents.return_value.batchUpdate.assert_called_once()
                call_args = mock_service.documents.return_value.batchUpdate.call_args

                assert call_args.kwargs["documentId"] == "doc123"
                requests = call_args.kwargs["body"]["requests"]
                assert len(requests) == 1

                insert_request = requests[0]["insertText"]
                # Text should be inserted at index 1
                assert insert_request["location"]["index"] == 1
                assert insert_request["text"] == "Hello world"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_uses_document_id_from_create_blank(self):
        """Test that document ID from create_blank_document is used for batchUpdate."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                 patch('server.get_docs_service', return_value=mock_service):
                mock_create_blank.return_value = {
                    "title": "Test Doc",
                    "id": "unique_doc_id_xyz",
                    "url": "https://docs.google.com/document/d/unique_doc_id_xyz/edit"
                }

                await create_document_from_text("Test Doc", "content")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                assert call_args.kwargs["documentId"] == "unique_doc_id_xyz"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_preserves_text_content_exactly(self):
        """Test that text content is preserved exactly as provided."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        test_contents = [
            "Simple text",
            "Text with\nnewlines\nand more lines",
            "Text with special chars: @#$%^&*()",
            "Unicode: 日本語テスト",
            "Multiple  spaces  preserved",
        ]

        token = auth_token_context.set("test_token")
        try:
            for content in test_contents:
                mock_service.reset_mock()

                with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                     patch('server.get_docs_service', return_value=mock_service):
                    mock_create_blank.return_value = {
                        "title": "Test",
                        "id": "doc123",
                        "url": "https://docs.google.com/document/d/doc123/edit"
                    }

                    await create_document_from_text("Test", content)

                    call_args = mock_service.documents.return_value.batchUpdate.call_args
                    requests = call_args.kwargs["body"]["requests"]
                    actual_text = requests[0]["insertText"]["text"]
                    assert actual_text == content
        finally:
            auth_token_context.reset(token)


class TestCreateDocumentFromTextResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_document_info(self):
        """Test that response contains document info."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                 patch('server.get_docs_service', return_value=mock_service):
                mock_create_blank.return_value = {
                    "title": "My Document",
                    "id": "doc_id_abc",
                    "url": "https://docs.google.com/document/d/doc_id_abc/edit"
                }

                result = await create_document_from_text("My Document", "content")

                assert result["title"] == "My Document"
                assert result["id"] == "doc_id_abc"
                assert result["url"] == "https://docs.google.com/document/d/doc_id_abc/edit"
        finally:
            auth_token_context.reset(token)


class TestCreateDocumentFromTextErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_create_blank_error(self):
        """Test that errors from create_blank_document propagate as RuntimeError."""
        from googleapiclient.errors import HttpError

        mock_resp = MagicMock()
        mock_resp.status = 400

        token = auth_token_context.set("test_token")
        try:
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank:
                mock_create_blank.side_effect = HttpError(
                    mock_resp,
                    b'{"error": {"message": "Invalid title"}}'
                )

                # HttpError is caught and re-raised as RuntimeError
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await create_document_from_text("", "content")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_batch_update_error(self):
        """Test that errors from batchUpdate propagate."""
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
            with patch('server.create_blank_document', new_callable=AsyncMock) as mock_create_blank, \
                 patch('server.get_docs_service', return_value=mock_service):
                mock_create_blank.return_value = {
                    "title": "Test",
                    "id": "doc123",
                    "url": "https://docs.google.com/document/d/doc123/edit"
                }

                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await create_document_from_text("Test", "content")
        finally:
            auth_token_context.reset(token)
