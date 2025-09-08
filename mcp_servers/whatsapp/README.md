# WhatsApp MCP Server

A Model Context Protocol (MCP) server for WhatsApp Business integration. Send messages and manage WhatsApp Business conversations using WhatsApp's Business API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to WhatsApp with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("WHATSAPP", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run WhatsApp MCP Server
docker run -p 5000:5000 -e API_KEY=your_whatsapp_token \
  ghcr.io/klavis-ai/whatsapp-mcp-server:latest
```

**Access Token Setup:** Get your WhatsApp Business API access token from the [Meta for Developers](https://developers.facebook.com/) platform.

## 🛠️ Available Tools

- **Message Sending**: Send text messages and media to WhatsApp contacts
- **Template Messages**: Use pre-approved message templates
- **Media Handling**: Send images, documents, and other media types
- **Business Profile**: Manage WhatsApp Business profile information
- **Webhook Management**: Handle incoming messages and events

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