# MarkItDown MCP Server

A Model Context Protocol (MCP) server for MarkItDown integration. Convert documents and content to Markdown format using MarkItDown's conversion capabilities.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to MarkItDown with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("MARKITDOWN", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/markitdown-mcp-server:latest


# Run MarkItDown MCP Server (no authentication required)
docker run -p 5000:5000 \
  ghcr.io/klavis-ai/markitdown-mcp-server:latest
```

**No Authentication:** MarkItDown conversion typically requires no external authentication.

## 🛠️ Available Tools

- **Document Conversion**: Convert various document formats to Markdown
- **HTML to Markdown**: Convert HTML content to clean Markdown
- **File Processing**: Process multiple document types and formats
- **Content Cleaning**: Clean and optimize converted Markdown output
- **Batch Processing**: Convert multiple documents efficiently

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
