# Pandoc MCP Server

A Model Context Protocol (MCP) server for Pandoc integration. Convert documents between different formats using Pandoc's universal document converter.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Pandoc with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("PANDOC", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/pandoc-mcp-server:latest


# Run Pandoc MCP Server (no authentication required)
docker run -p 5000:5000 \
  ghcr.io/klavis-ai/pandoc-mcp-server:latest
```

**No Authentication:** Pandoc document conversion typically requires no external authentication.

## 🛠️ Available Tools

- **Document Conversion**: Convert between various document formats
- **Format Support**: Handle Markdown, HTML, PDF, Word, LaTeX, and more
- **Template Processing**: Use custom templates for document generation
- **Batch Processing**: Convert multiple documents efficiently
- **Format Options**: Configure conversion options and output settings

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
