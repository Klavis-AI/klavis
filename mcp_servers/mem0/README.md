# MCP Server with Mem0

This demonstrates a structured approach for using an [MCP](https://modelcontextprotocol.io/introduction) server with [mem0](https://mem0.ai) to manage memory for an AI application.

## Installation

1. Clone this repository
2. Initialize the `uv` environment:

```bash
uv venv
```

3. Activate the virtual environment:

```bash
source .venv/bin/activate
```

4. Install the dependencies using `uv`:

```bash
# Install in editable mode from pyproject.toml
uv pip install -e .
```

5. Update `.env` file in the root directory with your mem0 API key:

```bash
MEM0_API_KEY=your_api_key_here
```

## Usage

1. Start the MCP server:

```bash
uv run server.py
```

2. To configure Mem0 MCP using JSON configuration:

```json
{
  "mcpServers": {
    "mem0": {
      "transport": "http",
      "url": "http://localhost:5000/mcp"
    }
  }
}
```

## Features

This server provides the following capabilities through MCP tools:

| Tool | Description |
|------|-------------|
| `mem0_add_memory` | Store code snippets, implementation details, and programming knowledge for future reference |
| `mem0_get_all_memories` | Retrieve all stored memories for comprehensive context analysis |
| `mem0_search_memories` | Semantically search through stored memories using natural language queries |
| `mem0_update_memory` | Update an existing memory with new content while maintaining its unique identifier |
| `mem0_delete_memory` | Delete a specific memory by ID or delete all memories for a user |

## Why?

This implementation allows for a persistent preferences system that can be accessed via MCP. The streamable-HTTP based server can run as a process that agents connect to, use, and disconnect from whenever needed. This pattern fits well with "cloud-native" use cases where the server and clients can be decoupled processes on different nodes.

### Server

By default, the server runs on 0.0.0.0:5000 but is configurable with command line arguments like:

```
uv run main.py --host <your host> --port <your port>
```

The server exposes an Streamable HTTP endpoint at `/mcp` that MCP clients can connect to for accessing the preferences management tools.
