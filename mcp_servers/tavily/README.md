# Tavily MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Tavily API](https://img.shields.io/badge/Tavily_API-v1-4b9ce2.svg)](https://docs.tavily.com)

## 📖 Overview

Tavily MCP Server is a Model Context Protocol (MCP) implementation that connects language models and other applications with the Tavily API. It provides a standardized interface for executing web search, extraction, crawling, and mapping operations through MCP tools.

## 🚀 Features

This server provides the following capabilities through MCP tools:

| Tool | Description |
|------|-------------|
| `tavily_search` | Search the web with filters like topic, date range, domains, images, and raw content |
| `tavily_extract` | Extract and parse content from one or more web pages |
| `tavily_crawl` | Crawl a website starting from a root URL with depth/breadth controls |
| `tavily_map` | Generate a website map without heavy content extraction |

## 🔧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip
- **Tavily API Key:** Get one from [Tavily](https://app.tavily.com)

## ⚙️ Setup & Configuration

### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your Tavily API credentials:
   ```
   TAVILY_API_KEY=YOUR_ACTUAL_TAVILY_API_KEY
   TAVILY_MCP_SERVER_PORT=5000
   ```

## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t tavily-mcp-server -f mcp_servers/tavily/Dockerfile .

# Run the container
docker run -d -p 5000:5000 --env-file mcp_servers/tavily/.env --name tavily-mcp tavily-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the Tavily server directory
cd mcp_servers/tavily

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5000`.

## 🔌 API Usage

The server implements the Model Context Protocol (MCP) standard. Here's an example of how to call a tool:

```python
import httpx

async def call_tavily_tool():
    url = "http://localhost:5000/mcp"
    payload = {
        "tool_name": "tavily_search",
        "tool_args": {
            "query": "multi-agent Retrieval-Augmented Generation",
            "topic": "news",
            "max_results": 5,
            "include_images": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Tavily Search

```python
payload = {
    "tool_name": "tavily_search",
    "tool_args": {
        "query": "multi-agent RAG frameworks",
        "topic": "news",
        "max_results": 5,
        "include_images": True
    }
}
```

### Tavily Extract

```python
payload = {
    "tool_name": "tavily_extract",
    "tool_args": {
        "urls": ["https://www.python.org"],
        "extract_depth": "advanced",
        "include_images": True
    }
}
```

### Tavily Crawl

```python
payload = {
    "tool_name": "tavily_crawl",
    "tool_args": {
        "url": "https://example.com",
        "max_depth": 2,
        "limit": 10
    }
}
```

### Tavily Map

```python
payload = {
    "tool_name": "tavily_map",
    "tool_args": {
        "url": "https://example.com",
        "max_depth": 1
    }
}
```

## 🛠️ Troubleshooting

### Docker Build Issues

- **File Not Found Errors**: Ensure you are building from the root project directory (`klavis/`), not from the server directory.

### Common Runtime Issues

- **Authentication Failures**: Verify your API key is correct and has not expired.
- **API Errors**: Check the Tavily API documentation for error meanings.
- **Rate Limiting**: Tavily may have usage limits depending on your plan.
- **Invalid Arguments**: Make sure your payload matches the expected schema for each tool.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
