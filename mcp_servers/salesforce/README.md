# Salesforce MCP Server

A Model Context Protocol (MCP) server for Salesforce CRM integration. Manage leads, contacts, opportunities, and other Salesforce objects using the Salesforce API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Salesforce with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("SALESFORCE", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Salesforce MCP Server (OAuth required)
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/salesforce-mcp-server:latest
```

**OAuth Setup:** Salesforce requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Lead Management**: Create, read, update leads and lead conversion
- **Contact Operations**: Manage contacts and customer relationships
- **Opportunity Tracking**: Handle sales opportunities and pipeline
- **Account Management**: Manage customer accounts and hierarchies
- **Custom Objects**: Work with custom Salesforce objects and fields
- **Reports & Analytics**: Access Salesforce reports and dashboards

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
