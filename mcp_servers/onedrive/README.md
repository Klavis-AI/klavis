# OneDrive MCP Server

A Model Context Protocol (MCP) server for Microsoft OneDrive integration. Manage files, folders, and sharing using OneDrive's API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to OneDrive with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("ONEDRIVE", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run OneDrive MCP Server (OAuth support through Klavis AI)
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/onedrive-mcp-server:latest

# Run OneDrive MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_onedrive_access_token_here"}' \
  ghcr.io/klavis-ai/onedrive-mcp-server:latest
```

**OAuth Setup:** OneDrive requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **File Management**: Upload, download, and manage OneDrive files
- **Folder Operations**: Create, move, and organize folders
- **Sharing**: Create and manage shared links and permissions
- **Search**: Search files and folders by name and content
- **Collaboration**: Handle real-time collaboration and version control

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