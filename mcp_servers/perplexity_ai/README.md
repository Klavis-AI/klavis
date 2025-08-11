# Perplexity AI MCP Server

A Model Context Protocol (MCP) server that provides conversational AI capabilities using Perplexity AI's powerful Sonar models. This server enables AI assistants to engage in conversations, perform deep research, and conduct reasoning tasks with automatic citation handling.

## 🚀 Quick Start for JavaScript Developers

As someone coming from a JavaScript background, this guide will help you understand Python and get the Perplexity AI MCP server running quickly.

### Prerequisites

1. **Python 3.11 or higher** - Think of this like Node.js for JavaScript
   - **macOS**: Use `brew install python` or download from [python.org](https://python.org)
   - **Windows**: Download from [python.org](https://python.org) and check "Add Python to PATH"
   - **Linux**: `sudo apt update && sudo apt install python3.11 python3.11-pip`

2. **Get a Perplexity AI API Key**
   - Visit [Perplexity AI Settings](https://www.perplexity.ai/settings/api)
   - Create an account and generate an API key
   - Save this key - you'll need it later

### Installation

```bash
# 1. Navigate to the server directory
cd mcp_servers/perplexity_ai

# 2. Create a virtual environment (like node_modules for Python)
python -m venv venv

# 3. Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies (like npm install)
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in this directory (like environment variables in JavaScript):

```bash
# Copy the example file and edit it
cp .env.example .env

# Edit the .env file with your API key
# .env file
PERPLEXITY_API_KEY=your_api_key_here
PERPLEXITY_MCP_SERVER_PORT=5000
```

### Running the Server

```bash
# Start the server (like npm start)
python server.py

# Or with custom port
python server.py --port 8080

# With debug logging
python server.py --log-level DEBUG
```

The server will start on `http://localhost:5000` by default.

## 🔧 Understanding the Code Structure

For JavaScript developers, here's how Python concepts map to what you know:

| JavaScript | Python | Purpose |
|------------|--------|---------|
| `package.json` | `requirements.txt` | Dependencies |
| `import/export` | `import/from` | Module system |
| `async/await` | `async/await` | Same! Asynchronous code |
| `npm install` | `pip install` | Package installation |
| `node_modules` | `venv` | Dependency isolation |
| `function()` | `def function():` | Function definition |
| `const obj = {}` | `obj = {}` | Object creation |

### Project Structure

```
perplexity_ai/
├── server.py              # Main server file (like app.js)
├── requirements.txt       # Dependencies (like package.json)
├── Dockerfile            # Container setup
├── README.md             # This file
├── .env                  # Environment variables
└── tools/                # Tool implementations
    ├── __init__.py       # Package exports (like index.js)
    ├── base.py           # Base API client
    └── search.py         # Search tool implementations
```

## 🛠 Available Tools

The server provides three main conversation tools that match the JavaScript implementation:

### 1. Perplexity Search (`perplexity_search`)
Performs web search using the **sonar-pro** model. Accepts an array of messages and returns a search completion response with citations.

```python
# Example usage in Python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"}
]
result = await perplexity_search(messages)
```

**Model Used:** `sonar-pro`  
**Best For:** Web search and quick answers

### 2. Perplexity Research (`perplexity_research`)
Performs deep research using the **sonar-deep-research** model with comprehensive responses and citations.

```python
messages = [
    {"role": "user", "content": "Research the latest developments in renewable energy technology"}
]
result = await perplexity_research(messages)
```

**Model Used:** `sonar-deep-research`  
**Best For:** In-depth research requiring comprehensive analysis

### 3. Perplexity Reason (`perplexity_reason`)
Performs reasoning tasks using the **sonar-reasoning-pro** model for well-reasoned responses.

```python
messages = [
    {"role": "user", "content": "Analyze the pros and cons of remote work for software development teams"}
]
result = await perplexity_reason(messages)
```

**Model Used:** `sonar-reasoning-pro`  
**Best For:** Complex reasoning, analysis, and logical thinking tasks

### Message Format

All tools accept an array of message objects with the following structure:

```python
{
    "role": "system|user|assistant",  # Role of the message sender
    "content": "The message content"   # The actual message text
}
```

### Response Format

All tools return a string response that includes:
- The main response content from the AI model
- Automatically appended citations (when available)
- Numbered citation format: `[1] source_url`

Example response:
```
Machine learning is a subset of artificial intelligence...

Citations:
[1] https://example.com/ml-definition
[2] https://example.com/ai-overview
```

### Model Comparison

| Tool | Model | Use Case | Response Time | Detail Level |
|------|-------|----------|---------------|-------------|
| `perplexity_search` | `sonar-pro` | Web search, quick questions | Fast | Moderate |
| `perplexity_research` | `sonar-deep-research` | In-depth research, analysis | Slower | High |
| `perplexity_reason` | `sonar-reasoning-pro` | Logic, reasoning, problem-solving | Moderate | High |

### 🔄 JavaScript vs Python Versions

This Python implementation is **functionally identical** to the JavaScript version:

| Feature | JavaScript | Python | 
|---------|------------|--------|
| Tool Names | ✅ `perplexity_search`, `perplexity_research`, `perplexity_reason` | ✅ Same |
| Models Used | ✅ `sonar-pro`, `sonar-deep-research`, `sonar-reasoning-pro` | ✅ Same |
| Input Format | ✅ Array of message objects | ✅ Same |
| Citation Handling | ✅ Auto-appended to response | ✅ Same |
| API Compatibility | ✅ MCP Protocol | ✅ Same |

You can switch between the JavaScript and Python versions seamlessly!

## 🌐 API Endpoints

The server exposes two transport methods:

1. **Server-Sent Events (SSE)**: `http://localhost:5000/sse`
2. **HTTP Streaming**: `http://localhost:5000/mcp`

## 🔑 Authentication

Pass your Perplexity AI API key in the request headers:

```bash
# For SSE
curl -H "x-api-key: your_api_key_here" http://localhost:5000/sse

# For HTTP requests
curl -H "x-api-key: your_api_key_here" http://localhost:5000/mcp
```

## 🐳 Docker Deployment

If you're familiar with Docker from Node.js:

```bash
# Build the image
docker build -t perplexity-mcp-server .

# Run the container
docker run -p 5000:5000 -e PERPLEXITY_API_KEY=your_key perplexity-mcp-server
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | Your Perplexity AI API key | Required |
| `PERPLEXITY_MCP_SERVER_PORT` | Server port | 5000 |

## 🔍 Testing the Server

You can test the server using curl (like testing an Express.js API):

```bash
# Test the SSE endpoint
curl -H "x-api-key: your_key" "http://localhost:5000/sse"

# Test with different tools
# 1. Web search
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_key" \
  -d '{"method": "tools/call", "params": {"name": "perplexity_search", "arguments": {"messages": [{"role": "user", "content": "What are the differences between Python and JavaScript?"}]}}}' \
  http://localhost:5000/mcp

# 2. Deep research
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_key" \
  -d '{"method": "tools/call", "params": {"name": "perplexity_research", "arguments": {"messages": [{"role": "user", "content": "Research the latest developments in quantum computing"}]}}}' \
  http://localhost:5000/mcp

# 3. Reasoning task
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: your_key" \
  -d '{"method": "tools/call", "params": {"name": "perplexity_reason", "arguments": {"messages": [{"role": "user", "content": "Analyze the pros and cons of microservices vs monolithic architecture"}]}}}' \
  http://localhost:5000/mcp
```

## 🆘 Troubleshooting

### Common Issues for JavaScript Developers

1. **Import Errors**: Make sure you've activated the virtual environment
2. **Module Not Found**: Run `pip install -r requirements.txt`
3. **Port Already in Use**: Change the port with `--port 8080`
4. **API Key Issues**: Check your `.env` file and Perplexity AI account
5. **Tool Not Found**: Ensure you're using the correct tool names (`perplexity_search`, `perplexity_research`, `perplexity_reason`)
6. **Message Format Error**: Make sure your messages array contains objects with `role` and `content` fields

### Debug Mode

Run with debugging enabled:

```bash
python server.py --log-level DEBUG
```

## 📚 Learning Resources

To understand Python better coming from JavaScript:

- [Python for JavaScript Developers](https://realpython.com/python-vs-javascript/)
- [Async Programming in Python](https://realpython.com/async-io-python/)
- [Python Virtual Environments](https://realpython.com/python-virtual-environments-a-primer/)

## 🤝 Contributing

Feel free to submit issues and PRs! The code structure should feel familiar if you've worked with Express.js or similar frameworks.

## 📄 License

This project follows the same license as the main Klavis repository.
