# LinkedIn MCP Server

A Model Context Protocol (MCP) server for LinkedIn integration. Manage professional profiles, posts, and networking using LinkedIn's API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to LinkedIn with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("LINKEDIN", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run LinkedIn MCP Server (OAuth support through Klavis AI)
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/linkedin-mcp-server:latest

# Run LinkedIn MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_linkedin_access_token_here"}' \
  ghcr.io/klavis-ai/linkedin-mcp-server:latest
```

**OAuth Setup:** LinkedIn requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Profile Management**: Access and update professional profiles
- **Post Operations**: Create, read, and manage LinkedIn posts
- **Connection Management**: Manage professional connections
- **Company Pages**: Handle company page content and updates
- **Analytics**: Access post and profile analytics

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