# Trello MCP Server

A Model Context Protocol (MCP) server for Trello integration. Manage boards, lists, cards, and checklists using Trello's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🐳 Using Docker (For Self-Hosting)

```bash
# Build the Docker image
docker build -t trello-mcp-server .

# Run the server with your credentials
docker run -p 5002:5002 -e TRELLO_API_KEY="your_key" -e TRELLO_API_TOKEN="your_token" trello-mcp-server
```

### 💻 Local Development

```bash
# Navigate to the server directory
cd mcp_servers/trello

# Create and activate virtual environment
uv venv
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Create a .env file with your Trello credentials
# TRELLO_API_KEY=your_key
# TRELLO_API_TOKEN=your_token

# Run the server
python server.py
```

## 🛠️ Available Tools

- **Board Management**: Create new boards and fetch existing ones.
- **List Operations**: Fetch lists from boards.
- **Card Operations**: Create, read, update, and delete cards within lists.
- **Checklist Management**: Create checklists on cards and manage their items.

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [docs.klavis.ai](https://docs.klavis.ai) |
| **💬 Discord** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **🐛 Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📜 License

Apache 2.0 license - see [LICENSE](../../LICENSE) for details.