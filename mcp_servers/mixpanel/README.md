# Mixpanel MCP Server

A Model Context Protocol (MCP) server for Mixpanel integration. Analyze user events, track metrics, and manage analytics using Mixpanel's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Mixpanel with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("MIXPANEL", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Mixpanel MCP Server
docker run -p 5000:5000 -e API_KEY=your_mixpanel_secret \
  ghcr.io/klavis-ai/mixpanel-mcp-server:latest
```

**API Secret Setup:** Get your Mixpanel API secret from your [Mixpanel project settings](https://mixpanel.com/settings/project).

## 🛠️ Available Tools

- **Event Analytics**: Track and analyze user events and behaviors
- **User Profiles**: Manage user properties and segmentation
- **Funnel Analysis**: Create and analyze conversion funnels
- **Cohort Analysis**: Track user retention and engagement
- **Report Generation**: Generate custom analytics reports

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