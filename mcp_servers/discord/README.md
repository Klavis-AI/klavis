# Discord MCP Server

A Model Context Protocol (MCP) server for Discord integration. Send messages, manage channels, and interact with Discord servers using Discord's API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Discord with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("DISCORD", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Discord MCP Server
docker run -p 5000:5000 -e DISCORD_TOKEN=your_discord_bot_token_here \
  ghcr.io/klavis-ai/discord-mcp-server:latest
```

## 🛠️ Available Tools

- **Message Management**: Send, edit, and delete messages
- **Channel Operations**: Manage channels and channel permissions
- **Server Management**: Get server information and member details
- **User Interactions**: Manage user roles and permissions
- **Bot Operations**: Handle bot-specific Discord functionality

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [docs.klavis.ai](https://docs.klavis.ai) |
| **💬 Discord** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **🐛 Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📜 License

MIT License - see [LICENSE](../../LICENSE) for details.

---

<div align="center">
  <p><strong>🚀 Supercharge AI Applications </strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>