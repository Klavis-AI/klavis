# Klavis AI - LLM API Documentation

## Overview

Klavis AI is an open-source MCP (Model Context Protocol) integration platform that provides hosted, secure MCP servers for AI applications. It eliminates authentication management and client-side code complexity while offering 100+ tools for various business platforms.

**Key Features:**
- 🚀 Instant Integration with Python/TypeScript SDKs or REST API
- 🔐 Built-in OAuth flows and API key management
- ⚡ Production-ready hosted infrastructure
- 🛠️ 100+ tools across CRM, productivity, development platforms
- 🌐 Multi-platform LLM support (OpenAI, Anthropic, Gemini, etc.)
- 🔧 Self-hostable open-source MCP servers

## Installation

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

## Core API Usage

### Python SDK

```python
import klavis
from klavis import McpServerName, ToolFormat

# Initialize client
klavis_client = klavis.Client(api_key="your_api_key")

# Create MCP server instance
server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.YOUTUBE,
    user_id="user123",
    platform_name="MyApp"
)

# List available tools
tools = klavis_client.mcp_server.list_tools(
    server_url=server.server_url,
    format=ToolFormat.OPENAI
)

# Execute tool
result = klavis_client.mcp_server.call_tools(
    server_url=server.server_url,
    tool_name="search_videos",
    tool_args={"query": "AI tutorials", "max_results": 10}
)
```

### TypeScript SDK

```typescript
import { Klavis } from 'klavis';

// Initialize client
const klavisClient = new Klavis.Client({ apiKey: 'your_api_key' });

// Create MCP server instance
const server = await klavisClient.mcpServer.createServerInstance({
    serverName: Klavis.McpServerName.Youtube,
    userId: "user123",
    platformName: "MyApp"
});

// List available tools
const tools = await klavisClient.mcpServer.listTools({
    serverUrl: server.serverUrl,
    format: Klavis.ToolFormat.Openai
});

// Execute tool
const result = await klavisClient.mcpServer.callTools({
    serverUrl: server.serverUrl,
    toolName: "search_videos",
    toolArgs: { query: "AI tutorials", maxResults: 10 }
});
```

## REST API

**Base URL:** `https://api.klavis.ai`
**Authentication:** Bearer token (API key)

### Core Endpoints

#### Create Server Instance
```http
POST /mcp-server/instance/create
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "serverName": "youtube",
  "userId": "user123",
  "platformName": "MyApp"
}
```

#### List Tools
```http
POST /mcp-server/list-tools
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "serverUrl": "server_url_from_create_response",
  "format": "openai"
}
```

#### Call Tool
```http
POST /mcp-server/call-tool
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "serverUrl": "server_url_from_create_response",
  "toolName": "search_videos",
  "toolArgs": {
    "query": "AI tutorials",
    "max_results": 10
  }
}
```


## Available MCP Servers

### CRM & Sales

#### Salesforce
- **Purpose**: CRM and sales management
- **Tools**: Accounts, Contacts, Opportunities, Leads, Cases, Campaigns
- **Key Functions**: `get_accounts`, `create_contact`, `update_opportunity`, `convert_lead`

#### HubSpot
- **Purpose**: Marketing, sales, and service CRM
- **Tools**: Properties, Contacts, Companies, Deals, Tickets
- **Key Functions**: `hubspot_get_contacts`, `hubspot_create_contact`, `hubspot_get_companies`

#### Close
- **Purpose**: Sales CRM and lead management
- **Tools**: Leads, Contacts, Opportunities, Tasks, Users
- **Key Functions**: Lead and contact management, opportunity tracking

#### Affinity
- **Purpose**: Relationship intelligence and CRM
- **Tools**: Lists, Persons, Companies, Opportunities, Notes
- **Key Functions**: `get_all_persons`, `search_organizations`, `get_all_opportunities`

### Project Management

#### Asana
- **Purpose**: Project and task management
- **Tools**: Tasks, Projects, Workspaces, Users, Teams, Tags
- **Key Functions**: Task and project management across workspaces

#### Linear
- **Purpose**: Issue tracking and project management
- **Tools**: Teams, Issues, Projects, Comments
- **Key Functions**: `get_issues`, `create_issue`, `update_issue`, `search_issues`

#### ClickUp
- **Purpose**: Project management and task tracking
- **Tools**: Teams, Workspaces, Spaces, Folders, Lists, Tasks, Comments
- **Key Functions**: `get_tasks`, `create_task`, `update_task`, `search_tasks`

#### Motion
- **Purpose**: AI-powered calendar and task management
- **Tools**: Tasks, Projects, Comments, Users, Workspaces
- **Key Functions**: `get_tasks`, `create_task`, `get_projects`, `create_project`

#### Monday
- **Purpose**: Work management platform
- **Tools**: Boards, Items, Columns, Users
- **Implementation**: TypeScript-based

### Communication

#### Gmail
- **Purpose**: Email management
- **Tools**: Email sending, reading, searching, management
- **Implementation**: TypeScript-based

#### Slack
- **Purpose**: Team communication
- **Tools**: Messaging, channels, users, files
- **Implementation**: TypeScript-based

#### Discord
- **Purpose**: Communication and community management
- **Tools**: Server management, messaging, user management

#### WhatsApp
- **Purpose**: Messaging integration
- **Tools**: Message sending and management

### Google Workspace

#### Google Calendar
- **Purpose**: Calendar management
- **Tools**: Event creation, scheduling, calendar management

#### Google Docs
- **Purpose**: Document management
- **Tools**: Document creation, editing, sharing

#### Google Drive
- **Purpose**: File storage and management
- **Tools**: File upload, download, sharing, organization

#### Google Sheets
- **Purpose**: Spreadsheet management
- **Tools**: Sheet creation, data manipulation, formula management

#### Google Slides
- **Purpose**: Presentation management
- **Tools**: Slide creation, editing, presentation management

### Development & Documentation

#### GitHub
- **Purpose**: Version control and repository management
- **Tools**: Repository management, issues, pull requests, commits
- **Implementation**: Go-based

#### Jira
- **Purpose**: Issue tracking and project management
- **Tools**: Issue management, project tracking, workflow management
- **Implementation**: TypeScript-based

#### Confluence
- **Purpose**: Documentation and knowledge management
- **Tools**: Page creation, content management, space organization

#### Notion
- **Purpose**: Note-taking and documentation
- **Tools**: Page management, database operations, content creation
- **Implementation**: TypeScript-based with OpenAPI integration

### Data & Analytics

#### Airtable
- **Purpose**: Database and spreadsheet management
- **Tools**: Bases, Tables, Records, Fields
- **Key Functions**: `list_records`, `create_records`, `update_records`, `delete_records`

#### Gong
- **Purpose**: Revenue intelligence and call analytics
- **Tools**: Transcripts, Calls
- **Key Functions**: `get_transcripts_by_user`, `list_calls`, `add_new_call`

#### Postgres
- **Purpose**: Database management
- **Tools**: SQL operations, database management
- **Implementation**: TypeScript-based

#### Supabase
- **Purpose**: Backend-as-a-Service
- **Tools**: Database operations, authentication, storage
- **Implementation**: TypeScript-based


### Content & Media

#### YouTube
- **Purpose**: Video platform integration
- **Tools**: Video search, channel management, analytics

#### Figma
- **Purpose**: Design collaboration
- **Tools**: Design file access, component management, collaboration
- **Implementation**: TypeScript-based

#### WordPress
- **Purpose**: Content management system
- **Tools**: Post management, page creation, media handling

### E-commerce & Payments

#### Shopify
- **Purpose**: E-commerce platform integration
- **Tools**: Product management, order processing, customer management
- **Implementation**: TypeScript-based

#### Stripe
- **Purpose**: Payment processing
- **Tools**: Payment management, subscription handling, customer management

### Utilities & Services

#### Resend
- **Purpose**: Email delivery
- **Tools**: Email sending, template management
- **Implementation**: TypeScript-based

#### Perplexity
- **Purpose**: AI search integration
- **Tools**: Search queries, AI-powered research
- **Implementation**: TypeScript-based

#### Firecrawl
- **Purpose**: Web scraping and research
- **Tools**: Web page crawling, content extraction
- **Implementation**: TypeScript-based

#### Cloudflare
- **Purpose**: CDN and security services
- **Tools**: DNS management, security configuration
- **Implementation**: TypeScript-based with GraphQL

#### Pandoc
- **Purpose**: Document conversion
- **Tools**: Format conversion, document processing

#### Markitdown
- **Purpose**: Markdown processing
- **Tools**: Markdown conversion and processing

#### Report Generation
- **Purpose**: Automated reporting
- **Tools**: Report creation, data visualization

## AI Platform Integrations

### OpenAI Integration
```python
import openai
from klavis import McpServerName, ToolFormat

# Get tools in OpenAI format
tools = klavis_client.mcp_server.list_tools(
    server_url=server.server_url,
    format=ToolFormat.OPENAI
)

# Use with OpenAI function calling
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Search for AI tutorials on YouTube"}],
    tools=tools,
    tool_choice="auto"
)

# Execute tool calls
for tool_call in response.choices[0].message.tool_calls:
    result = klavis_client.mcp_server.call_tools(
        server_url=server.server_url,
        tool_name=tool_call.function.name,
        tool_args=json.loads(tool_call.function.arguments)
    )
```

### Anthropic Claude Integration
```python
import anthropic
from klavis import ToolFormat

# Get tools in Anthropic format
tools = klavis_client.mcp_server.list_tools(
    server_url=server.server_url,
    format=ToolFormat.ANTHROPIC
)

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[{"role": "user", "content": "Help me manage my tasks"}]
)
```

### Google Gemini Integration
```python
import google.generativeai as genai
from klavis import ToolFormat

# Get tools in Gemini format
tools = klavis_client.mcp_server.list_tools(
    server_url=server.server_url,
    format=ToolFormat.GEMINI
)

model = genai.GenerativeModel('gemini-pro', tools=tools)
response = model.generate_content("Search for project management videos")
```

### CrewAI Framework Integration
```python
from crewai import Agent, Task, Crew
from klavis import McpServerName

# Create specialized agents with Klavis tools
youtube_agent = Agent(
    role='YouTube Analyst',
    goal='Search and analyze YouTube content',
    backstory='Expert in finding relevant video content',
    tools=klavis_youtube_tools
)

email_agent = Agent(
    role='Email Specialist', 
    goal='Manage email communications',
    backstory='Handles email operations efficiently',
    tools=klavis_gmail_tools
)

# Define tasks
search_task = Task(
    description='Search for AI tutorial videos',
    agent=youtube_agent
)

email_task = Task(
    description='Send summary email with video recommendations',
    agent=email_agent
)

# Create and run crew
crew = Crew(
    agents=[youtube_agent, email_agent],
    tasks=[search_task, email_task],
    verbose=True
)

result = crew.kickoff()
```


## MCP Client Implementations

### Available Clients

#### Discord Bot
```python
from mcp_clients import DiscordBot

bot = DiscordBot(
    token="discord_bot_token",
    klavis_api_key="your_klavis_key"
)
bot.run()
```

#### Slack Bot
```python
from mcp_clients import SlackBot

bot = SlackBot(
    token="slack_bot_token",
    klavis_api_key="your_klavis_key"
)
bot.run()
```

#### Web Bot
```python
from mcp_clients import WebBot

bot = WebBot(
    klavis_api_key="your_klavis_key",
    port=8000
)
bot.run()
```

#### WhatsApp Bot
```python
from mcp_clients import WhatsAppBot

bot = WhatsAppBot(
    klavis_api_key="your_klavis_key",
    whatsapp_config=config
)
bot.run()
```

### LLM Provider Support

#### OpenAI Integration
```python
from mcp_clients.llms import OpenAIProvider

provider = OpenAIProvider(
    api_key="openai_key",
    model="gpt-4"
)
```

#### Anthropic Integration
```python
from mcp_clients.llms import AnthropicProvider

provider = AnthropicProvider(
    api_key="anthropic_key",
    model="claude-3-sonnet-20240229"
)
```

## Authentication & OAuth

### OAuth Flow
```python
# Create server instance (returns OAuth URL if needed)
server = klavis_client.mcp_server.create_server_instance(
    server_name=McpServerName.GMAIL,
    user_id="user123",
    platform_name="MyApp"
)

if server.oauth_url:
    print(f"Please authorize: {server.oauth_url}")
    # User completes OAuth flow in browser
    # Klavis handles token storage automatically
```

### Manual Token Setting
```python
# Set authentication token manually
klavis_client.mcp_server.set_auth_token(
    instance_id=server.instance_id,
    auth_token="your_service_token"
)
```

### Supported OAuth Platforms
- GitHub, Slack, Jira, Notion, Supabase, WordPress
- Google services (Gmail, Calendar, Drive, Docs, Sheets)
- Airtable, Asana, Close, Confluence, Salesforce, Linear
- ClickUp, HubSpot, Attio, and more

## Error Handling

```python
try:
    result = klavis_client.mcp_server.call_tools(
        server_url=server.server_url,
        tool_name="search_videos",
        tool_args={"query": "AI tutorials"}
    )
    
    if result.success:
        print(result.result)
    else:
        print(f"Error: {result.error}")
        
except Exception as e:
    print(f"API Error: {e}")
```

## Configuration

### Environment Variables
```bash
KLAVIS_API_KEY=your_klavis_api_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

### Server Configuration
Each MCP server can be configured with:
- Custom port settings
- Service-specific API tokens
- Environment-specific configurations
- Connection type preferences

## Tool Formats

### OpenAI Format
```json
{
  "type": "function",
  "function": {
    "name": "search_videos",
    "description": "Search for videos on YouTube",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer"}
      }
    }
  }
}
```

### Anthropic Format
```json
{
  "name": "search_videos",
  "description": "Search for videos on YouTube",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "max_results": {"type": "integer"}
    }
  }
}
```

### Gemini Format
```json
{
  "function_declarations": [{
    "name": "search_videos",
    "description": "Search for videos on YouTube",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer"}
      }
    }
  }]
}
```

## Best Practices

1. **Server Instance Management**: Create instances once and reuse them
2. **Authentication**: Handle OAuth flows gracefully with user feedback
3. **Error Handling**: Always check result.success before using result.result
4. **Tool Discovery**: Use list_tools to understand available functionality
5. **Rate Limiting**: Respect API rate limits and implement backoff strategies
6. **Security**: Store API keys securely and use environment variables

## Support & Resources

- **Documentation**: [docs.klavis.ai](https://docs.klavis.ai)
- **Website**: [klavis.ai](https://www.klavis.ai)
- **Discord**: [Join Community](https://discord.gg/p7TuTEcssn)
- **GitHub**: [klavis-ai/klavis](https://github.com/klavis-ai/klavis)
- **PyPI**: [klavis](https://pypi.org/project/klavis/)
- **npm**: [klavis](https://www.npmjs.com/package/klavis)

