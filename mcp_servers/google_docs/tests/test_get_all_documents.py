"""Unit tests for google_docs_get_all_documents tool."""

import pytest
from unittest.mock import patch, MagicMock


class TestGetAllDocumentsApiCalls:
    """Tests for Google Drive API call parameters."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_api_called_with_correct_query(self):
        """Test that files().list() is called with correct Google Docs MIME type query."""
        from server import get_all_documents, auth_token_context

        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": []
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_service):
                await get_all_documents()

                # Verify the API was called with correct parameters
                mock_service.files.return_value.list.assert_called_once_with(
                    q="mimeType='application/vnd.google-apps.document'",
                    fields="nextPageToken, files(id, name, createdTime, modifiedTime, webViewLink)",
                    orderBy="modifiedTime desc"
                )
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_uses_drive_service_not_docs_service(self):
        """Test that get_drive_service is used instead of get_docs_service."""
        from server import get_all_documents, auth_token_context

        mock_drive_service = MagicMock()
        mock_drive_service.files.return_value.list.return_value.execute.return_value = {
            "files": []
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_drive_service) as mock_get_drive:
                await get_all_documents()
                mock_get_drive.assert_called_once_with("test_token")
        finally:
            auth_token_context.reset(token)


class TestGetAllDocumentsResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_formatted_documents_list(self):
        """Test that documents are formatted with correct keys."""
        from server import get_all_documents, auth_token_context

        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": [
                {
                    "id": "doc1",
                    "name": "Document 1",
                    "createdTime": "2024-01-01T00:00:00Z",
                    "modifiedTime": "2024-01-02T00:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc1/edit"
                },
                {
                    "id": "doc2",
                    "name": "Document 2",
                    "createdTime": "2024-01-03T00:00:00Z",
                    "modifiedTime": "2024-01-04T00:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc2/edit"
                }
            ]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_service):
                result = await get_all_documents()

                assert "documents" in result
                assert "total_count" in result
                assert result["total_count"] == 2

                # Check first document structure
                doc1 = result["documents"][0]
                assert doc1["id"] == "doc1"
                assert doc1["name"] == "Document 1"
                assert doc1["createdAt"] == "2024-01-01T00:00:00Z"
                assert doc1["modifiedAt"] == "2024-01-02T00:00:00Z"
                assert doc1["url"] == "https://docs.google.com/document/d/doc1/edit"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_returns_empty_list_when_no_documents(self):
        """Test that empty list is returned when no documents exist."""
        from server import get_all_documents, auth_token_context

        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": []
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_service):
                result = await get_all_documents()

                assert result["documents"] == []
                assert result["total_count"] == 0
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_handles_missing_optional_fields(self):
        """Test that missing optional fields are handled gracefully."""
        from server import get_all_documents, auth_token_context

        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": [
                {
                    "id": "doc1",
                    "name": "Document 1"
                    # Missing createdTime, modifiedTime, webViewLink
                }
            ]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_service):
                result = await get_all_documents()

                doc = result["documents"][0]
                assert doc["id"] == "doc1"
                assert doc["name"] == "Document 1"
                assert doc["createdAt"] is None
                assert doc["modifiedAt"] is None
                assert doc["url"] is None
        finally:
            auth_token_context.reset(token)


class TestGetAllDocumentsErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_raises_on_api_error(self):
        """Test that API errors are properly raised."""
        from server import get_all_documents, auth_token_context
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status = 403
        mock_service.files.return_value.list.return_value.execute.side_effect = HttpError(
            mock_resp,
            b'{"error": {"message": "Access denied"}}'
        )

        token = auth_token_context.set("test_token")
        try:
            with patch('server.get_drive_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Drive API Error"):
                    await get_all_documents()
        finally:
            auth_token_context.reset(token)
