# OpenRouter MCP Server

A Model Context Protocol (MCP) server for OpenRouter, providing access to various AI models through a unified API.

## Features

- **Model Management**: List available models, get model details, and check model status
- **Chat Completions**: Generate text completions using various AI models
- **Model Comparison**: Compare different models' capabilities and pricing
- **Usage Tracking**: Monitor API usage and costs
- **Authentication**: Secure API key management

## Prerequisites

- Python 3.10 or higher
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

## Installation

1. Clone the repository and navigate to the OpenRouter MCP server directory:
```bash
cd mcp_servers/openrouter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENROUTER_API_KEY="your_api_key_here"
export OPENROUTER_MCP_SERVER_PORT="5000"
```

## Usage

### Starting the Server

```bash
python server.py --port 5000 --log-level INFO
```

### Available Endpoints

The server provides endpoints for both transport methods:

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/messages/` - SSE message handling endpoint
- `/mcp` - StreamableHTTP endpoint for direct API calls

## Authentication

The server uses a custom authentication header with your OpenRouter API key. The API key should be provided in the `x-auth-token` header:

```
x-auth-token: your_api_key_here
```

## Available Tools

### Model Management

#### List Models
```json
{
  "name": "openrouter_list_models",
  "arguments": {
    "limit": 50,
    "next_page_token": null
  }
}
```

#### Get Model Details
```json
{
  "name": "openrouter_get_model",
  "arguments": {
    "model_id": "anthropic/claude-3-opus"
  }
}
```

### Chat Completions

#### Generate Chat Completion
```json
{
  "name": "openrouter_create_chat_completion",
  "arguments": {
    "model": "anthropic/claude-3-opus",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "max_tokens": 1000,
    "temperature": 0.7,
    "stream": false
  }
}
```

#### Stream Chat Completion
```json
{
  "name": "openrouter_create_chat_completion_stream",
  "arguments": {
    "model": "anthropic/claude-3-opus",
    "messages": [
      {
        "role": "user",
        "content": "Write a short story about a robot."
      }
    ],
    "max_tokens": 500,
    "temperature": 0.8
  }
}
```

### Usage and Analytics

#### Get Usage Statistics
```json
{
  "name": "openrouter_get_usage",
  "arguments": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

#### Get User Profile
```json
{
  "name": "openrouter_get_user_profile",
  "arguments": {}
}
```

### Model Comparison

#### Compare Models
```json
{
  "name": "openrouter_compare_models",
  "arguments": {
    "models": ["anthropic/claude-3-opus", "openai/gpt-4", "meta-llama/llama-3.1-8b-instruct"],
    "test_prompt": "Explain quantum computing in simple terms"
  }
}
```

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters
- Authentication failures
- API rate limiting
- Network connectivity issues
- Model availability issues

## Rate Limiting

OpenRouter API has rate limits. The server will handle rate limit responses appropriately. See the [OpenRouter API documentation](https://openrouter.ai/docs) for current limits.

## Contributing

1. Follow the existing code structure
2. Add new tools to the appropriate files in the `tools/` directory
3. Update `tools/__init__.py` to export new functions
4. Add tool definitions to `server.py`
5. Update this README with new functionality

## License

This project follows the same license as the parent Klavis project. 