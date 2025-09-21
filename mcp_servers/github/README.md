# GitHub MCP Server

A Model Context Protocol (MCP) server for GitHub integration. Interact with repositories, manage issues, search code, and more using GitHub's API through the standardized MCP interface.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to GitHub with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("GITHUB", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/github-mcp-server:latest


# Run GitHub MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/github-mcp-server:latest

# Run GitHub MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"ghp_your_github_token_here"}' \
  ghcr.io/klavis-ai/github-mcp-server:latest
```

**OAuth Setup:** For OAuth authentication (recommended), use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys). This handles the complex OAuth flow automatically.

**Manual Setup:** Alternatively, provide your GitHub Personal Access Token directly via `AUTH_DATA`.

## 🛠️ Available Tools

- **Repository Management**: Get repository info, list files, read content
- **Issue Management**: Create, read, update issues and comments  
- **Pull Requests**: Manage PRs, reviews, and merges
- **Search**: Search repositories, code, issues, and users
- **User Operations**: Get user profiles and organization info

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [docs.klavis.ai](https://docs.klavis.ai) |
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
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>
