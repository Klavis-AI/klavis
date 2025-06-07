# Asana MCP Server

A Model Context Protocol (MCP) server for interacting with Asana tasks and projects.

## Features

- **Task Management**: Create, read, update, and search tasks
- **Project Management**: List and filter projects
- **Workspace Management**: Access user workspaces
- **Tag Support**: Create and manage task tags
- **Date Filtering**: Filter tasks by due dates and start dates
- **Assignee Management**: Assign tasks to users

## Available Tools

### Task Operations
- `create_task`: Create a new task with optional project, assignee, dates, and tags
- `get_task`: Retrieve a specific task by ID with optional subtasks
- `search_tasks`: Search for tasks with various filters (keywords, dates, assignee, project, etc.)
- `update_task`: Update task properties like name, completion status, dates, and assignee

### Project Operations
- `get_projects`: List projects in a workspace or team

### Workspace Operations
- `get_workspaces`: List user's available workspaces

## Configuration

Set the following environment variables:

- `ASANA_MCP_SERVER_PORT`: Port for the server (default: 5000)
- `ASANA_MAX_CONCURRENT_REQUESTS`: Max concurrent API requests (default: 3)
- `ASANA_MAX_TIMEOUT_SECONDS`: Request timeout in seconds (default: 20)

## Authentication

The server expects an Asana Personal Access Token to be provided in the Authorization header:

```
Authorization: Bearer YOUR_ASANA_TOKEN
```

## Running the Server

### Direct Python
```bash
python server.py --port 5000
```

### Docker
```bash
docker build -t asana-mcp-server .
docker run -p 5001:5000 asana-mcp-server
```

## API Endpoints

- **SSE**: `GET /sse` - Server-Sent Events endpoint for MCP communication
- **HTTP**: All other paths - StreamableHTTP endpoint for MCP communication

## Dependencies

- mcp>=1.8.1
- httpx
- starlette
- uvicorn
- click
- python-dotenv 