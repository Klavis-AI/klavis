# mcp-scholarly

A Model Context Protocol (MCP) server to search for accurate academic articles from arXiv and Google Scholar.

> **Note**: This project is forked and modified from [adityak74/mcp-scholarly](https://github.com/adityak74/mcp-scholarly)

## Features

- Search academic articles on arXiv
- Search academic articles on Google Scholar
- MCP-compliant server for integration with AI assistants

## Requirements

- Python >= 3.11
- Dependencies listed in `pyproject.toml`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Klavis-AI/klavis.git
cd mcp_servers/scholarly
```

2. Install `uv` if you haven't already:
```bash
pip install uv
```

## Running the MCP Server

### Using uv (Recommended)

Run the server with default settings (port 5000):
```bash
uv run mcp-scholarly
```

### Custom Port and Options

You can customize the server with various options:

```bash
# Run on a custom port
uv run mcp-scholarly --port 8080

# Set logging level
uv run mcp-scholarly --log-level DEBUG

# Enable JSON responses instead of SSE streams
uv run mcp-scholarly --json-response
```

### Using Python Module

Alternatively, run as a Python module:
```bash
uv run python -m mcp_scholarly
```

### Environment Variables

You can set the default port using an environment variable:
```bash
# Set in .env file
SCHOLARLY_MCP_SERVER_PORT=5000
```

## Using Docker

Build and run the server using Docker:

```bash
# Build the Docker image from the repository root
docker build -f mcp_servers/scholarly/Dockerfile -t mcp-scholarly .

# Run the container
docker run -p 5000:5000 mcp-scholarly

# Run with environment variables
docker run -p 5000:5000 -e SCHOLARLY_MCP_SERVER_PORT=5000 mcp-scholarly
```

## Available Options

- `--port`: Port to listen on for HTTP (default: 5000)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--json-response`: Enable JSON responses for StreamableHTTP instead of SSE streams

## License

See [LICENSE](LICENSE) file for details.
