# Freshdesk MCP Server

A Model Context Protocol (MCP) server for Freshdesk integration. Manage tickets, contacts, and customer support using Freshdesk's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Freshdesk with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("FRESHDESK", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Freshdesk MCP Server
docker run -p 5000:5000 -e API_KEY=your_freshdesk_api_key \
  ghcr.io/klavis-ai/freshdesk-mcp-server:latest
```

**API Key Setup:** Get your Freshdesk API key from your [Freshdesk admin settings](https://support.freshdesk.com/en/support/solutions/articles/215517).

## 🛠️ Available Tools

- **Ticket Management**: Create, read, update, and resolve support tickets
- **Contact Management**: Manage customer contacts and information
- **Agent Operations**: Handle agent assignments and ticket routing
- **Knowledge Base**: Access and manage knowledge base articles
- **Reporting**: Generate support metrics and analytics

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