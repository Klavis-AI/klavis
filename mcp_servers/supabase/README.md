# Supabase MCP Server

A Model Context Protocol (MCP) server for Supabase integration. Manage database operations, authentication, and real-time subscriptions using Supabase's API.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Supabase with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("SUPABASE", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Supabase MCP Server
docker run -p 5000:5000 \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_KEY=your_supabase_anon_key \
  ghcr.io/klavis-ai/supabase-mcp-server:latest
```

**Setup:** Get your Supabase URL and anon key from your [Supabase project dashboard](https://app.supabase.com/).

## 🛠️ Available Tools

- **Database Operations**: Query, insert, update, and delete data
- **Authentication**: User management and authentication flows
- **Real-time**: Subscribe to database changes and real-time updates
- **Storage**: File upload and storage management
- **Functions**: Invoke Supabase Edge Functions

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