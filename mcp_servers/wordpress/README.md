# WordPress MCP Server

A Model Context Protocol (MCP) server for WordPress integration. Manage posts, pages, comments, and media using WordPress REST API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to WordPress with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("WORDPRESS", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/wordpress-mcp-server:latest


# Run WordPress MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/wordpress-mcp-server:latest

# Run WordPress MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_wordpress_api_token_here"}' \
  ghcr.io/klavis-ai/wordpress-mcp-server:latest
```

**OAuth Setup:** WordPress requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Content Management**: Create, read, update posts and pages
- **Media Operations**: Upload and manage media files
- **Comment Management**: Handle comments and moderation
- **User Management**: Manage WordPress users and roles
- **Site Operations**: Access site settings and configurations

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
