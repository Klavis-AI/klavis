# Stripe MCP Server

A Model Context Protocol (MCP) server for Stripe integration. Manage payments, customers, and billing using Stripe's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Stripe with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("STRIPE", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Stripe MCP Server
docker run -p 5000:5000 -e STRIPE_API_KEY=your_stripe_secret_key \
  ghcr.io/klavis-ai/stripe-mcp-server:latest
```

**API Key Setup:** Get your Stripe secret key from the [Stripe Dashboard](https://dashboard.stripe.com/apikeys).

## 🛠️ Available Tools

- **Payment Processing**: Create and manage payment intents and charges
- **Customer Management**: Manage customer records and payment methods
- **Subscription Handling**: Create and manage recurring subscriptions
- **Invoice Operations**: Generate and manage invoices
- **Financial Reporting**: Access transaction history and analytics

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
