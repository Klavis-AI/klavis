# Confluence MCP Server

A Model Context Protocol (MCP) server for Atlassian Confluence integration. Manage pages, spaces, and content using Confluence's API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Confluence with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("CONFLUENCE", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/confluence-mcp-server:latest


# Run Confluence MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/confluence-mcp-server:latest


# Run Confluence MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_confluence_api_token_here"}' \
  ghcr.io/klavis-ai/confluence-mcp-server:latest
```

**OAuth Setup:** Confluence requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Page Management**: Create, read, update, and delete Confluence pages
- **Space Operations**: Manage Confluence spaces and permissions
- **Content Search**: Search content across pages and spaces
- **Comments**: Add and manage page comments
- **Attachments**: Handle file attachments and media

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [www.klavis.ai/docs](https://www.klavis.ai/docs) |
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
    <a href="https://www.klavis.ai/docs">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>
