# OpenRouter MCP Server

A Model Context Protocol (MCP) server for OpenRouter integration. Access multiple AI models through OpenRouter's unified API interface.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to OpenRouter with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("OPENROUTER", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/openrouter-mcp-server:latest


# Run OpenRouter MCP Server
docker run -p 5000:5000 -e API_KEY=$API_KEY \
  ghcr.io/klavis-ai/openrouter-mcp-server:latest
```

**API Key Setup:** Get your OpenRouter API key from the [OpenRouter Dashboard](https://openrouter.ai/keys).

## 🛠️ Available Tools

- **Model Access**: Access multiple AI models through unified interface
- **Chat Completions**: Generate text responses using various AI models
- **Model Comparison**: Compare outputs from different AI models
- **Usage Analytics**: Track API usage and model performance
- **Cost Management**: Monitor and manage API costs across models

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
