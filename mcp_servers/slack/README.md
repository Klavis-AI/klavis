# Slack MCP Server

A Model Context Protocol (MCP) server for Slack integration. Send messages, manage channels, search conversations, and handle workspace operations using both bot and user tokens.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Slack with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("SLACK", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/slack-mcp-server:latest


# Run Slack MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/slack-mcp-server:latest

# Run Slack MCP Server (no OAuth support)
docker run -p 5000:5000 \
  -e SLACK_BOT_TOKEN=xoxb-your-bot-token \
  -e SLACK_USER_TOKEN=xoxp-your-user-token \
  ghcr.io/klavis-ai/slack-mcp-server:latest
```

**OAuth Setup:** For OAuth authentication (recommended), use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys). This handles the complex OAuth flow automatically.

**Manual Setup:** Alternatively, provide your Slack bot and user tokens directly.

## 🛠️ Available Tools

### User Tools (User Token)
- **Channel Management**: List channels, get channel history
- **Messaging**: Post messages, reply to threads, add reactions as user
- **User Management**: List users, get user information
- **Search**: Search messages with user permissions

### Bot Tools (Bot Token)
- **Bot Messaging**: Send messages, reply to threads, add reactions as bot
- **Workspace Operations**: Bot-specific channel and user operations

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

---

<div align="center">
  <p><strong>🚀 Supercharge AI Applications </strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>
