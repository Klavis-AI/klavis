# Google Slides MCP Server

A Model Context Protocol (MCP) server for Google Slides integration. Create, edit, and manage presentations using Google Slides API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Google Slides with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("GOOGLE_SLIDES", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/google-slides-mcp-server:latest


# Run Google Slides MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/google-slides-mcp-server:latest


# Run Google Slides MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_google_access_token_here"}' \
  ghcr.io/klavis-ai/google-slides-mcp-server:latest
```

**OAuth Setup:** Google Slides requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🔐 Security Note

When self-hosting with the local OAuth flow, after the first successful authorization the server writes the authorized user credentials to a `token.json` file in the server's working directory (relative path, written with default OS file permissions — no restrictive mode is set). On subsequent starts the server reuses `token.json` and refreshes it when expired (see `mcp_servers/google_slides/server.py`). Keep the working directory appropriately secured, and never commit `token.json` to version control.


## 🛠️ Available Tools

- **Presentation Management**: Create, read, update Google Slides presentations
- **Slide Operations**: Add, remove, and modify slides and layouts
- **Content Editing**: Insert text, images, and shapes into presentations
- **Formatting**: Apply themes, styles, and formatting to slides
- **Collaboration**: Manage sharing and collaborative editing

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
