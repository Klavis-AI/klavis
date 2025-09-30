# Microsoft Teams MCP Server

A Model Context Protocol (MCP) server for Microsoft Teams, enabling AI agents to manage teams, channels, chats, users, and meetings.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to the Microsoft Teams MCP Server with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("MSTEAMS", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

*The official Docker image will be available on GitHub Packages after this contribution is merged.*

```bash
# Example of how to run the future official image
docker pull ghcr.io/klavis-ai/msteams-mcp-server:latest

# Run with credentials passed as environment variables
docker run -p 8791:8791 \
  -e MS_CLIENT_ID="YOUR_CLIENT_ID" \
  -e MS_CLIENT_SECRET="YOUR_CLIENT_SECRET" \
  -e MS_TENANT_ID="YOUR_TENANT_ID" \
  ghcr.io/klavis-ai/msteams-mcp-server:latest
```

## 🛠️ Available Tools

- **Teams & Channels**: List, get, and create teams and channels.
- **Messaging**: Send messages to both team channels and private/group chats.
- **Users**: List and get users in the organization.
- **Meetings**: Create and list online meetings for users (*requires a work or school account*).

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Klavis AI Docs** | [docs.klavis.ai](https://docs.klavis.ai) |
| **💬 Discord Community** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **🐛 Report an Issue** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |

## 🧑‍💻 Local Development Setup

Follow these steps to run the server locally for development or contribution.

### 1. Prerequisites

- Python 3.8+
- A Microsoft Azure account with an App Registration.

### 2. Installation

```bash
# Navigate to this server's directory
cd mcp_servers/msteams

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Azure App Permissions

This server requires **Application-level** permissions. In your Azure App Registration, under "API permissions", add the following permissions for **Microsoft Graph** and grant admin consent:

- `Team.Read.All`
- `Channel.Read.All`
- `Group.ReadWrite.All`
- `User.Read.All`
- `Chat.Read.All`
- `Chat.ReadWrite.All`
- `OnlineMeetings.Read.All`
- `OnlineMeetings.ReadWrite.All`

### 4. Running the Server

The server can be run in two modes:

- **For Claude Desktop (stdio):**
  ```bash
  python server.py --stdio
  ```
  Use the `claude_desktop_config.json` file to configure the server, making sure to add your credentials to the `env` block.

- **For HTTP API Testing:**
  ```bash
  # First, copy .env.example to .env and fill it out
  cp .env.example .env
  # Then run the server:
  python server.py
  ```

## 🤝 Contributing

We welcome contributions! Please see the main [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📜 License

Apache 2.0 license - see [LICENSE](../../LICENSE) for details.

---

<div align="center">
  <p><strong>🚀 Supercharge AI Applications </strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>