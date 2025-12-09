import contextlib
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from pathlib import Path
import tempfile
import json

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_WORKSPACE_PATH = os.getenv("WORKSPACE_PATH", os.getcwd())
DEFAULT_TEMPFILE_DIR = os.getenv("TEMPFILE_DIR", os.path.join(DEFAULT_WORKSPACE_PATH, ".pdf_tools_tempfiles"))


def ensure_workspace_path(workspace_path: str, file_path: str) -> Path:
    """
    Ensures the file path is within the workspace directory.
    Returns the absolute path.
    """
    workspace = Path(workspace_path).resolve()
    target = (workspace / file_path).resolve()
    
    # Security check: ensure target is within workspace
    try:
        target.relative_to(workspace)
    except ValueError:
        raise ValueError(f"Access denied: {file_path} is outside workspace directory")
    
    return target


async def read_pdf(workspace_path: str, file_path: str) -> Dict[str, Any]:
    """
    Read and extract text content from a PDF file.
    
    Args:
        workspace_path: The workspace directory path
        file_path: Relative path to the PDF file within workspace
        
    Returns:
        Dictionary containing PDF metadata and text content
    """
    logger.info(f"Reading PDF: {file_path}")
    
    try:
        pdf_path = ensure_workspace_path(workspace_path, file_path)
        
        if not pdf_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        reader = PdfReader(str(pdf_path))
        
        # Extract metadata
        metadata = {}
        if reader.metadata:
            metadata = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "producer": reader.metadata.get("/Producer", ""),
                "creation_date": str(reader.metadata.get("/CreationDate", "")),
            }
        
        # Extract text from all pages
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            pages_text.append({
                "page_number": i + 1,
                "text": text
            })
        
        return {
            "file_path": file_path,
            "num_pages": len(reader.pages),
            "metadata": metadata,
            "pages": pages_text
        }
        
    except PdfReadError as e:
        logger.exception(f"Error reading PDF: {e}")
        return {"error": f"Failed to read PDF: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error reading PDF: {e}")
        return {"error": f"Unexpected error: {str(e)}"}


async def extract_pages(
    workspace_path: str,
    tempfile_dir: str,
    input_file: str,
    output_file: str,
    page_numbers: List[int]
) -> Dict[str, Any]:
    """
    Extract specific pages from a PDF and create a new PDF.
    
    Args:
        workspace_path: The workspace directory path
        tempfile_dir: Directory for temporary files
        input_file: Path to input PDF
        output_file: Path to output PDF (will be created)
        page_numbers: List of page numbers to extract (1-indexed)
        
    Returns:
        Dictionary with operation result
    """
    logger.info(f"Extracting pages {page_numbers} from {input_file} to {output_file}")
    
    try:
        input_path = ensure_workspace_path(workspace_path, input_file)
        output_path = ensure_workspace_path(workspace_path, output_file)
        
        if not input_path.exists():
            return {"error": f"Input file not found: {input_file}"}
        
        reader = PdfReader(str(input_path))
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        
        # Validate page numbers
        for page_num in page_numbers:
            if page_num < 1 or page_num > total_pages:
                return {"error": f"Invalid page number {page_num}. PDF has {total_pages} pages."}
            writer.add_page(reader.pages[page_num - 1])
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as output:
            writer.write(output)
        
        return {
            "success": True,
            "output_file": output_file,
            "pages_extracted": len(page_numbers),
            "message": f"Successfully extracted {len(page_numbers)} pages to {output_file}"
        }
        
    except Exception as e:
        logger.exception(f"Error extracting pages: {e}")
        return {"error": f"Failed to extract pages: {str(e)}"}


async def merge_pdfs(
    workspace_path: str,
    tempfile_dir: str,
    input_files: List[str],
    output_file: str
) -> Dict[str, Any]:
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        workspace_path: The workspace directory path
        tempfile_dir: Directory for temporary files
        input_files: List of input PDF file paths
        output_file: Path to output merged PDF
        
    Returns:
        Dictionary with operation result
    """
    logger.info(f"Merging {len(input_files)} PDFs into {output_file}")
    
    try:
        output_path = ensure_workspace_path(workspace_path, output_file)
        writer = PdfWriter()
        
        total_pages = 0
        for input_file in input_files:
            input_path = ensure_workspace_path(workspace_path, input_file)
            
            if not input_path.exists():
                return {"error": f"Input file not found: {input_file}"}
            
            reader = PdfReader(str(input_path))
            for page in reader.pages:
                writer.add_page(page)
            total_pages += len(reader.pages)
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as output:
            writer.write(output)
        
        return {
            "success": True,
            "output_file": output_file,
            "input_files_count": len(input_files),
            "total_pages": total_pages,
            "message": f"Successfully merged {len(input_files)} PDFs ({total_pages} pages) into {output_file}"
        }
        
    except Exception as e:
        logger.exception(f"Error merging PDFs: {e}")
        return {"error": f"Failed to merge PDFs: {str(e)}"}


async def split_pdf(
    workspace_path: str,
    tempfile_dir: str,
    input_file: str,
    output_prefix: str
) -> Dict[str, Any]:
    """
    Split a PDF into individual pages.
    
    Args:
        workspace_path: The workspace directory path
        tempfile_dir: Directory for temporary files
        input_file: Path to input PDF
        output_prefix: Prefix for output files (e.g., "page" -> "page_1.pdf", "page_2.pdf")
        
    Returns:
        Dictionary with operation result
    """
    logger.info(f"Splitting {input_file} with prefix {output_prefix}")
    
    try:
        input_path = ensure_workspace_path(workspace_path, input_file)
        
        if not input_path.exists():
            return {"error": f"Input file not found: {input_file}"}
        
        reader = PdfReader(str(input_path))
        output_files = []
        
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            output_file = f"{output_prefix}_{i + 1}.pdf"
            output_path = ensure_workspace_path(workspace_path, output_file)
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as output:
                writer.write(output)
            
            output_files.append(output_file)
        
        return {
            "success": True,
            "output_files": output_files,
            "pages_created": len(output_files),
            "message": f"Successfully split PDF into {len(output_files)} pages"
        }
        
    except Exception as e:
        logger.exception(f"Error splitting PDF: {e}")
        return {"error": f"Failed to split PDF: {str(e)}"}


async def get_pdf_info(workspace_path: str, file_path: str) -> Dict[str, Any]:
    """
    Get information about a PDF file without extracting full text.
    
    Args:
        workspace_path: The workspace directory path
        file_path: Relative path to the PDF file within workspace
        
    Returns:
        Dictionary containing PDF information
    """
    logger.info(f"Getting info for PDF: {file_path}")
    
    try:
        pdf_path = ensure_workspace_path(workspace_path, file_path)
        
        if not pdf_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        reader = PdfReader(str(pdf_path))
        
        # Extract metadata
        metadata = {}
        if reader.metadata:
            metadata = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "producer": reader.metadata.get("/Producer", ""),
                "creation_date": str(reader.metadata.get("/CreationDate", "")),
            }
        
        # Get page sizes
        page_sizes = []
        for i, page in enumerate(reader.pages):
            box = page.mediabox
            page_sizes.append({
                "page": i + 1,
                "width": float(box.width),
                "height": float(box.height)
            })
        
        return {
            "file_path": file_path,
            "num_pages": len(reader.pages),
            "metadata": metadata,
            "page_sizes": page_sizes,
            "is_encrypted": reader.is_encrypted
        }
        
    except Exception as e:
        logger.exception(f"Error getting PDF info: {e}")
        return {"error": f"Failed to get PDF info: {str(e)}"}


@click.command()
@click.option(
    "--workspace_path",
    default=DEFAULT_WORKSPACE_PATH,
    help="Path to the workspace directory where PDFs are located"
)
@click.option(
    "--tempfile_dir",
    default=DEFAULT_TEMPFILE_DIR,
    help="Directory for temporary file storage"
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(
    workspace_path: str,
    tempfile_dir: str,
    log_level: str,
) -> int:
    """PDF Tools MCP Server - Local PDF manipulation and extraction."""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Ensure directories exist
    Path(workspace_path).mkdir(parents=True, exist_ok=True)
    Path(tempfile_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting PDF Tools MCP Server")
    logger.info(f"Workspace path: {workspace_path}")
    logger.info(f"Tempfile directory: {tempfile_dir}")
    
    # Create the MCP server instance
    app = Server(
        "pdf-tools-mcp-server",
        instructions="PDF document manipulation and extraction server. Provides tools for reading, analyzing, "
                     "extracting, merging, and splitting PDF files within a workspace directory.",
    )
    
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="read_pdf",
                description="Read and extract text content from a PDF file. Returns metadata and text from all pages.",
                inputSchema={
                    "type": "object",
                    "required": ["file_path"],
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to the PDF file within the workspace directory"
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PDF_READ", "readOnlyHint": True}),
            ),
            types.Tool(
                name="get_pdf_info",
                description="Get metadata and information about a PDF file without extracting full text content.",
                inputSchema={
                    "type": "object",
                    "required": ["file_path"],
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to the PDF file within the workspace directory"
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PDF_INFO", "readOnlyHint": True}),
            ),
            types.Tool(
                name="extract_pages",
                description="Extract specific pages from a PDF and create a new PDF file.",
                inputSchema={
                    "type": "object",
                    "required": ["input_file", "output_file", "page_numbers"],
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Relative path to the input PDF file"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Relative path for the output PDF file"
                        },
                        "page_numbers": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Array of page numbers to extract (1-indexed)"
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PDF_MANIPULATE"}),
            ),
            types.Tool(
                name="merge_pdfs",
                description="Merge multiple PDF files into a single PDF file.",
                inputSchema={
                    "type": "object",
                    "required": ["input_files", "output_file"],
                    "properties": {
                        "input_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of relative paths to input PDF files"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Relative path for the output merged PDF file"
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PDF_MANIPULATE"}),
            ),
            types.Tool(
                name="split_pdf",
                description="Split a PDF file into individual pages, creating one PDF per page.",
                inputSchema={
                    "type": "object",
                    "required": ["input_file", "output_prefix"],
                    "properties": {
                        "input_file": {
                            "type": "string",
                            "description": "Relative path to the input PDF file"
                        },
                        "output_prefix": {
                            "type": "string",
                            "description": "Prefix for output files (e.g., 'page' creates 'page_1.pdf', 'page_2.pdf')"
                        }
                    },
                },
                annotations=types.ToolAnnotations(**{"category": "PDF_MANIPULATE"}),
            ),
        ]
    
    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool calls."""
        
        try:
            result = None
            
            if name == "read_pdf":
                file_path = arguments.get("file_path")
                if not file_path:
                    return [types.TextContent(type="text", text="Error: file_path parameter is required")]
                result = await read_pdf(workspace_path, file_path)
                
            elif name == "get_pdf_info":
                file_path = arguments.get("file_path")
                if not file_path:
                    return [types.TextContent(type="text", text="Error: file_path parameter is required")]
                result = await get_pdf_info(workspace_path, file_path)
                
            elif name == "extract_pages":
                input_file = arguments.get("input_file")
                output_file = arguments.get("output_file")
                page_numbers = arguments.get("page_numbers")
                
                if not all([input_file, output_file, page_numbers]):
                    return [types.TextContent(type="text", text="Error: input_file, output_file, and page_numbers are required")]
                
                result = await extract_pages(workspace_path, tempfile_dir, input_file, output_file, page_numbers)
                
            elif name == "merge_pdfs":
                input_files = arguments.get("input_files")
                output_file = arguments.get("output_file")
                
                if not all([input_files, output_file]):
                    return [types.TextContent(type="text", text="Error: input_files and output_file are required")]
                
                result = await merge_pdfs(workspace_path, tempfile_dir, input_files, output_file)
                
            elif name == "split_pdf":
                input_file = arguments.get("input_file")
                output_prefix = arguments.get("output_prefix")
                
                if not all([input_file, output_prefix]):
                    return [types.TextContent(type="text", text="Error: input_file and output_prefix are required")]
                
                result = await split_pdf(workspace_path, tempfile_dir, input_file, output_prefix)
                
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
            # Return the result as JSON
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    # Use stdio transport for local usage
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            logger.info("PDF Tools MCP Server running on stdio")
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    import asyncio
    asyncio.run(run_server())
    
    return 0


if __name__ == "__main__":
    main()

