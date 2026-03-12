# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides tools to search academic literature from ArXiv and Google Scholar. The server implements two main search tools:

- `search-arxiv`: Search ArXiv for academic articles using keywords
- `search-google-scholar`: Search Google Scholar for academic publications using keywords

## Architecture

The codebase follows a modular structure:

- `src/mcp_scholarly/server.py`: Main MCP server implementation with tool registration and request handling
- `src/mcp_scholarly/arxiv_search.py`: ArXiv search functionality using the arxiv Python library
- `src/mcp_scholarly/google_scholar.py`: Google Scholar search using the scholarly library
- `src/mcp_scholarly/__init__.py`: Package entry point and main function

The server runs as an MCP server using stdio communication and registers tools that can be called by MCP clients like Claude Desktop.

## Development Commands

### Setup and Dependencies
```bash
# Install/sync dependencies
uv sync

# Install in development mode
uv sync --no-install-project --no-dev --no-editable
```

### Building and Publishing
```bash
# Build package distributions
uv build

# Publish to PyPI (requires credentials)
uv publish
```

### Running the Server

#### Development Mode
```bash
# Run directly with uv
uv --directory . run mcp-scholarly

# For debugging with MCP Inspector
npx @modelcontextprotocol/inspector uv --directory . run mcp-scholarly
```

#### Production Mode
```bash
# Run as installed package
uvx mcp-scholarly

# Using Docker
docker run --rm -i mcp/scholarly
```

### MCP Client Configuration

For Claude Desktop integration, add to `claude_desktop_config.json`:

**Development:**
```json
{
  "mcpServers": {
    "mcp-scholarly": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-scholarly", "run", "mcp-scholarly"]
    }
  }
}
```

**Production:**
```json
{
  "mcpServers": {
    "mcp-scholarly": {
      "command": "uvx",
      "args": ["mcp-scholarly"]
    }
  }
}
```

## Key Dependencies

- `mcp`: MCP SDK for server implementation
- `arxiv`: ArXiv API client for academic paper search
- `scholarly`: Google Scholar scraping library
- `free-proxy`: Proxy support for scholarly requests

## Testing and Debugging

Since MCP servers communicate over stdio, use the MCP Inspector for debugging:
```bash
npx @modelcontextprotocol/inspector uv --directory . run mcp-scholarly
```

The Inspector provides a web interface to test MCP tool calls and debug server responses.