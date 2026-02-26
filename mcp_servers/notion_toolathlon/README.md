# Notion MCP Server

> [!NOTE] 
> 
> We’ve introduced **Notion MCP**, a remote MCP server with the following improvements:
> - Easy installation via standard OAuth. No need to fiddle with JSON or API token anymore.
> - Powerful tools tailored to AI agents. These tools are designed with optimized token consumption in mind.
> 
> Learn more and try it out [here](https://developers.notion.com/docs/mcp)


![notion-mcp-sm](https://github.com/user-attachments/assets/6c07003c-8455-4636-b298-d60ffdf46cd8)

This project implements an [MCP server](https://spec.modelcontextprotocol.io/) for the [Notion API](https://developers.notion.com/reference/intro). 

![mcp-demo](https://github.com/user-attachments/assets/e3ff90a7-7801-48a9-b807-f7dd47f0d3d6)

### Installation

#### 1. Setting up Integration in Notion:
Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations) and create a new **internal** integration or select an existing one.

![Creating a Notion Integration token](docs/images/integrations-creation.png)

While we limit the scope of Notion API's exposed (for example, you will not be able to delete databases via MCP), there is a non-zero risk to workspace data by exposing it to LLMs. Security-conscious users may want to further configure the Integration's _Capabilities_. 

For example, you can create a read-only integration token by giving only "Read content" access from the "Configuration" tab:

![Notion Integration Token Capabilities showing Read content checked](docs/images/integrations-capabilities.png)

#### 2. Connecting content to integration:
Ensure relevant pages and databases are connected to your integration.

To do this, visit the **Access** tab in your internal integration settings. Edit access and select the pages you'd like to use.
![Integration Access tab](docs/images/integration-access.png)

![Edit integration access](docs/images/page-access-edit.png)

Alternatively, you can grant page access individually. You'll need to visit the target page, and click on the 3 dots, and select "Connect to integration". 

![Adding Integration Token to Notion Connections](docs/images/connections.png)

#### 3. Adding MCP config to your client:

##### Using npm:

**Cursor & Claude:**

Add the following to your `.cursor/mcp.json` or `claude_desktop_config.json` (MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`)

**Option 1: Using NOTION_TOKEN (recommended)**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_TOKEN": "ntn_****"
      }
    }
  }
}
```

**Option 2: Using OPENAPI_MCP_HEADERS (for advanced use cases)**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2022-06-28\" }"
      }
    }
  }
}
```

**Zed**

Add the following to your `settings.json`

```json
{
  "context_servers": {
    "some-context-server": {
      "command": {
        "path": "npx",
        "args": ["-y", "@notionhq/notion-mcp-server"],
        "env": {
          "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2022-06-28\" }"
        }
      },
      "settings": {}
    }
  }
}
```

##### Using Docker:

There are two options for running the MCP server with Docker:

###### Option 1: Using the official Docker Hub image:

Add the following to your `.cursor/mcp.json` or `claude_desktop_config.json`:

**Using NOTION_TOKEN (recommended):**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "NOTION_TOKEN",
        "mcp/notion"
      ],
      "env": {
        "NOTION_TOKEN": "ntn_****"
      }
    }
  }
}
```

**Using OPENAPI_MCP_HEADERS (for advanced use cases):**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "OPENAPI_MCP_HEADERS",
        "mcp/notion"
      ],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer ntn_****\",\"Notion-Version\":\"2022-06-28\"}"
      }
    }
  }
}
```

This approach:
- Uses the official Docker Hub image
- Properly handles JSON escaping via environment variables
- Provides a more reliable configuration method

###### Option 2: Building the Docker image locally:

You can also build and run the Docker image locally. First, build the Docker image:

```bash
docker compose build
```

Then, add the following to your `.cursor/mcp.json` or `claude_desktop_config.json`:

**Using NOTION_TOKEN (recommended):**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "NOTION_TOKEN=ntn_****",
        "notion-mcp-server"
      ]
    }
  }
}
```

**Using OPENAPI_MCP_HEADERS (for advanced use cases):**
```javascript
{
  "mcpServers": {
    "notionApi": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OPENAPI_MCP_HEADERS={\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2022-06-28\"}",
        "notion-mcp-server"
      ]
    }
  }
}
```

Don't forget to replace `ntn_****` with your integration secret. Find it from your integration configuration tab:

![Copying your Integration token from the Configuration tab in the developer portal](https://github.com/user-attachments/assets/67b44536-5333-49fa-809c-59581bf5370a)


#### Installing via Smithery

[![smithery badge](https://smithery.ai/badge/@makenotion/notion-mcp-server)](https://smithery.ai/server/@makenotion/notion-mcp-server)

To install Notion API Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@makenotion/notion-mcp-server):

```bash
npx -y @smithery/cli install @makenotion/notion-mcp-server --client claude
```

### Transport Options

The Notion MCP Server supports two transport modes:

#### STDIO Transport (Default)
The default transport mode uses standard input/output for communication. This is the standard MCP transport used by most clients like Claude Desktop.

```bash
# Run with default stdio transport
npx @notionhq/notion-mcp-server

# Or explicitly specify stdio
npx @notionhq/notion-mcp-server --transport stdio
```

#### Streamable HTTP Transport
For web-based applications or clients that prefer HTTP communication, you can use the Streamable HTTP transport:

```bash
# Run with Streamable HTTP transport on port 3000 (default)
npx @notionhq/notion-mcp-server --transport http

# Run on a custom port
npx @notionhq/notion-mcp-server --transport http --port 8080

# Run with a custom authentication token
npx @notionhq/notion-mcp-server --transport http --auth-token "your-secret-token"
```

When using Streamable HTTP transport, the server will be available at `http://0.0.0.0:<port>/mcp`.

##### Authentication
The Streamable HTTP transport requires bearer token authentication for security. You have three options:

**Option 1: Auto-generated token (recommended for development)**
```bash
npx @notionhq/notion-mcp-server --transport http
```
The server will generate a secure random token and display it in the console:
```
Generated auth token: a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789ab
Use this token in the Authorization header: Bearer a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789ab
```

**Option 2: Custom token via command line (recommended for production)**
```bash
npx @notionhq/notion-mcp-server --transport http --auth-token "your-secret-token"
```

**Option 3: Custom token via environment variable (recommended for production)**
```bash
AUTH_TOKEN="your-secret-token" npx @notionhq/notion-mcp-server --transport http
```

The command line argument `--auth-token` takes precedence over the `AUTH_TOKEN` environment variable if both are provided.

##### Making HTTP Requests
All requests to the Streamable HTTP transport must include the bearer token in the Authorization header:

```bash
# Example request
curl -H "Authorization: Bearer your-token-here" \
     -H "Content-Type: application/json" \
     -H "mcp-session-id: your-session-id" \
     -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}' \
     http://localhost:3000/mcp
```

**Note:** Make sure to set either the `NOTION_TOKEN` environment variable (recommended) or the `OPENAPI_MCP_HEADERS` environment variable with your Notion integration token when using either transport mode.

### Examples

1. Using the following instruction
```
Comment "Hello MCP" on page "Getting started"
```

AI will correctly plan two API calls, `v1/search` and `v1/comments`, to achieve the task

2. Similarly, the following instruction will result in a new page named "Notion MCP" added to parent page "Development"
```
Add a page titled "Notion MCP" to page "Development"
```

3. You may also reference content ID directly
```
Get the content of page 1a6b35e6e67f802fa7e1d27686f017f2
```

### Development

Build

```
npm run build
```

Execute

```
npx -y --prefix /path/to/local/notion-mcp-server @notionhq/notion-mcp-server
```

Publish

```
npm publish --access public
```
