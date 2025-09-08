# Google Jobs MCP Server

A Model Context Protocol (MCP) server for Google Jobs API integration. Search and access job listings using Google's Jobs API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Google Jobs with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("GOOGLE_JOBS", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Google Jobs MCP Server
docker run -p 5000:5000 -e API_KEY=your_google_api_key \
  ghcr.io/klavis-ai/google_jobs-mcp-server:latest
```

**API Key Setup:** Get your Google API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and enable the Google Jobs API.

## 🛠️ Available Tools

- **Job Search**: Search for job listings by keywords, location, and filters
- **Job Details**: Get detailed information about specific job postings
- **Company Information**: Access employer details and company profiles
- **Location-based Search**: Find jobs in specific geographic areas
- **Filter Options**: Apply various filters for salary, experience, job type

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