# fastCRW MCP Server

A Model Context Protocol (MCP) server for fastCRW integration. Web scraping and content extraction using fastCRW's API for reliable data harvesting.

fastCRW is a Firecrawl-API-compatible web data engine in a single Rust binary. Self-host (AGPL open core) or use the managed cloud at [fastcrw.com](https://fastcrw.com).

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to fastCRW with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("FASTCRW", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/fastcrw-mcp-server:latest


# Run fastCRW MCP Server
docker run -p 5000:5000 -e API_KEY=$API_KEY \
  ghcr.io/klavis-ai/fastcrw-mcp-server:latest
```

**API Key Setup:** Get your fastCRW API key from the [fastCRW dashboard](https://fastcrw.com/). The server targets the managed cloud (`https://fastcrw.com/api`) by default. To point at a self-hosted instance, set `CRW_API_URL` (e.g. `http://localhost:3000`).

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
