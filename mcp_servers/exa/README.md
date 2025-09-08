# Exa MCP Server

A Model Context Protocol (MCP) server for Exa (formerly Metaphor) integration. Perform semantic web searches and content discovery using Exa's AI-powered search API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Exa with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("EXA", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Exa MCP Server
docker run -p 5000:5000 -e API_KEY=your_exa_api_key \
  ghcr.io/klavis-ai/exa-mcp-server:latest
```

**API Key Setup:** Get your Exa API key from the [Exa Dashboard](https://dashboard.exa.ai/).

## 🛠️ Available Tools

- **Semantic Search**: AI-powered semantic web search
- **Content Discovery**: Find relevant content and resources
- **Neural Search**: Advanced neural search capabilities
- **Similar Content**: Find content similar to given URLs or topics
- **Research Tools**: Academic and professional research assistance

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