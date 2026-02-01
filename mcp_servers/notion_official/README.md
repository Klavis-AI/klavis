# Notion MCP Server

> [!NOTE]
>
> We’ve introduced **Notion MCP**, a remote MCP server with the following improvements:
>
> - Easy installation via standard OAuth. No need to fiddle with JSON or API tokens anymore.
> - Powerful tools tailored to AI agents, including editing pages in Markdown. These tools are designed with optimized token consumption in mind.
>
> Learn more and get started at [Notion MCP documentation](https://developers.notion.com/docs/mcp).
>
> We are prioritizing, and only providing active support for, **Notion MCP** (remote). As a result:
>
> - We may sunset this local MCP server repository in the future.
> - Issues and pull requests here are not actively monitored.
> - Please do not file issues relating to the remote MCP here; instead, contact Notion support.

![notion-mcp-sm](https://github.com/user-attachments/assets/6c07003c-8455-4636-b298-d60ffdf46cd8)

This project implements an [MCP server](https://spec.modelcontextprotocol.io/) for the [Notion API](https://developers.notion.com/reference/intro).

![mcp-demo](https://github.com/user-attachments/assets/e3ff90a7-7801-48a9-b807-f7dd47f0d3d6)

---

## ⚠️ Version 2.0.0 breaking changes

**Version 2.0.0 migrates to the Notion API 2025-09-03** which introduces data sources as the primary abstraction for databases.

### What changed

**Removed tools (3):**

- `post-database-query` - replaced by `query-data-source`
- `update-a-database` - replaced by `update-a-data-source`
- `create-a-database` - replaced by `create-a-data-source`

**New tools (7):**

- `query-data-source` - Query a data source (database) with filters and sorts
- `retrieve-a-data-source` - Get metadata and schema for a data source
- `update-a-data-source` - Update data source properties
- `create-a-data-source` - Create a new data source
- `list-data-source-templates` - List available templates in a data source
- `move-page` - Move a page to a different parent location
- `retrieve-a-database` - Get database metadata including its data source IDs

**Parameter changes:**

- All database operations now use `data_source_id` instead of `database_id`
- Search filter values changed from `["page", "database"]` to `["page", "data_source"]`
- Page creation now supports both `page_id` and `database_id` parents (for data sources)

### Do I need to migrate?

**No code changes required.** MCP tools are discovered automatically when the server starts. When you upgrade to v2.0.0, AI clients will automatically see the new tool names and parameters. The old database tools are no longer available.

If you have hardcoded tool names or prompts that reference the old database tools, update them to use the new data source tools:

| Old Tool (v1.x) | New Tool (v2.0) | Parameter Change |
| -------------- | --------------- | ---------------- |
| `post-database-query` | `query-data-source` | `database_id` → `data_source_id` |
| `update-a-database` | `update-a-data-source` | `database_id` → `data_source_id` |
| `create-a-database` | `create-a-data-source` | No change (uses `parent.page_id`) |

> **Note:** `retrieve-a-database` is still available and returns database metadata including the list of data source IDs. Use `retrieve-a-data-source` to get the schema and properties of a specific data source.

**Total tools now: 22** (was 19 in v1.x)

---

### Installation

#### 1. Setting up integration in Notion

Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations) and create a new **internal** integration or select an existing one.

![Creating a Notion Integration token](docs/images/integrations-creation.png)

While we limit the scope of Notion API's exposed (for example, you will not be able to delete databases via MCP), there is a non-zero risk to workspace data by exposing it to LLMs. Security-conscious users may want to further configure the Integration's _Capabilities_.

For example, you can create a read-only integration token by giving only "Read content" access from the "Configuration" tab:

![Notion Integration Token Capabilities showing Read content checked](docs/images/integrations-capabilities.png)

#### 2. Connecting content to integration

Ensure relevant pages and databases are connected to your integration.

To do this, visit the **Access** tab in your internal integration settings. Edit access and select the pages you'd like to use.

![Integration Access tab](docs/images/integration-access.png)

![Edit integration access](docs/images/page-access-edit.png)

Alternatively, you can grant page access individually. You'll need to visit the target page, and click on the 3 dots, and select "Connect to integration".

![Adding Integration Token to Notion Connections](docs/images/connections.png)

#### 3. Adding MCP config to your client

##### Using npm

###### Cursor & Claude

Add the following to your `.cursor/mcp.json` or `claude_desktop_config.json` (MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`)

###### Option 1: Using NOTION_TOKEN (recommended)

```json
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

###### Option 2: Using OPENAPI_MCP_HEADERS (for advanced use cases)

```json
{
  "mcpServers": {
    "notionApi": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2025-09-03\" }"
      }
    }
  }
}
```

###### Zed

Add the following to your `settings.json`

```json
{
  "context_servers": {
    "some-context-server": {
      "command": {
        "path": "npx",
        "args": ["-y", "@notionhq/notion-mcp-server"],
        "env": {
          "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2025-09-03\" }"
        }
      },
      "settings": {}
    }
  }
}
```

###### GitHub Copilot CLI

Use the Copilot CLI to interactively add the MCP server:

```bash
/mcp add
```

Alternatively, create or edit the configuration file `~/.copilot/mcp-config.json` and add:

```json
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

For more information, see the [Copilot CLI documentation](https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli).

##### Using Docker

There are two options for running the MCP server with Docker:

###### Option 1: Using the official Docker Hub image

Add the following to your `.cursor/mcp.json` or `claude_desktop_config.json`

Using NOTION_TOKEN (recommended):

```json
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

Using OPENAPI_MCP_HEADERS (for advanced use cases):

```json
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
        "OPENAPI_MCP_HEADERS": "{\"Authorization\":\"Bearer ntn_****\",\"Notion-Version\":\"2025-09-03\"}"
      }
    }
  }
}
```

This approach:

- Uses the official Docker Hub image
- Properly handles JSON escaping via environment variables
- Provides a more reliable configuration method

###### Option 2: Building the Docker image locally

You can also build and run the Docker image locally. First, build the Docker image:

```bash
docker compose build
```

Then, add the following to your `.cursor/mcp.json` or `claude_desktop_config.json`

Using NOTION_TOKEN (recommended):

```json
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

Using OPENAPI_MCP_HEADERS (for advanced use cases):

```json
{
  "mcpServers": {
    "notionApi": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OPENAPI_MCP_HEADERS={\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2025-09-03\"}",
        "notion-mcp-server"
      ]
    }
  }
}
```

Don't forget to replace `ntn_****` with your integration secret. Find it from your integration configuration tab:

![Copying your Integration token from the Configuration tab in the developer portal](https://github.com/user-attachments/assets/67b44536-5333-49fa-809c-59581bf5370a)

### Transport options

The Notion MCP Server supports two transport modes:

#### STDIO transport (default)

The default transport mode uses standard input/output for communication. This is the standard MCP transport used by most clients like Claude Desktop.

```bash
# Run with default stdio transport
npx @notionhq/notion-mcp-server

# Or explicitly specify stdio
npx @notionhq/notion-mcp-server --transport stdio
```

#### Streamable HTTP transport

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

###### Option 1: Auto-generated token (recommended for development)

```bash
npx @notionhq/notion-mcp-server --transport http
```

The server will generate a secure random token and display it in the console:

```text
Generated auth token: a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789ab
Use this token in the Authorization header: Bearer a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789ab
```

###### Option 2: Custom token via command line (recommended for production)

```bash
npx @notionhq/notion-mcp-server --transport http --auth-token "your-secret-token"
```

###### Option 3: Custom token via environment variable (recommended for production)

```bash
AUTH_TOKEN="your-secret-token" npx @notionhq/notion-mcp-server --transport http
```

The command line argument `--auth-token` takes precedence over the `AUTH_TOKEN` environment variable if both are provided.

##### Making HTTP requests

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

```text
Comment "Hello MCP" on page "Getting started"
```

   AI will correctly plan two API calls, `v1/search` and `v1/comments`, to achieve the task

1. Similarly, the following instruction will result in a new page named "Notion MCP" added to parent page "Development"

```text
Add a page titled "Notion MCP" to page "Development"
```

1. You may also reference content ID directly

```text
Get the content of page 1a6b35e6e67f802fa7e1d27686f017f2
```

### Development

#### Build & test

```bash
npm run build
npm test
```

#### Execute

```bash
npx -y --prefix /path/to/local/notion-mcp-server @notionhq/notion-mcp-server
```

Testing changes locally in Cursor:

1. Run `npm link` command from repository root to create a machine-global symlink to the `notion-mcp-server` package.
2. Merge the configuration snippet below into Cursor's `mcp.json` (or other MCP client you want to test with).
3. (Cleanup) run `npm unlink` from repository root.

```json
{
  "mcpServers": {
    "notion-local-package": {
      "command": "notion-mcp-server",
      "env": {
        "NOTION_TOKEN": "ntn_..."
      }
    }
  }
}
```

#### Publish

```bash
npm login
npm publish --access public
```
