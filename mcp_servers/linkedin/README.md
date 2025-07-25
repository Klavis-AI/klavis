# LinkedIn MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![LinkedIn API](https://img.shields.io/badge/LinkedIn_API-v2-0077B5.svg)](https://docs.microsoft.com/en-us/linkedin/)

## 📖 Overview

LinkedIn MCP Server is a Model Context Protocol (MCP) implementation that bridges language models and other applications with LinkedIn's API. It provides a standardized interface for executing LinkedIn operations through various tools defined by the MCP standard.

## 🚀 Features

This server provides the following capabilities through MCP tools:

| Tool | Description |
|------|-------------|
| `get_profile_info` | Retrieve LinkedIn profile information (current user or specified person) |
| `create_post` | Create a text/article post on LinkedIn with customizable visibility |

## 🔧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip

## ⚙️ Setup & Configuration

### LinkedIn App Setup

1. **Create a LinkedIn App**:
   - Visit the [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
   - Create a new application and add it to your developer account
   - Under the "Auth" section, configure the following scopes:
     - `r_liteprofile` (for basic profile access)
     - `w_member_social` (for posting content)
   - Copy your Client ID and Client Secret

2. **Generate Access Token**:
   - Use LinkedIn's OAuth2 authorization code flow
   - Navigate to OAuth2 > URL Generator in the LinkedIn Developer Portal
   - Generate an access token with the required scopes
   - For testing, you can use the temporary access token provided in the developer console

   ### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your LinkedIn credentials:
   ```
   LINKEDIN_ACCESS_TOKEN=YOUR_ACTUAL_LINKEDIN_ACCESS_TOKEN
   LINKEDIN_MCP_SERVER_PORT=5000
   ```

   ## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t linkedin-mcp-server -f mcp_servers/linkedin/Dockerfile .

# Run the container
docker run -d -p 5000:5000 --name linkedin-mcp linkedin-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5000:5000 --env-file mcp_servers/linkedin/.env --name linkedin-mcp linkedin-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the LinkedIn server directory
cd mcp_servers/linkedin

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

async def call_linkedin_tool():
    url = "http://localhost:5000/mcp"
    payload = {
        "tool_name": "linkedin_create_text_post",
        "tool_args": {
            "text": "Hello from LinkedIn MCP Server!",
            "visibility": "PUBLIC"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Getting Profile Information

```python
payload = {
    "tool_name": "linkedin_get_profile_info",
    "tool_args": {}  # Empty for current user, or provide person_id
}
```

#### Basic Text Post

```python
payload = {
    "tool_name": "linkedin_create_post",
    "tool_args": {
        "text": "Excited to share my latest project!",
        "visibility": "PUBLIC"  # Optional: defaults to "PUBLIC"
    }
}
```

#### Article-Style Post (with title)

```python
payload = {
    "tool_name": "linkedin_create_post",
    "tool_args": {
        "title": "The Future of AI",
        "text": "In this article, I explore the latest trends in artificial intelligence...",
        "visibility": "PUBLIC"
    }
}
```

## 🛠️ Troubleshooting

### Docker Build Issues

- **File Not Found Errors**: If you see errors like `failed to compute cache key: failed to calculate checksum of ref: not found`, this means Docker can't find the files referenced in the Dockerfile. Make sure you're building from the root project directory (`klavis/`), not from the server directory.

### Common Runtime Issues

- **Authentication Failures**: Verify your access token is correct and hasn't expired. LinkedIn access tokens typically have a short lifespan.
- **API Errors**: Check LinkedIn API documentation for error meanings and status codes.
- **Missing Permissions**: Ensure your LinkedIn app has the necessary scopes enabled (`r_liteprofile`, `w_member_social`).
- **Rate Limiting**: LinkedIn has strict rate limits. Implement appropriate delays between requests if needed.
- **Scope Issues**: Some endpoints require additional permissions or LinkedIn partnership status.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details. 
