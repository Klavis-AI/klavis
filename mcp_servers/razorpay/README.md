# Razorpay MCP Server

A Model Context Protocol (MCP) server for comprehensive Razorpay integration. Manage payments, orders, customers, and much more using Razorpay's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Razorpay with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("RAZORPAY", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

This server is designed to be run as a self-hosted Docker container.

```bash
# Pull the latest image (once published to ghcr.io)
docker pull ghcr.io/klavis-ai/razorpay-mcp-server:latest


# Run the Razorpay MCP Server (No Auth)
docker run --rm -i \
  -e RAZORPAY_API_ID=$YOUR_RAZORPAY_KEY_ID \
  -e RAZORPAY_API_SECRET=$YOUR_RAZORPAY_KEY_SECRET \
  ghcr.io/klavis-ai/razorpay-mcp-server:latest
```

**Authentication Setup:** Razorpay uses an **API Key ID** and **Key Secret** for authentication. You must generate these from your Razorpay Dashboard under `Settings -> API Keys`. These keys must be provided as environment variables (`RAZORPAY_API_ID` and `RAZORPAY_API_SECRET`) when running the container.

*Note: This server communicates via `stdio` and does not use a network port, so no port mapping (`-p`) is required.*

## 🛠️ Available Tools

- **Order Management**: Create, fetch, update, and view payments for orders.
- **Customer Management**: Create, list, edit, and retrieve individual customers.
- **Payment Processing**: Fetch, capture, and update payments, including retrieving card details.
- **Payment Links & QR Codes**: Create and manage sharable payment links and UPI QR codes.
- **Account & Document Management**: Monitor payment gateway downtimes and manage uploaded documents.

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