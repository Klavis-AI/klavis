# Notion MCP Server

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

#### 2. Adding MCP config to your client:

##### Using npm:
Add the following to your `.cursor/mcp.json` or `claude_desktop_config.json` (MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`)

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

##### Using Docker:
You can also run the MCP server using Docker. First, build the Docker image:

```bash
docker-compose build
```

Then, add the following to your `.cursor/mcp.json` or `claude_desktop_config.json`:

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
        "notion-mcp-server-notion-mcp-server"
      ]
    }
  }
}
```

Don't forget to replace `ntn_****` with your integration secret. Find it from your integration configuration tab:

![Copying your Integration token from the Configuration tab in the developer portal](https://github.com/user-attachments/assets/67b44536-5333-49fa-809c-59581bf5370a)

#### 3. Connecting content to integration:
Ensure relevant pages and databases are connected to your integration.

To do this, you'll need to visit that page, and click on the 3 dots, and select "Connect to integration". 

![Adding Integration Token to Notion Connections](docs/images/connections.png)

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

## Using the MCP Server

This MCP server follows the Model Context Protocol and implements the standard `/sse` and `/messages` endpoints that are used by MCP clients.

### Endpoints

- **GET /sse** - Establishes an SSE connection that the server uses to send messages to the client.
- **POST /messages** - Endpoint for clients to send messages to the server.
  - Required query parameter: `sessionId` - The session ID obtained from the SSE connection.
  - Optional header: `x-auth-token` - Notion API key (if not provided via environment variables).

### Authentication

The server requires a Notion API key to communicate with the Notion API. This can be provided in two ways:

1. Via the `NOTION_API_KEY` environment variable.
2. Via the `x-auth-token` header when making requests to the `/messages` endpoint.

### Running the Server

```bash
# Install dependencies
npm install

# Start the server
npm start
```

The server will listen on port 5000 by default. You can customize this by setting the `PORT` environment variable.

### OpenAPI Specification

The server uses a Notion API OpenAPI specification file located at `scripts/notion-openapi.json`. This specification defines all the endpoints and operations available through the Notion API. If you need to customize or update the API specification, you can:

1. Modify the existing specification file, or
2. Provide a different specification file path using the `OPENAPI_SPEC_PATH` environment variable.
