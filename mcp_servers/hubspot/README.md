# HubSpot MCP Server

A Model Context Protocol (MCP) server for HubSpot CRM integration. Manage contacts, deals, companies, and marketing campaigns using HubSpot's API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to HubSpot with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("HUBSPOT", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run HubSpot MCP Server (OAuth required)
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/hubspot-mcp-server:latest
```

**OAuth Setup:** HubSpot requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Contact Management**: Create, read, update contacts and customer data
- **Deal Operations**: Manage sales deals and pipeline stages
- **Company Management**: Handle company records and relationships
- **Marketing Tools**: Manage campaigns and marketing automation
- **Custom Properties**: Work with custom fields and properties

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