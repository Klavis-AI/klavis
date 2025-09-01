# QuickBooks MCP Server

A Model Context Protocol (MCP) server for QuickBooks integration. Manage accounting data, invoices, and financial transactions using QuickBooks API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to QuickBooks with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("QUICKBOOKS", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run QuickBooks MCP Server (OAuth required)
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/quickbooks-mcp-server:latest
```

**OAuth Setup:** QuickBooks requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Invoice Management**: Create, read, update, and send invoices
- **Customer Management**: Manage customer and vendor information
- **Financial Reporting**: Access financial reports and accounting data
- **Transaction Processing**: Handle payments and financial transactions
- **Tax Operations**: Manage tax calculations and reporting

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