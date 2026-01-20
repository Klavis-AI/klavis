"""Unit tests for google_docs_insert_text_at_end tool."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from server import (
    auth_token_context,
    insert_text_at_end,
)


class TestInsertTextAtEndInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        with pytest.raises(TypeError):
            await insert_text_at_end()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_text_is_required(self):
        """Test that text parameter is required."""
        with pytest.raises(TypeError):
            await insert_text_at_end("doc123")


class TestInsertTextAtEndApiCalls:
    """Tests for Google Docs API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_gets_document_to_find_end_index(self):
        """Test that document is fetched to determine end index."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service), \
                 patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {"endIndex": 100}
                        ]
                    }
                }

                await insert_text_at_end("doc123", "New text")

                mock_get_doc.assert_called_once_with("doc123")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_batch_update_called_with_correct_insert_request(self):
        """Test that batchUpdate is called with correct insertText request."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service), \
                 patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {
                        "content": [
                            {"endIndex": 50}
                        ]
                    }
                }

                await insert_text_at_end("doc123", "Hello World")

                # Verify batchUpdate was called with correct parameters
                mock_service.documents.return_value.batchUpdate.assert_called_once()
                call_args = mock_service.documents.return_value.batchUpdate.call_args

                assert call_args.kwargs["documentId"] == "doc123"
                requests = call_args.kwargs["body"]["requests"]
                assert len(requests) == 1

                insert_request = requests[0]["insertText"]
                # endIndex - 1 = 50 - 1 = 49
                assert insert_request["location"]["index"] == 49
                assert insert_request["text"] == "Hello World"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_insert_index_is_end_index_minus_one(self):
        """Test that insert index is calculated as endIndex - 1."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        test_cases = [
            (10, 9),    # endIndex 10 -> insert at 9
            (100, 99),  # endIndex 100 -> insert at 99
            (1, 0),     # endIndex 1 -> insert at 0
        ]

        token = auth_token_context.set("test_token")
        try:
            for end_index, expected_insert_index in test_cases:
                mock_service.reset_mock()

                with patch('server.get_docs_service', return_value=mock_service), \
                     patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                    mock_get_doc.return_value = {
                        "body": {
                            "content": [
                                {"endIndex": end_index}
                            ]
                        }
                    }

                    await insert_text_at_end("doc123", "text")

                    call_args = mock_service.documents.return_value.batchUpdate.call_args
                    requests = call_args.kwargs["body"]["requests"]
                    actual_index = requests[0]["insertText"]["location"]["index"]
                    assert actual_index == expected_insert_index, \
                        f"For endIndex {end_index}, expected insert at {expected_insert_index}, got {actual_index}"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_preserves_text_exactly(self):
        """Test that text content is preserved exactly as provided."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        test_texts = [
            "Simple text",
            "Text with\nnewlines",
            "Text with special chars: @#$%^&*()",
            "Unicode: 日本語テスト",
            "Whitespace:   spaces   and\ttabs",
        ]

        token = auth_token_context.set("test_token")
        try:
            for text in test_texts:
                mock_service.reset_mock()

                with patch('server.get_docs_service', return_value=mock_service), \
                     patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                    mock_get_doc.return_value = {
                        "body": {"content": [{"endIndex": 10}]}
                    }

                    await insert_text_at_end("doc123", text)

                    call_args = mock_service.documents.return_value.batchUpdate.call_args
                    requests = call_args.kwargs["body"]["requests"]
                    actual_text = requests[0]["insertText"]["text"]
                    assert actual_text == text
        finally:
            auth_token_context.reset(token)


class TestInsertTextAtEndResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_success_response(self):
        """Test that success response is returned."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service), \
                 patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {"content": [{"endIndex": 10}]}
                }

                result = await insert_text_at_end("doc123", "test")

                assert result["id"] == "doc123"
                assert result["status"] == "success"
        finally:
            auth_token_context.reset(token)


class TestInsertTextAtEndErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 403
        mock_service.documents.return_value.batchUpdate.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Permission denied"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_docs_service', return_value=mock_service), \
                 patch('server._get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {"content": [{"endIndex": 10}]}
                }

                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await insert_text_at_end("doc123", "test")
        finally:
            auth_token_context.reset(token)
