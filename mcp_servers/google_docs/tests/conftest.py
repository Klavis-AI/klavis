"""Shared test fixtures for Google Docs MCP server tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory to path so tests can import from server.py
sys.path.insert(0, str(Path(__file__).parent.parent))

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def mock_docs_service():
    """Create a mock Google Docs service."""
    service = MagicMock()
    service.documents.return_value.get.return_value.execute.return_value = {}
    service.documents.return_value.create.return_value.execute.return_value = {}
    service.documents.return_value.batchUpdate.return_value.execute.return_value = {}
    return service


@pytest.fixture
def mock_drive_service():
    """Create a mock Google Drive service."""
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {"files": []}
    return service


@pytest.fixture
def sample_document():
    """Sample Google Docs API document response."""
    return {
        "documentId": "test_doc_123",
        "title": "Test Document",
        "revisionId": "rev_456",
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
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"}
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_document_with_formatting():
    """Sample document with various formatting."""
    return {
        "documentId": "formatted_doc_123",
        "title": "Formatted Document",
        "revisionId": "rev_789",
        "body": {
            "content": [
                {
                    "startIndex": 1,
                    "endIndex": 15,
                    "paragraph": {
                        "elements": [
                            {
                                "startIndex": 1,
                                "endIndex": 5,
                                "textRun": {
                                    "content": "Bold",
                                    "textStyle": {"bold": True}
                                }
                            },
                            {
                                "startIndex": 5,
                                "endIndex": 6,
                                "textRun": {
                                    "content": " ",
                                    "textStyle": {}
                                }
                            },
                            {
                                "startIndex": 6,
                                "endIndex": 12,
                                "textRun": {
                                    "content": "Italic",
                                    "textStyle": {"italic": True}
                                }
                            }
                        ],
                        "paragraphStyle": {"namedStyleType": "HEADING_1"}
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_files_list():
    """Sample Google Drive files list response."""
    return {
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
