"""Google Docs MCP Server Tools."""

from .base import (
    auth_token_context,
    get_auth_token,
    get_docs_service,
    get_drive_service,
    extract_access_token,
)
from .converters import (
    extract_text_from_document,
    get_paragraph_heading_type,
    convert_document_to_markdown,
    convert_document_to_structured,
    format_document_response,
    normalize_document_response,
    hex_to_rgb,
)
from .markdown_parser import (
    parse_markdown_text,
    parse_inline_formatting,
)
from .get_document_by_id import get_document_by_id, _get_document_raw
from .get_all_documents import get_all_documents
from .insert_text_at_end import insert_text_at_end
from .create_blank_document import create_blank_document
from .create_document_from_text import create_document_from_text
from .edit_text import edit_text
from .apply_style import apply_style
from .insert_formatted_text import insert_formatted_text

__all__ = [
    # Base utilities
    "auth_token_context",
    "get_auth_token",
    "get_docs_service",
    "get_drive_service",
    "extract_access_token",
    # Converters
    "extract_text_from_document",
    "get_paragraph_heading_type",
    "convert_document_to_markdown",
    "convert_document_to_structured",
    "format_document_response",
    "normalize_document_response",
    "hex_to_rgb",
    # Markdown parser
    "parse_markdown_text",
    "parse_inline_formatting",
    # Tools
    "get_document_by_id",
    "_get_document_raw",
    "get_all_documents",
    "insert_text_at_end",
    "create_blank_document",
    "create_document_from_text",
    "edit_text",
    "apply_style",
    "insert_formatted_text",
]
