"""
Core functionality for the Word Document Server.

This package contains the core functionality modules used by the Word Document Server.
"""

from word_document_server.core.styles import ensure_heading_style, ensure_table_style, create_style
from word_document_server.core.protection import add_protection_info, verify_document_protection, is_section_editable, create_signature_info, verify_signature
from word_document_server.core.footnotes import add_footnote, add_endnote, convert_footnotes_to_endnotes, find_footnote_references, get_format_symbols, customize_footnote_formatting
from word_document_server.core.tables import set_cell_border, apply_table_style, copy_table
