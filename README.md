<div align="center">
  <picture>
    <img src="https://raw.githubusercontent.com/klavis-ai/klavis/main/static/klavis-ai.png" width="80">
  </picture>
</div>

<h1 align="center">Klavis AI - Production-Ready MCP Servers</h1>
<p align="center"><strong>🌐 Hosted MCP Service | 🐳 Self-Hosted Solutions | 🔐 Enterprise OAuth</strong></p>

<div align="center">

[![Documentation](https://img.shields.io/badge/Documentation-📖-green)](https://docs.klavis.ai)
[![Website](https://img.shields.io/badge/Website-🌐-purple)](https://www.klavis.ai)
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white)](https://discord.gg/p7TuTEcssn)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker Images](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/orgs/klavis-ai/packages)

</div>

## 🚀 Quick Start - Run Any MCP Server in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to 50+ MCP servers with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("GMAIL", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Run Gmail MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=your_key \
  ghcr.io/klavis-ai/gmail-mcp-server:latest

# Run GitHub MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"ghp_your_github_token_here"}' \
  ghcr.io/klavis-ai/github-mcp-server:latest
```

### 🖥️ Cursor Configuration

**For Cursor, use our hosted service URLs directly - no Docker setup needed:**

```json
{
  "mcpServers": {
    "klavis-gmail": {
      "url": "https://gmail-mcp-server.klavis.ai/mcp/?instance_id=your-instance"
    },
    "klavis-github": {
      "url": "https://github-mcp-server.klavis.ai/mcp/?instance_id=your-instance"
    }
  }
}
```

**💡 Get your personalized configuration instantly:**

1. **🔗 [Visit our MCP Servers page →](https://www.klavis.ai/home/mcp-servers)**
2. **Select any service** (Gmail, GitHub, Slack, etc.)  
3. **Copy the generated configuration** for your tool
4. **Paste into Claude Desktop config** - done!

## ✨ Enterprise-Grade MCP Infrastructure

- **🌐 Hosted Service**: Production-ready managed infrastructure with 99.9% uptime SLA
- **🔐 Enterprise OAuth**: Seamless authentication for Google, GitHub, Slack, Salesforce, etc.
- **🛠️ 50+ Integrations**: CRM, productivity tools, databases, social media, and more
- **🚀 Instant Deployment**: Zero-config setup for Claude Desktop, VS Code, Cursor
- **🏢 Enterprise Ready**: SOC2 compliant, GDPR ready, with dedicated support
- **📖 Open Source**: Full source code available for customization and self-hosting

## 🎯 Self Hosting Instructions

### 1. 🐳 Docker Images (Fastest Way to Start)

Perfect for trying out MCP servers or integrating with AI tools like Claude Desktop.

**Available Images:**
- `ghcr.io/klavis-ai/{server-name}-mcp-server:latest` - Basic server
- `ghcr.io/klavis-ai/{server-name}-mcp-server:latest` - With OAuth support

[**🔍 Browse All Docker Images →**](https://github.com/orgs/Klavis-AI/packages?repo_name=klavis)

```bash
# Example: GitHub MCP Server
docker run -p 5000:5000 ghcr.io/klavis-ai/github-mcp-server:latest

# Example: Gmail with OAuth (requires API key)
docker run -it -e KLAVIS_API_KEY=your_key \
  ghcr.io/klavis-ai/gmail-mcp-server:latest
```

[**🔗 Get Free API Key →**](https://www.klavis.ai/home/api-keys)

### 2. 🏗️ Build from Source

Clone and run any MCP server locally (with or without Docker):

```bash
git clone https://github.com/klavis-ai/klavis.git
cd klavis/mcp_servers/github

# Option A: Using Docker
docker build -t github-mcp .
docker run -p 5000:5000 github-mcp

# Option B: Run directly (Go example)
go mod download
go run server.go

# Option C: Python servers  
cd ../youtube
pip install -r requirements.txt
python server.py

# Option D: Node.js servers
cd ../slack  
npm install
npm start
```

Each server includes detailed setup instructions in its individual README.

Use our managed infrastructure - no Docker required:

```bash
pip install klavis  # or npm install klavis
```

## 🛠️ Available MCP Servers

| Service | Docker Image | OAuth Required | Description |
|---------|--------------|----------------|-------------|
| **GitHub** | `ghcr.io/klavis-ai/github-mcp-server` | ✅ | Repository management, issues, PRs |
| **Gmail** | `ghcr.io/klavis-ai/gmail-mcp-server:latest` | ✅ | Email reading, sending, management |
| **Google Sheets** | `ghcr.io/klavis-ai/google_sheets-mcp-server:latest` | ✅ | Spreadsheet operations |
| **YouTube** | `ghcr.io/klavis-ai/youtube-mcp-server` | ❌ | Video information, search |
| **Slack** | `ghcr.io/klavis-ai/slack-mcp-server:latest` | ✅ | Channel management, messaging |
| **Notion** | `ghcr.io/klavis-ai/notion-mcp-server:latest` | ✅ | Database and page operations |
| **Salesforce** | `ghcr.io/klavis-ai/salesforce-mcp-server:latest` | ✅ | CRM data management |
| **Postgres** | `ghcr.io/klavis-ai/postgres-mcp-server` | ❌ | Database operations |
| ... | ... | ...| ... |

And more! 
[**🔍 View All 50+ Servers →**](https://docs.klavis.ai/documentation/introduction#mcp-server-quickstart) | [**🐳 Browse Docker Images →**](https://github.com/orgs/Klavis-AI/packages?repo_name=klavis)

## 💡 Usage Examples

For existing MCP implementations:

**Python**
```python
from klavis import Klavis

klavis = Klavis(api_key="your-key")
server = klavis.mcp_server.create_server_instance(
    server_name="YOUTUBE",
    user_id="user123"
)
```

**TypeScript**
```typescript
import { KlavisClient } from 'klavis';

const klavis = new KlavisClient({ apiKey: 'your-key' });
const server = await klavis.mcpServer.createServerInstance({
    serverName: "Gmail",
    userId: "user123"
});
```

### With AI Frameworks

**OpenAI Function Calling**
```python
from openai import OpenAI
from klavis import Klavis

klavis = Klavis(api_key="your-key")
openai = OpenAI(api_key="your-openai-key")

# Create server and get tools
server = klavis.mcp_server.create_server_instance("YOUTUBE", "user123")
tools = klavis.mcp_server.list_tools(server.server_url, format="OPENAI")

# Use with OpenAI
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize this video: https://..."}],
    tools=tools.tools
)
```

[**📖 View Complete Examples →**](examples/)

## 🌐 Hosted MCP Service - Zero Setup Required

**Perfect for individuals and businesses who want instant access without infrastructure complexity:**

### ✨ **Why Choose Our Hosted Service:**
- **🚀 Instant Setup**: Get any MCP server running in 30 seconds
- **🔐 OAuth Handled**: No complex authentication setup required  
- **🏗️ No Infrastructure**: Everything runs on our secure, scalable cloud
- **📈 Auto-Scaling**: From prototype to production seamlessly
- **🔄 Always Updated**: Latest MCP server versions automatically
- **💰 Cost-Effective**: Pay only for what you use, free tier available

### 💻 **Quick Integration:**

```python
from klavis import Klavis

# Get started with just an API key
klavis = Klavis(api_key="your-free-key")

# Create any MCP server instantly
gmail_server = klavis.mcp_server.create_server_instance(
    server_name="GMAIL",
    user_id="your-user-id"
)

# Server is ready to use immediately
print(f"Gmail MCP server ready: {gmail_server.server_url}")
```

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)** | **📖 [Complete Documentation →](https://docs.klavis.ai)**

## 🔐 OAuth Authentication (For OAuth-Enabled Servers)

Some servers require OAuth authentication (Google, GitHub, Slack, etc.). OAuth implementation requires significant setup and code complexity:

```bash
# Run with OAuth support (requires free API key)
docker run -it -e KLAVIS_API_KEY=your_free_key \
  ghcr.io/klavis-ai/gmail-mcp-server:latest

# Follow the displayed URL to authenticate
# Server starts automatically after authentication
```

**Why OAuth needs additional implementation?**
- 🔧 **Complex Setup**: Each service requires creating OAuth apps with specific redirect URLs, scopes, and credentials
- 📝 **Implementation Overhead**: OAuth 2.0 flow requires callback handling, token refresh, and secure storage
- 🔑 **Credential Management**: Managing multiple OAuth app secrets across different services
- 🔄 **Token Lifecycle**: Handling token expiration, refresh, and error cases

Our OAuth wrapper simplifies this by handling all the complex OAuth implementation details, so you can focus on using the MCP servers directly.

**Alternative**: For advanced users, you can implement OAuth yourself by creating apps with each service provider. Check individual server READMEs for technical details.

## 📚 Resources & Community

| Resource | Link | Description |
|----------|------|-------------|
| **📖 Documentation** | [docs.klavis.ai](https://docs.klavis.ai) | Complete guides and API reference |
| **💬 Discord** | [Join Community](https://discord.gg/p7TuTEcssn) | Get help and connect with users |
| **🐛 Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) | Report bugs and request features |
| **📦 Examples** | [examples/](examples/) | Working examples with popular AI frameworks |
| **🔧 Server Guides** | [mcp_servers/](mcp_servers/) | Individual server documentation |

## 🤝 Contributing

We love contributions! Whether you want to:
- 🐛 Report bugs or request features
- 📝 Improve documentation  
- 🔧 Build new MCP servers
- 🎨 Enhance existing servers

Check out our [Contributing Guide](CONTRIBUTING.md) to get started!

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
  <p><strong>🚀 Supercharge AI Applications </strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a> •
    <a href="examples/">Examples</a>
  </p>
</div>
