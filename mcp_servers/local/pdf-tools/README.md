# PDF Tools MCP Server (Local)

A Model Context Protocol (MCP) server for local PDF document manipulation and extraction. This server provides comprehensive PDF tools for reading, analyzing, extracting, merging, and splitting PDF files.

## Features

### PDF Reading & Analysis
- **read_pdf**: Extract text content from all pages of a PDF with metadata
- **get_pdf_info**: Get PDF metadata and information without full text extraction

### PDF Manipulation
- **extract_pages**: Extract specific pages from a PDF to create a new document
- **merge_pdfs**: Combine multiple PDF files into a single document
- **split_pdf**: Split a PDF into individual page files

## Installation

### Using uvx (Recommended)

```bash
uvx --from . pdf-tools-mcp --workspace_path=/path/to/workspace
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py --workspace_path=/path/to/workspace
```

## Configuration

The server accepts the following command-line options:

- `--workspace_path`: Path to the workspace directory where PDFs are located (default: current directory)
- `--tempfile_dir`: Directory for temporary file storage (default: `{workspace}/.pdf_tools_tempfiles`)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

### Environment Variables

You can also configure using environment variables:

- `WORKSPACE_PATH`: Default workspace path
- `TEMPFILE_DIR`: Default temporary file directory

## Usage with MCP Clients

### Claude Desktop / Cursor Configuration

Add to your MCP configuration file:

```json
{
  "mcpServers": {
    "pdf-tools": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/mcp_servers/local/pdf-tools",
        "pdf-tools-mcp",
        "--workspace_path",
        "${agent_workspace}",
        "--tempfile_dir",
        "${agent_workspace}/.pdf_tools_tempfiles"
      ],
      "client_session_timeout_seconds": 120,
      "cache_tools_list": true
    }
  }
}
```

### Python SDK Example

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py", "--workspace_path", "/path/to/workspace"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])
            
            # Read a PDF
            result = await session.call_tool(
                "read_pdf",
                arguments={"file_path": "document.pdf"}
            )
            print(json.loads(result.content[0].text))

asyncio.run(main())
```

## Available Tools

### read_pdf

Extract text content and metadata from a PDF file.

**Parameters:**
- `file_path` (string, required): Relative path to the PDF file within workspace

**Returns:**
```json
{
  "file_path": "document.pdf",
  "num_pages": 10,
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "subject": "Subject",
    "creator": "Creator",
    "producer": "Producer",
    "creation_date": "2024-01-01"
  },
  "pages": [
    {
      "page_number": 1,
      "text": "Page 1 content..."
    }
  ]
}
```

### get_pdf_info

Get metadata and information about a PDF without extracting full text.

**Parameters:**
- `file_path` (string, required): Relative path to the PDF file

**Returns:**
```json
{
  "file_path": "document.pdf",
  "num_pages": 10,
  "metadata": {...},
  "page_sizes": [
    {"page": 1, "width": 612.0, "height": 792.0}
  ],
  "is_encrypted": false
}
```

### extract_pages

Extract specific pages from a PDF to create a new document.

**Parameters:**
- `input_file` (string, required): Relative path to input PDF
- `output_file` (string, required): Relative path for output PDF
- `page_numbers` (array of integers, required): Page numbers to extract (1-indexed)

**Example:**
```json
{
  "input_file": "document.pdf",
  "output_file": "extracted_pages.pdf",
  "page_numbers": [1, 3, 5]
}
```

**Returns:**
```json
{
  "success": true,
  "output_file": "extracted_pages.pdf",
  "pages_extracted": 3,
  "message": "Successfully extracted 3 pages to extracted_pages.pdf"
}
```

### merge_pdfs

Merge multiple PDF files into a single document.

**Parameters:**
- `input_files` (array of strings, required): Array of relative paths to input PDFs
- `output_file` (string, required): Relative path for output merged PDF

**Example:**
```json
{
  "input_files": ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
  "output_file": "merged.pdf"
}
```

**Returns:**
```json
{
  "success": true,
  "output_file": "merged.pdf",
  "input_files_count": 3,
  "total_pages": 30,
  "message": "Successfully merged 3 PDFs (30 pages) into merged.pdf"
}
```

### split_pdf

Split a PDF into individual page files.

**Parameters:**
- `input_file` (string, required): Relative path to input PDF
- `output_prefix` (string, required): Prefix for output files

**Example:**
```json
{
  "input_file": "document.pdf",
  "output_prefix": "page"
}
```

This creates: `page_1.pdf`, `page_2.pdf`, etc.

**Returns:**
```json
{
  "success": true,
  "output_files": ["page_1.pdf", "page_2.pdf", "page_3.pdf"],
  "pages_created": 3,
  "message": "Successfully split PDF into 3 pages"
}
```

## Security

The server implements security measures to ensure files are only accessed within the configured workspace directory:

- All file paths are validated to be within the workspace
- Path traversal attempts (e.g., `../../../etc/passwd`) are blocked
- Files outside the workspace cannot be accessed

## Error Handling

All tools return error information in a consistent format:

```json
{
  "error": "Description of the error"
}
```

Common errors:
- File not found
- Invalid PDF format
- Invalid page numbers
- Access denied (outside workspace)
- Permission errors

## Performance Considerations

- `client_session_timeout_seconds: 120` is recommended for processing large PDFs
- `cache_tools_list: true` improves performance by caching tool definitions
- Large PDFs may take longer to process; adjust timeout as needed

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt pytest

# Run tests
pytest tests/
```

### Logging

Set log level for debugging:

```bash
python server.py --log-level DEBUG --workspace_path=/path/to/workspace
```

## License

Part of the Klavis AI MCP Servers collection.

## Related Documentation

- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Klavis AI Documentation](https://klavis.ai/docs)
- [pypdf Documentation](https://pypdf.readthedocs.io)

## Support

For issues and questions:
- GitHub Issues: https://github.com/klavis-ai/klavis/issues
- Discord: https://discord.gg/p7TuTEcssn

