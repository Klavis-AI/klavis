# Perplexity AI MCP Server

A Model Context Protocol (MCP) server for performing real-time web search and reasoning using Perplexity AI's Sonar models. Provides focused tools with automatic citation handling.

## Features

- **Web search**: Uses Perplexity `sonar-pro` for up-to-date results
- **Reasoning**: Uses Perplexity `sonar-reasoning-pro` for structured analysis
- **Citations**: Automatically extracts and appends numbered citations
- **Conversation context**: Accepts `system`/`user`/`assistant` messages
- **Dual transport**: Supports both SSE and StreamableHTTP
- **MCP compatible**: Implements the standard MCP server interface

## Available Tools

### `perplexity_search`
Performs a web search via Perplexity Sonar models.

- **Model**: `sonar-pro`
- **Parameters**:
  - `messages` (array of objects, required): Each item has `role` and `content`
- **Returns**: Text with result content and appended citations when available
- **Best for**: Research queries, real-time facts, current events

### `perplexity_reason`
Performs reasoning tasks using Perplexity's reasoning-optimized model.

- **Model**: `sonar-reasoning-pro`
- **Parameters**:
  - `messages` (array of objects, required): Each item has `role` and `content`
- **Returns**: Well-reasoned response with citations when available
- **Best for**: Multi-step reasoning and structured analysis

## Prerequisites

- Python 3.11+
- Perplexity AI API key (create in Perplexity settings)
- Docker (optional)

## Configuration

Create a `.env` file in `mcp_servers/perplexity_ai/` for server config:

```bash
PERPLEXITY_MCP_SERVER_PORT=5000
```

API keys are provided via request header (see Authentication). The server does not read the API key from `.env`.

## Authentication

Provide your Perplexity API key in the request header:

```
x-api-key: YOUR_PERPLEXITY_API_KEY
```

## Running the Server

### Direct Python

```bash
cd mcp_servers/perplexity_ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py --port 5000 --log-level INFO
```

### Docker (from repo root)

```bash
docker build -t perplexity-mcp-server -f mcp_servers/perplexity_ai/Dockerfile .
docker run -p 5000:5000 perplexity-mcp-server
```

### Command line options

- `--port`: Port to listen on (default: 5000)
- `--log-level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `--json-response`: Return JSON for StreamableHTTP instead of SSE streams

## API Endpoints

- `/sse` — Server-Sent Events endpoint
- `/messages/` — SSE message handling endpoint
- `/mcp` — StreamableHTTP endpoint (JSON-RPC over HTTP)

## Usage

### Call via HTTP

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "x-api-key: YOUR_PERPLEXITY_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"perplexity_search","arguments":{"messages":[{"role":"user","content":"What is quantum computing?"}]}}}' \
  http://localhost:5000/mcp
```

### Example (client-side tool call)

```python
response = await client.call_tool(
    "perplexity_search",
    {
        "messages": [
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": "Latest developments in AI this week"}
        ]
    }
)

response = await client.call_tool(
    "perplexity_reason",
    {
        "messages": [
            {"role": "user", "content": "Reason step by step: pros and cons of nuclear vs solar for baseload"}
        ]
    }
)
```

## Response format

The tool returns text content. When citations are present, they are appended as numbered references:

```
...answer content...

Citations:
[1] https://example.com/source-1
[2] https://example.com/source-2
```

## Error handling

Common errors include:

- Invalid or missing `messages`
- Missing/invalid API key
- Upstream API rate limits or network failures

All responses follow standard MCP error formatting.

Note: For the StreamableHTTP endpoint, clients must set the `Accept` header to include both `application/json` and `text/event-stream`.

## Dependencies

- mcp>=1.12.0
- fastapi
- starlette
- uvicorn[standard]
- httpx
- click
- python-dotenv

## License

This project follows the same license as the parent Klavis repository.