# Firecrawl MCP Server

A Model Context Protocol (MCP) server for Firecrawl integration. Web scraping and content extraction using Firecrawl's API for reliable data harvesting.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Firecrawl with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("FIRECRAWL", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/firecrawl-mcp-server:latest


# Run Firecrawl MCP Server
docker run -p 5000:5000 -e API_KEY=$API_KEY \
  ghcr.io/klavis-ai/firecrawl-mcp-server:latest
```

**API Key Setup:** Get your Firecrawl API key from the [Firecrawl Dashboard](https://firecrawl.dev/).

## 🛠️ Available Tools

- **Web Scraping**: Extract content from websites and web pages
- **Content Parsing**: Parse HTML and extract structured data
- **Bulk Crawling**: Crawl multiple pages and websites efficiently
- **Data Extraction**: Extract specific data points and metadata
- **Format Conversion**: Convert web content to various formats

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
