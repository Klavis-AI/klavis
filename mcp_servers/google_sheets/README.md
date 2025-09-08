# Google Sheets MCP Server

A Model Context Protocol (MCP) server for Google Sheets integration. Read, write, and manage spreadsheet data using Google Sheets API with full OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Google Sheets with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("GOOGLE_SHEETS", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/google-sheets-mcp-server:latest


# Run Google Sheets MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/google-sheets-mcp-server:latest


# Run Google Sheets MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_google_access_token_here"}' \
  ghcr.io/klavis-ai/google-sheets-mcp-server:latest
```

**OAuth Setup:** Google Sheets requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools

- **Read Data**: Get spreadsheet values, ranges, and cell data
- **Write Data**: Update cells, rows, and ranges with new values
- **Sheet Management**: Create, delete, and manage worksheet tabs
- **Spreadsheet Info**: Get metadata, properties, and formatting details
- **Batch Operations**: Perform multiple read/write operations efficiently

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
