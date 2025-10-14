# Klavis AI - LLM API Documentation

## Overview

Klavis AI is an open-source MCP (Model Context Protocol) integration platform that that let AI agents use any tools reliably at any scale.

**Key Features:**
- 🚀 Instant Integration with Python/TypeScript SDKs or REST API
- 🔐 Built-in OAuth flows and API key management
- 🛠️ 100+ tools across CRM, GSuite, dev tools, sales, search, etc.
- 🌐 Multi-platform LLM provider support (OpenAI, Anthropic, Gemini, etc.)
- Strata: One MCP server for AI agents to use tools progressively at any scale

## Installation

## REST API

**Base URL:** `https://api.klavis.ai`  
**Authentication:** Bearer token (API key in Authorization header)

### Create Strata Server
```bash
curl -X POST https://api.klavis.ai/mcp-server/strata/create \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user_123",
    "servers": ["GitHub", "Linear"]
  }'
```

**Response:**
```json
{
  "strataServerUrl": "https://strata.klavis.ai/mcp/?strata_id=...",
  "strataId": "strata_abc123",
  "addedServers": ["GitHub", "Linear"],
  "oauthUrls": {
    "GitHub": "https://api.klavis.ai/oauth/github/authorize?instance_id=...",
    "Linear": "https://api.klavis.ai/oauth/linear/authorize?instance_id=..."
  }
}
```

### Add Servers to Strata
```bash
curl -X POST https://api.klavis.ai/mcp-server/strata/add \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "strataId": "strata_abc123",
    "servers": ["Slack", "Notion"]
  }'
```

### Get Available Servers
```bash
curl -X GET https://api.klavis.ai/mcp-server/servers \
  -H "Authorization: Bearer YOUR_API_KEY"
```


### Python SDK
```bash
pip install klavis
```

### TypeScript/JavaScript SDK
```bash
npm install klavis
```

### API Key Setup
Sign up at [klavis.ai](https://www.klavis.ai) and create your [API key](https://www.klavis.ai/home/api-keys).

## Quick Start

### Python SDK

```python
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

# Initialize client
klavis_client = Klavis(api_key="your_api_key")

# Create Strata MCP server (aggregates multiple MCP servers)
response = klavis_client.mcp_server.create_strata_server(
    servers=[McpServerName.GITHUB, McpServerName.LINEAR],
    user_id="user_123"
)

# Handle OAuth if needed
if response.oauth_urls:
    for server_name, oauth_url in response.oauth_urls.items():
        print(f"Authorize {server_name}: {oauth_url}")

```

### TypeScript SDK

```typescript
import { Klavis } from 'klavis';

const klavisClient = new Klavis({ apiKey: 'your_api_key' });

// Create Strata MCP server
const response = await klavisClient.mcpServer.createStrataServer({
    servers: [Klavis.McpServerName.Github, Klavis.McpServerName.Linear],
    userId: "user_123"
});
```

## Use Case - OpenAI Integration

```python
import json
from openai import OpenAI
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

openai_client = OpenAI(api_key="openai_key")
klavis_client = Klavis(api_key="klavis_key")

# Create Strata server with multiple services
response = klavis_client.mcp_server.create_strata_server(
    servers=[McpServerName.GMAIL, McpServerName.SLACK],
    user_id="user_123"
)

# Handle OAuth authorization for each service
if response.oauth_urls:
    for server_name, oauth_url in response.oauth_urls.items():
        print(f"Please open this URL to complete {server_name} OAuth authorization: {oauth_url}")

def openai_with_mcp_server(mcp_server_url: str, user_query: str):
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use the available tools to answer the user's question."},
        {"role": "user", "content": user_query}
    ]
    
    tools_info = klavis_client.mcp_server.list_tools(
        server_url=mcp_server_url,
        format=ToolFormat.OPENAI
    )
    
    max_iterations = 20 
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools_info.tools,
            tool_choice="auto",
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"Calling: {tool_name}")
                print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                
                function_result = klavis_client.mcp_server.call_tools(
                    server_url=mcp_server_url,
                    tool_name=tool_name,
                    tool_args=tool_args
                )
                                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(function_result)
                })
            continue
        else:
            messages.append({"role": "assistant", "content": assistant_message.content})
            return assistant_message.content
    
    return "Max iterations reached without final response"

# Run the integration
result = openai_with_mcp_server(
    mcp_server_url=response.strata_server_url, 
    user_query="Check my latest 5 emails and summarize them in a Slack message to #general"
)

print(f"\n🤖 Final Response: {result}")
```

## Strata Server Management

### Add
Add servers to an existing Strata MCP server.
```python
klavis_client.mcp_server.add_servers_to_strata(
    strata_id="strata_abc123",
    servers=[McpServerName.SLACK, McpServerName.NOTION]
)
```

### Remove
Delete servers from an existing Strata MCP server.
```python
klavis_client.mcp_server.delete_servers_from_strata(
    strata_id="strata_abc123",
    servers=["Slack"]
)
```

### Get Strata Info
```python
info = klavis_client.mcp_server.get_strata_instance(
    strata_id="strata_abc123"
)
print(info.connected_servers)  # List of connected servers
print(info.oauth_urls)  # OAuth URLs for authentication
```

## Tool Formats

Klavis supports multiple tool formats for different LLM providers:

- **`openai`** - OpenAI function calling format
- **`anthropic`** - Anthropic Claude tool format
- **`gemini`** - Google Gemini function declarations
- **`mcp_native`** - Standard MCP protocol format


## Environment Variables

```bash
KLAVIS_API_KEY=your_klavis_api_key
```

## Best Practices

1. **Use Strata Servers**: Aggregate ond or multiple MCP servers into one endpoint for easier management
2. **Handle OAuth Gracefully**: Direct users to OAuth URLs and wait for completion
3. **Reuse Connections**: Create Strata servers once per user and reuse them
5. **Secure API Keys**: Use environment variables and never commit keys to version control

## Support & Resources

- **Documentation**: [docs.klavis.ai](https://docs.klavis.ai)
- **OpenAPI** [klavis](https://api.klavis.ai/openapi.json)
- **Website**: [klavis.ai](https://www.klavis.ai)
- **PyPI**: [klavis](https://pypi.org/project/klavis/)
- **npm**: [klavis](https://www.npmjs.com/package/klavis)

