# Olostep MCP Server

A Model Context Protocol (MCP) server for Olostep integration. Scrape websites, search the web, extract structured data, crawl entire sites, and get AI-powered answers with citations.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Olostep with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("OLOSTEP", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/olostep-mcp-server:latest

# Run Olostep MCP Server
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_olostep_api_key_here"}' \
  ghcr.io/klavis-ai/olostep-mcp-server:latest
```

## 🛠️ Available Tools

- **Scrape Website**: Extract content from any URL in markdown, HTML, JSON, or text format
- **Search Web**: Search the web with structured, parser-based results
- **AI Answers**: Get AI-powered answers with citations and optional JSON-shaped output
- **Batch Scrape**: Scrape up to 10,000 URLs simultaneously
- **Get Batch Results**: Retrieve results from completed batch jobs
- **Create Crawl**: Autonomously discover and scrape entire websites by following links
- **Create Map**: Discover and list all URLs on a website with filtering
- **Get Webpage Content**: Quick markdown extraction from a single page
- **Get Website URLs**: Search and retrieve relevant URLs from a website

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
