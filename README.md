<div align="center">
  <picture>
    <img src="https://raw.githubusercontent.com/klavis-ai/klavis/main/static/klavis-ai.png" width="80">
  </picture>
</div>

<h1 align="center">Klavis AI - open source MCP integrations for AI Applications</h1>

<div align="center">

[![Documentation](https://img.shields.io/badge/Documentation-📖-green)](https://docs.klavis.ai)
[![Website](https://img.shields.io/badge/Website-🌐-purple)](https://www.klavis.ai)
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white)](https://discord.gg/p7TuTEcssn)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/klavis.svg)](https://pypi.org/project/klavis/)
[![npm](https://img.shields.io/npm/v/klavis.svg)](https://www.npmjs.com/package/klavis)

</div>

## What is Klavis AI?

Klavis AI is open source MCP integrations for AI Applications. Our API provides hosted, secure MCP servers, eliminating auth management and client-side code.
## ✨ Key Features

- **🚀 Instant Integration**: Get started in minutes with our Python and TypeScript SDKs, or simply REST API
- **🔐 Built-in Authentication**: Secure OAuth flows and API key management
- **⚡ Production-Ready**: Hosted infrastructure that scales to millions of users
- **🛠️ 100+ Tools**: Access to CRM, GSuite, Github, Slack, databases, and many more
- **🌐 Multi-Platform**: Works with any LLM provider (OpenAI, Anthropic, Gemini, etc.) and any AI agent framework (LangChain, Llamaindex, CrewAI, AutoGen, etc.)
- **🔧 Self-Hostable**: Open-source MCP servers you can run yourself

## 🚀 Quick Start

### Installation

**Python**
```bash
pip install klavis
```

**TypeScript/JavaScript**
```bash
npm install klavis
```

#### Get Your API Key

Sign up at [klavis.ai](https://www.klavis.ai) and create your [API key](https://www.klavis.ai/home/api-keys).

## With MCP Client

If you already have an MCP client implementation in your codebase:

**Python Example**
```python
from klavis import Klavis
from klavis.types import McpServerName, ConnectionType

klavis_client = Klavis(api_key="your-klavis-key")

# Create a YouTube MCP server instance
youtube_server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="user123", # Change to user id in your platform
    platform_name="MyApp" # change to your platform
)

print(f"Server created: {youtube_server.server_url}")
```

**TypeScript Example**
```typescript
import { KlavisClient, Klavis } from 'klavis';

const klavisClient = new KlavisClient({ apiKey: 'your-klavis-key' });

// Create Gmail MCP server with OAuth
const gmailServer = await klavisClient.mcpServer.createServerInstance({
    serverName: Klavis.McpServerName.Gmail,
    userId: "user123",
    platformName: "MyApp"
});

// Gmail needs OAuth flow
await window.open(gmailServer.oauthUrl);
```

## Without MCP Client (Function Calling)

Integrate directly with your LLM provider or AI agent framework using function calling:

**Python + OpenAI Example**
```python
import json
from openai import OpenAI
from klavis import Klavis
from klavis.types import McpServerName, ConnectionType, ToolFormat

OPENAI_MODEL = "gpt-4o-mini"

openai_client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
klavis_client = Klavis(api_key="YOUR_KLAVIS_API_KEY")

# Create server instance
youtube_server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="user123",
    platform_name="MyApp"
)

# Get available tools in OpenAI format
tools = klavis_client.mcp_server.list_tools(
    server_url=youtube_server.server_url,
    format=ToolFormat.OPENAI,
)

# Initial conversation
messages = [{"role": "user", "content": "Summarize this video: https://youtube.com/watch?v=..."}]

# First OpenAI call with function calling
response = openai_client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=messages,
    tools=tools.tools
)

messages.append(response.choices[0].message)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = klavis_client.mcp_server.call_tools(
            server_url=youtube_server.server_url,
            tool_name=tool_call.function.name,
            tool_args=json.loads(tool_call.function.arguments),
        )
        
        # Add tool result to conversation
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

# Second OpenAI call to process tool results and generate final response
final_response = openai_client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=messages
)

print(final_response.choices[0].message.content)
```

**TypeScript + OpenAI Example**
```typescript
import OpenAI from 'openai';
import { KlavisClient, Klavis } from 'klavis';

// Constants
const OPENAI_MODEL = "gpt-4o-mini";

const EMAIL_RECIPIENT = "john@example.com";
const EMAIL_SUBJECT = "Hello from Klavis";
const EMAIL_BODY = "This email was sent using Klavis MCP Server!";

const openaiClient = new OpenAI({ apiKey: 'your-openai-key' });
const klavisClient = new KlavisClient({ apiKey: 'your-klavis-key' });

// Create server and get tools
const gmailServer = await klavisClient.mcpServer.createServerInstance({
    serverName: Klavis.McpServerName.Gmail,
    userId: "user123",
    platformName: "MyApp"
});

// Handle OAuth authentication for Gmail
if (gmailServer.oauthUrl) {
    console.log("Please complete OAuth authorization:", gmailServer.oauthUrl);
    await window.open(gmailServer.oauthUrl);
}

const tools = await klavisClient.mcpServer.listTools({
    serverUrl: gmailServer.serverUrl,
    format: Klavis.ToolFormat.Openai
});

// Initial conversation
const messages = [{ 
    role: "user", 
    content: `Please send an email to ${EMAIL_RECIPIENT} with subject "${EMAIL_SUBJECT}" and body "${EMAIL_BODY}"` 
}];

// First OpenAI call with function calling
const response = await openaiClient.chat.completions.create({
    model: OPENAI_MODEL,
    messages: messages,
    tools: tools.tools
});

messages.push(response.choices[0].message);

// Handle tool calls
if (response.choices[0].message.tool_calls) {
    for (const toolCall of response.choices[0].message.tool_calls) {
        const result = await klavisClient.mcpServer.callTools({
            serverUrl: gmailServer.serverUrl,
            toolName: toolCall.function.name,
            toolArgs: JSON.parse(toolCall.function.arguments)
        });
        
        // Add tool result to conversation
        messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            content: JSON.stringify(result)
        });
    }
}

// Second OpenAI call to process tool results and generate final response
const finalResponse = await openaiClient.chat.completions.create({
    model: OPENAI_MODEL,
    messages: messages
});

console.log(finalResponse.choices[0].message.content);
```

## 📚 AI Platform Integration Tutorials

- **[AI Platform Integrations Overview](https://docs.klavis.ai/documentation/integrations/overview)** - Learn how to integrate with leading AI platforms
- **[Together AI Integration](https://docs.klavis.ai/documentation/integrations/together-ai)** - Build AI agents with Together AI's high-performance LLMs
- **[OpenAI Integration](https://docs.klavis.ai/documentation/integrations/open-ai)** - Create fast and efficient AI agents with OpenAI and Klavis MCP Servers
- And More!

## 🛠️ Available MCP Servers

[**View All Servers →**](https://docs.klavis.ai/documentation/introduction#mcp-server-quickstart)

## 🗺️ Roadmap

We're constantly expanding our MCP server ecosystem. Here are the upcoming integrations planned for release:
### AI platform Integration
Add more [examples](https://github.com/Klavis-AI/klavis/tree/main/examples) & [docs](https://docs.klavis.ai/documentation/ai-platform-integration/overview) for integrating popular AI platforms and LLMs with the Klavis AI SDK

### CRM & Sales
- **Greenhouse** - Applicant tracking system
- **Monday.com** - Work management platform
- **Zendesk** - Customer service platform

### Microsoft Ecosystem
- **Microsoft Teams** - Team collaboration and communication
- **Microsoft Outlook** - Email and calendar management  
- **OneDrive** - Cloud storage and file sharing

### Professional Networks & Communication
- **LinkedIn** - Professional networking platform

### File Storage & Productivity
- **Dropbox** - Cloud file storage and synchronization

### Scheduling & Calendar
- **Cal.com** - Open-source scheduling platform

### Testing & Quality Assurance
- Add Unit Tests, integration test for each MCP Servers

### Documentation & Updates
- **/docs** - Enhanced documentation and guides

*Want to see a specific integration? [Let us know](https://discord.gg/p7TuTEcssn) or [contribute](CONTRIBUTING.md) to help build it!*

## 🔧 Authentication & Multi-Tool Workflows

### Authentication

Many MCP servers require authentication. Klavis handles this seamlessly:

```python
# For OAuth services (Gmail, Google Drive, etc.)
server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.GMAIL,
    user_id="user123",
    platform_name="MyApp"
)
# Option 1 - OAuth URL is provided in server.oauth_url, redirect user to OAuth URL for authentication
import webbrowser
webbrowser.open(server.oauth_url)

# Option 2 - or for API key services
klavis_client.mcp_server.set_auth_token(
    instance_id=server.instance_id,
    auth_token="your-service-api-key"
)
```

### Multi-Tool Workflows

Combine multiple MCP servers for complex workflows:

```python
# Create multiple servers
github_server = klavis_client.mcp_server.create_server_instance(...)
slack_server = klavis_client.mcp_server.create_server_instance(...)

# Use tools from both servers in a single AI conversation
all_tools = []
all_tools.extend(klavis_client.mcp_server.list_tools(github_server.server_url).tools)
all_tools.extend(klavis_client.mcp_server.list_tools(slack_server.server_url).tools)

# Initialize conversation
messages = [{"role": "user", "content": "Create a GitHub issue and notify the team on Slack"}]

# Loop to let LLM work with multiple tools
max_iterations = 5
for iteration in range(max_iterations):
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=all_tools
    )
    
    messages.append(response.choices[0].message)
    
    # Check if LLM wants to use tools
    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            # Determine which server to use based on tool name
            server_url = github_server.server_url if "github" in tool_call.function.name else slack_server.server_url
            
            # Execute tool
            result = klavis_client.mcp_server.call_tools(
                server_url=server_url,
                tool_name=tool_call.function.name,
                tool_args=json.loads(tool_call.function.arguments)
            )
            
            # Add tool result to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    else:
        # LLM finished the task
        print(f"Task completed in {iteration + 1} iterations")
        print(response.choices[0].message.content)
        break
```

## 🏠 Self-Hosting

Want to run MCP servers yourself? All our servers are open-source:

```bash
# Clone the repository
git clone https://github.com/klavis-ai/klavis.git
cd klavis

# Run a specific MCP server
cd mcp_servers/github
docker build -t klavis-github .
docker run -p 8000:8000 klavis-github
```

### MCP Clients

Build custom integrations with our MCP clients:

- **[Discord Bot](mcp-clients/README-Discord.md)** - Deploy AI bots to Discord
- **[Slack Bot](mcp-clients/README-Slack.md)** - Create Slack AI assistants  
- **[Web Interface](mcp-clients/README-Web.md)** - Browser-based AI chat
- **[WhatsApp Bot](mcp-clients/README-WhatsApp.md)** - WhatsApp AI integration

## 📖 Documentation

- **[API Documentation](https://docs.klavis.ai)** - Complete API reference
- **[SDK Documentation](https://docs.klavis.ai/sdks)** - Python & TypeScript guides
- **[MCP Protocol Guide](https://docs.klavis.ai/mcp)** - Understanding MCP
- **[Authentication Guide](https://docs.klavis.ai/auth)** - OAuth and API keys

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Report Issues**: Found a bug? [Open an issue](https://github.com/klavis-ai/klavis/issues)
2. **Request Features**: Have an idea? [Start a discussion](https://github.com/klavis-ai/klavis/discussions)
3. **Contribute Code**: Check our [Contributing Guidelines](CONTRIBUTING.md)
4. **Join Community**: Connect with us on [Discord](https://discord.gg/p7TuTEcssn)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p><strong>Ready to supercharge your AI applications?</strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Started</a> •
    <a href="https://docs.klavis.ai">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a> •
    <a href="examples/">Examples</a>
  </p>
</div>
