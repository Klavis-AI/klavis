# Zapier MCP Server

A Model Context Protocol (MCP) server for Zapier that follows the standard Python MCP server format.

## Features

- **Dual Transport Support**: Both SSE and StreamableHTTP transports
- **Authentication**: Token-based authentication via headers
- **Comprehensive API Coverage**: Workflows, tasks, webhooks, and apps
- **Standard Format**: Follows the same pattern as other Python MCP servers

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Zapier API key:
```bash
export ZAPIER_API_KEY=your_api_key_here
```

3. Run the server:
```bash
python server.py
```

### HTTP Server Mode

Run with HTTP transport for remote access:

```bash
python server.py --port 5000
```

This will start the server with both SSE and StreamableHTTP endpoints:
- SSE: `http://localhost:5000/sse`
- StreamableHTTP: `http://localhost:5000/mcp`

### Authentication

The server supports authentication via the `x-auth-token` header:

```bash
curl -H "x-auth-token: your_zapier_api_key" \
     http://localhost:5000/mcp
```

## Available Tools

### Workflows
- `zapier_list_workflows` - List all workflows
- `zapier_get_workflow` - Get workflow details
- `zapier_create_workflow` - Create new workflow
- `zapier_update_workflow` - Update existing workflow
- `zapier_delete_workflow` - Delete workflow
- `zapier_trigger_workflow` - Trigger workflow manually

### Tasks
- `zapier_list_tasks` - List tasks
- `zapier_get_task` - Get task details

### Webhooks
- `zapier_list_webhooks` - List webhooks
- `zapier_create_webhook` - Create webhook
- `zapier_get_webhook` - Get webhook details

### Apps
- `zapier_list_apps` - List available apps
- `zapier_get_app` - Get app details
- `zapier_connect_app` - Connect app to account

## Project Structure

```
mcp_servers/zapier/
├── server.py              # Main server with CLI and transports
├── tools/                 # Tool implementations
│   ├── __init__.py       # Tool exports
│   ├── base.py           # Authentication utilities
│   ├── workflows.py      # Workflow tools
│   ├── tasks.py          # Task tools
│   ├── webhooks.py       # Webhook tools
│   └── apps.py           # App tools
├── requirements.txt       # Dependencies
├── Dockerfile            # Containerization
└── README.md            # This file
```

## Configuration

Environment variables:
- `ZAPIER_API_KEY`: Your Zapier API key
- `ZAPIER_MCP_SERVER_PORT`: Server port (default: 5000)

## Docker

Build and run with Docker:

```bash
docker build -t zapier-mcp-server .
docker run -p 5000:5000 -e ZAPIER_API_KEY=your_key zapier-mcp-server
```

## Development

The server follows the standard Python MCP server pattern used by other servers in this codebase:

1. **Simple server.py** with Click CLI and dual transport support
2. **Organized tools/** directory with clear separation of concerns
3. **Context-based authentication** for security
4. **Async HTTP client** for API calls

