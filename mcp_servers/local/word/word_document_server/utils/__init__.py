"""
Utility functions for the Word Document Server.

This package contains utility modules for file operations and document handling.
"""

from word_document_server.utils.file_utils import check_file_writeable, create_document_copy, ensure_docx_extension
from word_document_server.utils.document_utils import get_document_properties, extract_document_text, get_document_structure, find_paragraph_by_text, find_and_replace_text
