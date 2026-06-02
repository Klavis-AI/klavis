"""Unit tests for google_docs_edit_text tool."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from server import (
    auth_token_context,
    edit_text,
)


class TestEditTextInput:
    """Tests for input parameter validation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_document_id_is_required(self):
        """Test that document_id parameter is required."""
        with pytest.raises(TypeError):
            await edit_text()

    @pytest.mark.asyncio(loop_scope="function")
    async def test_old_text_and_new_text_are_required(self):
        """Test that old_text and new_text parameters are required."""
        with pytest.raises(TypeError):
            await edit_text("doc123")

    @pytest.mark.asyncio(loop_scope="function")
    async def test_defaults_for_optional_parameters(self):
        """Test that optional parameters have correct defaults."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                await edit_text("doc123", "old", "new")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                replace_request = requests[0]["replaceAllText"]["containsText"]

                # Default match_case should be True
                assert replace_request["matchCase"] is True
        finally:
            auth_token_context.reset(token)


class TestEditTextReplaceOperation:
    """Tests for text replacement operation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_replace_all_text_api_called(self):
        """Test that replaceAllText API is called for replace operation."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                await edit_text("doc123", "old text", "new text")

                mock_service.documents.return_value.batchUpdate.assert_called_once()
                call_args = mock_service.documents.return_value.batchUpdate.call_args

                assert call_args.kwargs["documentId"] == "doc123"
                requests = call_args.kwargs["body"]["requests"]
                assert len(requests) == 1
                assert "replaceAllText" in requests[0]
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_replace_request_structure(self):
        """Test the structure of replaceAllText request."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                await edit_text("doc123", "find this", "replace with this", match_case=False)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                replace_request = requests[0]["replaceAllText"]

                assert replace_request["containsText"]["text"] == "find this"
                assert replace_request["containsText"]["matchCase"] is False
                assert replace_request["replaceText"] == "replace with this"
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_match_case_parameter(self):
        """Test that match_case parameter is passed correctly."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            for match_case in [True, False]:
                mock_service.reset_mock()

                with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                    await edit_text("doc123", "text", "replacement", match_case=match_case)

                    call_args = mock_service.documents.return_value.batchUpdate.call_args
                    requests = call_args.kwargs["body"]["requests"]
                    actual_match_case = requests[0]["replaceAllText"]["containsText"]["matchCase"]
                    assert actual_match_case is match_case
        finally:
            auth_token_context.reset(token)


class TestEditTextDeleteOperation:
    """Tests for text deletion operation (replace with empty string)."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_delete_by_replacing_with_empty_string(self):
        """Test that deletion is achieved by replacing with empty string."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                await edit_text("doc123", "text to delete", "")

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]
                replace_request = requests[0]["replaceAllText"]

                assert replace_request["containsText"]["text"] == "text to delete"
                assert replace_request["replaceText"] == ""
        finally:
            auth_token_context.reset(token)


class TestEditTextAppendOperation:
    """Tests for append to end operation."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_append_to_end_uses_insert_text(self):
        """Test that append_to_end uses insertText API."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service), \
                 patch('tools.edit_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {"content": [{"endIndex": 50}]}
                }

                await edit_text("doc123", "", "appended text", append_to_end=True)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                assert len(requests) == 1
                assert "insertText" in requests[0]
                assert requests[0]["insertText"]["text"] == "appended text"
                # Should insert at endIndex - 1 = 49
                assert requests[0]["insertText"]["location"]["index"] == 49
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_append_to_end_requires_empty_old_text(self):
        """Test that append_to_end with non-empty old_text still does replace."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 1}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                # append_to_end is True but old_text is not empty
                await edit_text("doc123", "some text", "new text", append_to_end=True)

                call_args = mock_service.documents.return_value.batchUpdate.call_args
                requests = call_args.kwargs["body"]["requests"]

                # Should use replaceAllText, not insertText
                assert "replaceAllText" in requests[0]
        finally:
            auth_token_context.reset(token)


class TestEditTextResponse:
    """Tests for response handling."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_success_response_for_replace(self):
        """Test success response for replace operation."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 3}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                result = await edit_text("doc123", "old", "new")

                assert result["success"] is True
                assert result["document_id"] == "doc123"
                assert result["operation"] == "replace"
                assert result["replacements_made"] == 3
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_success_response_for_append(self):
        """Test success response for append operation."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {}

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service), \
                 patch('tools.edit_text.get_document_raw', new_callable=AsyncMock) as mock_get_doc:
                mock_get_doc.return_value = {
                    "body": {"content": [{"endIndex": 50}]}
                }

                result = await edit_text("doc123", "", "appended", append_to_end=True)

                assert result["success"] is True
                assert result["document_id"] == "doc123"
                assert result["operation"] == "append"
                assert result["characters_inserted"] == len("appended")
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_failure_response_when_text_not_found(self):
        """Test failure response when old_text is not found."""
        mock_service = MagicMock()
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "replies": [{"replaceAllText": {"occurrencesChanged": 0}}]
        }

        token = auth_token_context.set("test_token")
        try:
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                result = await edit_text("doc123", "nonexistent text", "new")

                assert result["success"] is False
                assert "error" in result
                assert "not found" in result["error"].lower()
        finally:
            auth_token_context.reset(token)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_error_response_when_old_text_empty_without_append(self):
        """Test error response when old_text is empty without append_to_end."""
        token = auth_token_context.set("test_token")
        try:
            result = await edit_text("doc123", "", "new text", append_to_end=False)

            assert result["success"] is False
            assert "error" in result
        finally:
            auth_token_context.reset(token)


class TestEditTextErrors:
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
            with patch('tools.edit_text.get_docs_service', return_value=mock_service):
                with pytest.raises(RuntimeError, match="Google Docs API Error"):
                    await edit_text("doc123", "old", "new")
        finally:
            auth_token_context.reset(token)
