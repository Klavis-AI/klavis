# Discord MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Discord API](https://img.shields.io/badge/Discord_API-v10-5865F2.svg)](https://discord.com/developers/docs/intro)

## 📖 Overview

Discord MCP Server is a Model Context Protocol (MCP) implementation that bridges language models and other applications with Discord's API. It provides a standardized interface for executing Discord operations through various tools defined by the MCP standard. It currently only supports the bot mode.

## 🚀 Features

This server provides the following capabilities through MCP tools:

| Tool | Description |
|------|-------------|
| `get_server_info` | Retrieve detailed information about a Discord server (guild) |
| `list_members` | List members of a server with customizable result limits |
| `create_text_channel` | Create a new text channel with optional category and topic |
| `send_message` | Send a message to a specified channel |
| `read_messages` | Retrieve recent messages from a channel |
| `add_reaction` | Add a single emoji reaction to a message |
| `add_multiple_reactions` | Add multiple emoji reactions to a message |
| `remove_reaction` | Remove a specific reaction from a message |
| `get_user_info` | Retrieve information about a specific Discord user |

## 🔧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip

## ⚙️ Setup & Configuration

### Discord Bot Setup

1. **Create a Discord Bot**:
   - Visit the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and add a bot user
   - Under the "Bot" section, enable the following Privileged Gateway Intents:
     - Server Members Intent
     - Message Content Intent
   - Copy your Bot Token

2. **Invite the Bot**:
   - Navigate to OAuth2 > URL Generator
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions: 
     - Read Messages/View Channels
     - Send Messages
     - Manage Messages (for reactions)
     - Manage Channels (for channel creation)
   - Use the generated URL to invite the bot to your server

### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your bot token:
   ```
   DISCORD_TOKEN=YOUR_ACTUAL_DISCORD_BOT_TOKEN
   DISCORD_MCP_SERVER_PORT=5000
   ```

## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t discord-mcp-server -f mcp_servers/discord/Dockerfile .

# Run the container
docker run -d -p 5000:5000 --name discord-mcp discord-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5000:5000 --env-file mcp_servers/discord/.env --name discord-mcp discord-mcp-server
```

### Option 2: Python Virtual Environment

```bash
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

async def call_discord_tool():
    url = "http://localhost:5000/execute"
    payload = {
        "tool_name": "send_message",
        "tool_args": {
            "channel_id": "123456789012345678",
            "content": "Hello from MCP!"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Getting Server Information

```python
payload = {
    "tool_name": "get_server_info",
    "tool_args": {
        "server_id": "YOUR_SERVER_ID"
    }
}
```

### Sending a Message

```python
payload = {
    "tool_name": "send_message",
    "tool_args": {
        "channel_id": "YOUR_CHANNEL_ID",
        "content": "Hello from Discord MCP Server!"
    }
}
```

## 🛠️ Troubleshooting

### Docker Build Issues

- **File Not Found Errors**: If you see errors like `failed to compute cache key: failed to calculate checksum of ref: not found`, this means Docker can't find the files referenced in the Dockerfile. Make sure you're building from the root project directory (`klavis/`), not from the server directory.

### Common Runtime Issues

- **API Errors**: Check Discord API documentation for error meanings
- **Authentication Failures**: Verify your bot token is correct and hasn't expired
- **Missing Permissions**: Ensure your bot has the necessary permissions in the server
- **Intents Issues**: Confirm you've enabled the required intents in the Developer Portal

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details. 