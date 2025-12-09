"""
Main entry point for the Word Document MCP Server.
Acts as the central controller for the MCP server that handles Word document operations.
Supports multiple transports: stdio, sse, and streamable-http using standalone FastMCP.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
print("Loading configuration from .env file...")
load_dotenv()
# Set required environment variable for FastMCP 2.8.1+
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')
from fastmcp import FastMCP
from word_document_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    protection_tools,
    footnote_tools,
    extended_document_tools,
    comment_tools
)
from word_document_server.tools.content_tools import replace_paragraph_block_below_header_tool
from word_document_server.tools.content_tools import replace_block_between_manual_anchors_tool

def get_transport_config():
    """
    Get transport configuration from environment variables.
    
    Returns:
        dict: Transport configuration with type, host, port, and other settings
    """
    # Default configuration
    config = {
        'transport': 'stdio',  # Default to stdio for backward compatibility
        'host': '0.0.0.0',
        'port': 8000,
        'path': '/mcp',
        'sse_path': '/sse'
    }
    
    # Override with environment variables if provided
    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()
    print(f"Transport: {transport}")
    # Validate transport type
    valid_transports = ['stdio', 'streamable-http', 'sse']
    if transport not in valid_transports:
        print(f"Warning: Invalid transport '{transport}'. Falling back to 'stdio'.")
        transport = 'stdio'
    
    config['transport'] = transport
    config['host'] = os.getenv('MCP_HOST', config['host'])
    # Use PORT from Render if available, otherwise fall back to MCP_PORT or default
    config['port'] = int(os.getenv('PORT', os.getenv('MCP_PORT', config['port'])))
    config['path'] = os.getenv('MCP_PATH', config['path'])
    config['sse_path'] = os.getenv('MCP_SSE_PATH', config['sse_path'])
    
    return config


def setup_logging(debug_mode):
    """
    Setup logging based on debug mode.
    
    Args:
        debug_mode (bool): Whether to enable debug logging
    """
    import logging
    
    if debug_mode:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        print("Debug logging enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )


# Initialize FastMCP server
mcp = FastMCP("Word Document Server")


def register_tools():
    """Register all tools with the MCP server using FastMCP decorators."""
    
    # Document tools (create, copy, info, etc.)
    @mcp.tool()
    def create_document(filename: str, title: str = None, author: str = None):
        """Create a new Word document with optional metadata."""
        return document_tools.create_document(filename, title, author)
    
    @mcp.tool()
    def copy_document(source_filename: str, destination_filename: str = None):
        """Create a copy of a Word document."""
        return document_tools.copy_document(source_filename, destination_filename)
    
    @mcp.tool()
    def get_document_info(filename: str):
        """Get information about a Word document."""
        return document_tools.get_document_info(filename)
    
    @mcp.tool()
    def get_document_text(filename: str):
        """Extract all text from a Word document."""
        return document_tools.get_document_text(filename)
    
    @mcp.tool()
    def get_document_outline(filename: str):
        """Get the structure of a Word document."""
        return document_tools.get_document_outline(filename)
    
    @mcp.tool()
    def list_available_documents(directory: str = "."):
        """List all .docx files in the specified directory."""
        return document_tools.list_available_documents(directory)
    
    @mcp.tool()
    def get_document_xml(filename: str):
        """Get the raw XML structure of a Word document."""
        return document_tools.get_document_xml_tool(filename)
    
    @mcp.tool()
    def insert_header_near_text(filename: str, target_text: str = None, header_title: str = None, position: str = 'after', header_style: str = 'Heading 1', target_paragraph_index: int = None):
        """Insert a header (with specified style) before or after the target paragraph. Specify by text or paragraph index. Args: filename (str), target_text (str, optional), header_title (str), position ('before' or 'after'), header_style (str, default 'Heading 1'), target_paragraph_index (int, optional)."""
        return content_tools.insert_header_near_text_tool(filename, target_text, header_title, position, header_style, target_paragraph_index)
    
    @mcp.tool()
    def insert_line_or_paragraph_near_text(filename: str, target_text: str = None, line_text: str = None, position: str = 'after', line_style: str = None, target_paragraph_index: int = None):
        """
        Insert a new line or paragraph (with specified or matched style) before or after the target paragraph. Specify by text or paragraph index. Args: filename (str), target_text (str, optional), line_text (str), position ('before' or 'after'), line_style (str, optional), target_paragraph_index (int, optional).
        """
        return content_tools.insert_line_or_paragraph_near_text_tool(filename, target_text, line_text, position, line_style, target_paragraph_index)
    
    @mcp.tool()
    def insert_numbered_list_near_text(filename: str, target_text: str = None, list_items: list = None, position: str = 'after', target_paragraph_index: int = None, bullet_type: str = 'bullet'):
        """Insert a bulleted or numbered list before or after the target paragraph. Specify by text or paragraph index. Args: filename (str), target_text (str, optional), list_items (list of str), position ('before' or 'after'), target_paragraph_index (int, optional), bullet_type ('bullet' for bullets or 'number' for numbered lists, default: 'bullet')."""
        return content_tools.insert_numbered_list_near_text_tool(filename, target_text, list_items, position, target_paragraph_index, bullet_type)
    # Content tools (paragraphs, headings, tables, etc.)
    @mcp.tool()
    def add_paragraph(filename: str, text: str, style: str = None,
                      font_name: str = None, font_size: int = None,
                      bold: bool = None, italic: bool = None, color: str = None):
        """Add a paragraph to a Word document with optional formatting.

        Args:
            filename: Path to Word document
            text: Paragraph text content
            style: Optional paragraph style name
            font_name: Font family (e.g., 'Helvetica', 'Times New Roman')
            font_size: Font size in points (e.g., 14, 36)
            bold: Make text bold
            italic: Make text italic
            color: Text color as hex RGB (e.g., '000000')
        """
        return content_tools.add_paragraph(filename, text, style, font_name, font_size, bold, italic, color)
    
    @mcp.tool()
    def add_heading(filename: str, text: str, level: int = 1,
                    font_name: str = None, font_size: int = None,
                    bold: bool = None, italic: bool = None, border_bottom: bool = False):
        """Add a heading to a Word document with optional formatting.

        Args:
            filename: Path to Word document
            text: Heading text
            level: Heading level (1-9)
            font_name: Font family (e.g., 'Helvetica')
            font_size: Font size in points (e.g., 14)
            bold: Make heading bold
            italic: Make heading italic
            border_bottom: Add bottom border (for section headers)
        """
        return content_tools.add_heading(filename, text, level, font_name, font_size, bold, italic, border_bottom)
    
    @mcp.tool()
    def add_picture(filename: str, image_path: str, width: float = None):
        """Add an image to a Word document."""
        return content_tools.add_picture(filename, image_path, width)
    
    @mcp.tool()
    def add_table(filename: str, rows: int, cols: int, data: list = None):
        """Add a table to a Word document."""
        return content_tools.add_table(filename, rows, cols, data)
    
    @mcp.tool()
    def add_page_break(filename: str):
        """Add a page break to the document."""
        return content_tools.add_page_break(filename)
    
    @mcp.tool()
    def delete_paragraph(filename: str, paragraph_index: int):
        """Delete a paragraph from a document."""
        return content_tools.delete_paragraph(filename, paragraph_index)
    
    @mcp.tool()
    def search_and_replace(filename: str, find_text: str, replace_text: str):
        """Search for text and replace all occurrences."""
        return content_tools.search_and_replace(filename, find_text, replace_text)
    
    # Format tools (styling, text formatting, etc.)
    @mcp.tool()
    def create_custom_style(filename: str, style_name: str, bold: bool = None, 
                          italic: bool = None, font_size: int = None, 
                          font_name: str = None, color: str = None, 
                          base_style: str = None):
        """Create a custom style in the document."""
        return format_tools.create_custom_style(
            filename, style_name, bold, italic, font_size, font_name, color, base_style
        )
    
    @mcp.tool()
    def format_text(filename: str, paragraph_index: int, start_pos: int, end_pos: int,
                   bold: bool = None, italic: bool = None, underline: bool = None,
                   color: str = None, font_size: int = None, font_name: str = None):
        """Format a specific range of text within a paragraph."""
        return format_tools.format_text(
            filename, paragraph_index, start_pos, end_pos, bold, italic, 
            underline, color, font_size, font_name
        )
    
    @mcp.tool()
    def format_table(filename: str, table_index: int, has_header_row: bool = None,
                    border_style: str = None, shading: list = None):
        """Format a table with borders, shading, and structure."""
        return format_tools.format_table(filename, table_index, has_header_row, border_style, shading)
    
    # New table cell shading tools
    @mcp.tool()
    def set_table_cell_shading(filename: str, table_index: int, row_index: int, 
                              col_index: int, fill_color: str, pattern: str = "clear"):
        """Apply shading/filling to a specific table cell."""
        return format_tools.set_table_cell_shading(filename, table_index, row_index, col_index, fill_color, pattern)
    
    @mcp.tool()
    def apply_table_alternating_rows(filename: str, table_index: int, 
                                   color1: str = "FFFFFF", color2: str = "F2F2F2"):
        """Apply alternating row colors to a table for better readability."""
        return format_tools.apply_table_alternating_rows(filename, table_index, color1, color2)
    
    @mcp.tool()
    def highlight_table_header(filename: str, table_index: int, 
                             header_color: str = "4472C4", text_color: str = "FFFFFF"):
        """Apply special highlighting to table header row."""
        return format_tools.highlight_table_header(filename, table_index, header_color, text_color)
    
    # Cell merging tools
    @mcp.tool()
    def merge_table_cells(filename: str, table_index: int, start_row: int, start_col: int, 
                        end_row: int, end_col: int):
        """Merge cells in a rectangular area of a table."""
        return format_tools.merge_table_cells(filename, table_index, start_row, start_col, end_row, end_col)
    
    @mcp.tool()
    def merge_table_cells_horizontal(filename: str, table_index: int, row_index: int, 
                                   start_col: int, end_col: int):
        """Merge cells horizontally in a single row."""
        return format_tools.merge_table_cells_horizontal(filename, table_index, row_index, start_col, end_col)
    
    @mcp.tool()
    def merge_table_cells_vertical(filename: str, table_index: int, col_index: int, 
                                 start_row: int, end_row: int):
        """Merge cells vertically in a single column."""
        return format_tools.merge_table_cells_vertical(filename, table_index, col_index, start_row, end_row)
    
    # Cell alignment tools
    @mcp.tool()
    def set_table_cell_alignment(filename: str, table_index: int, row_index: int, col_index: int,
                               horizontal: str = "left", vertical: str = "top"):
        """Set text alignment for a specific table cell."""
        return format_tools.set_table_cell_alignment(filename, table_index, row_index, col_index, horizontal, vertical)
    
    @mcp.tool()
    def set_table_alignment_all(filename: str, table_index: int, 
                              horizontal: str = "left", vertical: str = "top"):
        """Set text alignment for all cells in a table."""
        return format_tools.set_table_alignment_all(filename, table_index, horizontal, vertical)
    
    # Protection tools
    @mcp.tool()
    def protect_document(filename: str, password: str):
        """Add password protection to a Word document."""
        return protection_tools.protect_document(filename, password)
    
    @mcp.tool()
    def unprotect_document(filename: str, password: str):
        """Remove password protection from a Word document."""
        return protection_tools.unprotect_document(filename, password)
    
    # Footnote tools
    @mcp.tool()
    def add_footnote_to_document(filename: str, paragraph_index: int, footnote_text: str):
        """Add a footnote to a specific paragraph in a Word document."""
        return footnote_tools.add_footnote_to_document(filename, paragraph_index, footnote_text)
    
    @mcp.tool()
    def add_footnote_after_text(filename: str, search_text: str, footnote_text: str, 
                               output_filename: str = None):
        """Add a footnote after specific text with proper superscript formatting.
        This enhanced function ensures footnotes display correctly as superscript."""
        return footnote_tools.add_footnote_after_text(filename, search_text, footnote_text, output_filename)
    
    @mcp.tool()
    def add_footnote_before_text(filename: str, search_text: str, footnote_text: str, 
                                output_filename: str = None):
        """Add a footnote before specific text with proper superscript formatting.
        This enhanced function ensures footnotes display correctly as superscript."""
        return footnote_tools.add_footnote_before_text(filename, search_text, footnote_text, output_filename)
    
    @mcp.tool()
    def add_footnote_enhanced(filename: str, paragraph_index: int, footnote_text: str,
                             output_filename: str = None):
        """Enhanced footnote addition with guaranteed superscript formatting.
        Adds footnote at the end of a specific paragraph with proper style handling."""
        return footnote_tools.add_footnote_enhanced(filename, paragraph_index, footnote_text, output_filename)
    
    @mcp.tool()
    def add_endnote_to_document(filename: str, paragraph_index: int, endnote_text: str):
        """Add an endnote to a specific paragraph in a Word document."""
        return footnote_tools.add_endnote_to_document(filename, paragraph_index, endnote_text)
    
    @mcp.tool()
    def customize_footnote_style(filename: str, numbering_format: str = "1, 2, 3",
                                start_number: int = 1, font_name: str = None,
                                font_size: int = None):
        """Customize footnote numbering and formatting in a Word document."""
        return footnote_tools.customize_footnote_style(
            filename, numbering_format, start_number, font_name, font_size
        )
    
    @mcp.tool()
    def delete_footnote_from_document(filename: str, footnote_id: int = None,
                                     search_text: str = None, output_filename: str = None):
        """Delete a footnote from a Word document.
        Identify the footnote either by ID (1, 2, 3, etc.) or by searching for text near it."""
        return footnote_tools.delete_footnote_from_document(
            filename, footnote_id, search_text, output_filename
        )
    
    # Robust footnote tools - Production-ready with comprehensive validation
    @mcp.tool()
    def add_footnote_robust(filename: str, search_text: str = None, 
                           paragraph_index: int = None, footnote_text: str = "",
                           validate_location: bool = True, auto_repair: bool = False):
        """Add footnote with robust validation and Word compliance.
        This is the production-ready version with comprehensive error handling."""
        return footnote_tools.add_footnote_robust_tool(
            filename, search_text, paragraph_index, footnote_text, 
            validate_location, auto_repair
        )
    
    @mcp.tool()
    def validate_document_footnotes(filename: str):
        """Validate all footnotes in document for coherence and compliance.
        Returns detailed report on ID conflicts, orphaned content, missing styles, etc."""
        return footnote_tools.validate_footnotes_tool(filename)
    
    @mcp.tool()
    def delete_footnote_robust(filename: str, footnote_id: int = None,
                              search_text: str = None, clean_orphans: bool = True):
        """Delete footnote with comprehensive cleanup and orphan removal.
        Ensures complete removal from document.xml, footnotes.xml, and relationships."""
        return footnote_tools.delete_footnote_robust_tool(
            filename, footnote_id, search_text, clean_orphans
        )
    
    # Extended document tools
    @mcp.tool()
    def get_paragraph_text_from_document(filename: str, paragraph_index: int):
        """Get text from a specific paragraph in a Word document."""
        return extended_document_tools.get_paragraph_text_from_document(filename, paragraph_index)
    
    @mcp.tool()
    def find_text_in_document(filename: str, text_to_find: str, match_case: bool = True,
                             whole_word: bool = False):
        """Find occurrences of specific text in a Word document."""
        return extended_document_tools.find_text_in_document(
            filename, text_to_find, match_case, whole_word
        )
    
    @mcp.tool()
    def convert_to_pdf(filename: str, output_filename: str = None):
        """Convert a Word document to PDF format."""
        return extended_document_tools.convert_to_pdf(filename, output_filename)

    @mcp.tool()
    def replace_paragraph_block_below_header(filename: str, header_text: str, new_paragraphs: list, detect_block_end_fn=None):
        """Reemplaza el bloque de párrafos debajo de un encabezado, evitando modificar TOC."""
        return replace_paragraph_block_below_header_tool(filename, header_text, new_paragraphs, detect_block_end_fn)

    @mcp.tool()
    def replace_block_between_manual_anchors(filename: str, start_anchor_text: str, new_paragraphs: list, end_anchor_text: str = None, match_fn=None, new_paragraph_style: str = None):
        """Replace all content between start_anchor_text and end_anchor_text (or next logical header if not provided)."""
        return replace_block_between_manual_anchors_tool(filename, start_anchor_text, new_paragraphs, end_anchor_text, match_fn, new_paragraph_style)

    # Comment tools
    @mcp.tool()
    def get_all_comments(filename: str):
        """Extract all comments from a Word document."""
        return comment_tools.get_all_comments(filename)
    
    @mcp.tool()
    def get_comments_by_author(filename: str, author: str):
        """Extract comments from a specific author in a Word document."""
        return comment_tools.get_comments_by_author(filename, author)
    
    @mcp.tool()
    def get_comments_for_paragraph(filename: str, paragraph_index: int):
        """Extract comments for a specific paragraph in a Word document."""
        return comment_tools.get_comments_for_paragraph(filename, paragraph_index)
    # New table column width tools
    @mcp.tool()
    def set_table_column_width(filename: str, table_index: int, col_index: int, 
                              width: float, width_type: str = "points"):
        """Set the width of a specific table column."""
        return format_tools.set_table_column_width(filename, table_index, col_index, width, width_type)

    @mcp.tool()
    def set_table_column_widths(filename: str, table_index: int, widths: list, 
                               width_type: str = "points"):
        """Set the widths of multiple table columns."""
        return format_tools.set_table_column_widths(filename, table_index, widths, width_type)

    @mcp.tool()
    def set_table_width(filename: str, table_index: int, width: float, 
                       width_type: str = "points"):
        """Set the overall width of a table."""
        return format_tools.set_table_width(filename, table_index, width, width_type)

    @mcp.tool()
    def auto_fit_table_columns(filename: str, table_index: int):
        """Set table columns to auto-fit based on content."""
        return format_tools.auto_fit_table_columns(filename, table_index)

    # New table cell text formatting and padding tools
    @mcp.tool()
    def format_table_cell_text(filename: str, table_index: int, row_index: int, col_index: int,
                               text_content: str = None, bold: bool = None, italic: bool = None,
                               underline: bool = None, color: str = None, font_size: int = None,
                               font_name: str = None):
        """Format text within a specific table cell."""
        return format_tools.format_table_cell_text(filename, table_index, row_index, col_index,
                                                   text_content, bold, italic, underline, color, font_size, font_name)

    @mcp.tool()
    def set_table_cell_padding(filename: str, table_index: int, row_index: int, col_index: int,
                               top: float = None, bottom: float = None, left: float = None, 
                               right: float = None, unit: str = "points"):
        """Set padding/margins for a specific table cell."""
        return format_tools.set_table_cell_padding(filename, table_index, row_index, col_index,
                                                   top, bottom, left, right, unit)



def run_server():
    """Run the Word Document MCP Server with configurable transport."""
    # Get transport configuration
    config = get_transport_config()
    
    # Setup logging
    # setup_logging(config['debug'])
    
    # Register all tools
    register_tools()
    
    # Print startup information
    transport_type = config['transport']
    print(f"Starting Word Document MCP Server with {transport_type} transport...")
    
    # if config['debug']:
    #     print(f"Configuration: {config}")
    
    try:
        if transport_type == 'stdio':
            # Run with stdio transport (default, backward compatible)
            print("Server running on stdio transport")
            mcp.run(transport='stdio')
            
        elif transport_type == 'streamable-http':
            # Run with streamable HTTP transport
            print(f"Server running on streamable-http transport at http://{config['host']}:{config['port']}{config['path']}")
            mcp.run(
                transport='streamable-http',
                host=config['host'],
                port=config['port'],
                path=config['path']
            )
            
        elif transport_type == 'sse':
            # Run with SSE transport
            print(f"Server running on SSE transport at http://{config['host']}:{config['port']}{config['sse_path']}")
            mcp.run(
                transport='sse',
                host=config['host'],
                port=config['port'],
                path=config['sse_path']
            )
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        if config['debug']:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    return mcp


def main():
    """Main entry point for the server."""
    run_server()


if __name__ == "__main__":
    main()
