"""Unit tests for the Google Docs MCP server."""

import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


class TestExtractAccessToken:
    """Tests for the extract_access_token function."""

    def test_extract_from_env_variable(self):
        """Test extracting access token from AUTH_DATA environment variable."""
        from server import extract_access_token

        auth_data = json.dumps({"access_token": "env_token_123"})
        with patch.dict(os.environ, {"AUTH_DATA": auth_data}):
            result = extract_access_token(None)
            assert result == "env_token_123"

    def test_returns_empty_string_when_no_auth_data(self):
        """Test that empty string is returned when no auth data is present."""
        from server import extract_access_token

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AUTH_DATA", None)
            result = extract_access_token({})
            assert result == ""

    def test_returns_empty_string_on_invalid_json(self):
        """Test that empty string is returned when auth data is invalid JSON."""
        from server import extract_access_token

        with patch.dict(os.environ, {"AUTH_DATA": "not valid json"}):
            result = extract_access_token(None)
            assert result == ""

    def test_returns_empty_string_when_access_token_missing(self):
        """Test that empty string is returned when access_token key is missing."""
        from server import extract_access_token

        auth_data = json.dumps({"other_field": "value"})
        with patch.dict(os.environ, {"AUTH_DATA": auth_data}):
            result = extract_access_token(None)
            assert result == ""


class TestNormalizeDocumentResponse:
    """Tests for the normalize_document_response function."""

    def test_basic_document_normalization(self):
        """Test normalizing a basic document response."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {"content": []}
        }

        result = normalize_document_response(raw_response)

        assert result["documentId"] == "doc123"
        assert result["title"] == "Test Document"
        assert result["revisionId"] == "rev456"
        assert result["content"] == []

    def test_paragraph_extraction(self):
        """Test extracting paragraph content from document."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Hello World",
                                        "textStyle": {}
                                    }
                                }
                            ],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["text"] == "Hello World"

    def test_formatted_text_extraction(self):
        """Test extracting formatted text (bold)."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {
                                    "textRun": {
                                        "content": "Bold text",
                                        "textStyle": {"bold": True}
                                    }
                                }
                            ],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert "formattedParts" in result["content"][0]
        assert result["content"][0]["formattedParts"][0]["bold"] is True

    def test_heading_style_extraction(self):
        """Test extracting heading styles from paragraphs."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Heading", "textStyle": {}}}
                            ],
                            "paragraphStyle": {
                                "namedStyleType": "HEADING_1",
                                "headingId": "h.abc123"
                            }
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert result["content"][0]["style"] == "HEADING_1"
        assert result["content"][0]["headingId"] == "h.abc123"

    def test_bullet_list_extraction(self):
        """Test extracting bullet list items."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "List item", "textStyle": {}}}
                            ],
                            "paragraphStyle": {},
                            "bullet": {"listId": "list123", "nestingLevel": 1}
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert result["content"][0]["isBullet"] is True
        assert result["content"][0]["listId"] == "list123"
        assert result["content"][0]["nestingLevel"] == 1

    def test_table_extraction(self):
        """Test extracting table content."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "table": {
                            "rows": 2,
                            "columns": 2,
                            "tableRows": [
                                {
                                    "tableCells": [
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "elements": [{"textRun": {"content": "Cell 1", "textStyle": {}}}],
                                                        "paragraphStyle": {}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "content": [
                                                {
                                                    "paragraph": {
                                                        "elements": [{"textRun": {"content": "Cell 2", "textStyle": {}}}],
                                                        "paragraphStyle": {}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert result["content"][0]["type"] == "table"
        assert result["content"][0]["rows"] == 2
        assert result["content"][0]["columns"] == 2
        assert result["content"][0]["data"][0] == ["Cell 1", "Cell 2"]

    def test_empty_paragraphs_are_skipped(self):
        """Test that empty paragraphs are not included."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "   \n", "textStyle": {}}}],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert len(result["content"]) == 0

    def test_section_breaks_are_skipped(self):
        """Test that section breaks are skipped in content."""
        from server import normalize_document_response

        raw_response = {
            "documentId": "doc123",
            "title": "Test Document",
            "revisionId": "rev456",
            "body": {
                "content": [
                    {"sectionBreak": {}},
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Text", "textStyle": {}}}],
                            "paragraphStyle": {}
                        }
                    }
                ]
            }
        }

        result = normalize_document_response(raw_response)

        assert len(result["content"]) == 1
        assert result["content"][0]["text"] == "Text"


class TestGetAuthToken:
    """Tests for the get_auth_token function."""

    def test_get_auth_token_from_context(self):
        """Test retrieving auth token from context."""
        from server import get_auth_token, auth_token_context

        token = auth_token_context.set("test_token_123")
        try:
            result = get_auth_token()
            assert result == "test_token_123"
        finally:
            auth_token_context.reset(token)

    def test_get_auth_token_raises_when_not_set(self):
        """Test that RuntimeError is raised when token not in context."""
        from server import get_auth_token

        with pytest.raises(RuntimeError, match="Authentication token not found"):
            get_auth_token()


class TestCreateDocumentFromText:
    """Tests for the create_document_from_text function."""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_create_document_from_text_uses_correct_id_key(self):
        """Test that create_document_from_text correctly uses 'id' from create_blank_document."""
        from server import create_document_from_text, auth_token_context

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

                result = await create_document_from_text("Test Doc", "Hello world")

                # Verify batchUpdate was called with the correct document ID
                mock_service.documents.return_value.batchUpdate.assert_called_once_with(
                    documentId="doc123",
                    body={"requests": [{"insertText": {"location": {"index": 1}, "text": "Hello world"}}]}
                )

                assert result["id"] == "doc123"
                assert result["title"] == "Test Doc"
        finally:
            auth_token_context.reset(token)
