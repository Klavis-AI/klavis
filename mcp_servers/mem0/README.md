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
      "transport": "sse",
      "url": "http://localhost:8080/sse"
    }
  }
}
```

## Features

The server provides three main tools for managing persistent memories using mem0:

1. `mem0_add_memory`: Store any information in long-term memory with semantic indexing

2. `mem0_get_all_memories`: Retrieve all stored memories for comprehensive context 

3. `mem0_search_memories`: Semantically search through stored memories using natural language queries.

## Why?

This implementation allows for a persistent preferences system that can be accessed via MCP. The SSE-based server can run as a process that agents connect to, use, and disconnect from whenever needed. This pattern fits well with "cloud-native" use cases where the server and clients can be decoupled processes on different nodes.

### Server

By default, the server runs on 0.0.0.0:8080 but is configurable with command line arguments like:

```
uv run main.py --host <your host> --port <your port>
```

The server exposes an SSE endpoint at `/sse` that MCP clients can connect to for accessing the preferences management tools.
