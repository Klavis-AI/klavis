# Close CRM MCP Server

A Model Context Protocol (MCP) server for integrating with Close CRM. This server provides comprehensive access to Close CRM's API functionality including leads, contacts, opportunities, tasks, and user management.

## Features

### Lead Management
- Create, read, update, and delete leads
- Search and list leads with filtering
- Support for lead status management
- Merge multiple leads

### Contact Management
- Create, read, update, and delete contacts
- Search contacts with various filters
- Manage contact information (emails, phones, etc.)

### Opportunity Management
- Create, read, update, and delete opportunities
- Track opportunity value, confidence, and expected dates
- Manage opportunity statuses

### Task Management
- Create, read, update, and delete tasks
- List tasks with filtering (by completion status, assignee, etc.)
- Support for different task types and views

### User Management
- Get current user information
- List and search users

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export CLOSE_MCP_SERVER_PORT=5000
```

3. Run the server:
```bash
python server.py
```

## Authentication

The server uses Close CRM's access token authentication. You need to provide your Close access token in the Authorization header when making requests:

```
Authorization: Bearer YOUR_CLOSE_ACCESS_TOKEN
```

or via the x-auth-token header:

```
x-auth-token: YOUR_CLOSE_ACCESS_TOKEN
```

To get your access token:
1. Log in to your Close account
2. Go to Settings → API Keys
3. Generate a new access token

## API Endpoints

The server runs on port 5000 by default and provides the following endpoints:

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/` - Main HTTP endpoint for tool execution

## Available Tools

### Lead Tools
- `close_create_lead` - Create a new lead
- `close_get_lead` - Get a lead by ID
- `close_search_leads` - Search for leads
- `close_update_lead` - Update an existing lead
- `close_delete_lead` - Delete a lead
- `close_list_leads` - List leads with pagination

### Contact Tools
- `close_create_contact` - Create a new contact
- `close_get_contact` - Get a contact by ID
- `close_search_contacts` - Search for contacts
- `close_update_contact` - Update an existing contact
- `close_delete_contact` - Delete a contact

### Opportunity Tools
- `close_create_opportunity` - Create a new opportunity
- `close_get_opportunity` - Get an opportunity by ID
- `close_update_opportunity` - Update an existing opportunity
- `close_delete_opportunity` - Delete an opportunity

### Task Tools
- `close_create_task` - Create a new task
- `close_get_task` - Get a task by ID
- `close_update_task` - Update an existing task
- `close_delete_task` - Delete a task
- `close_list_tasks` - List tasks with filtering

### User Tools
- `close_get_current_user` - Get current user information
- `close_list_users` - List users
- `close_get_user` - Get a user by ID

## Docker Support

Build the Docker image:
```bash
docker build -t close-mcp-server -f mcp_servers/close/Dockerfile .
```

Run the container:
```bash
docker run -p 5001:5000 -e CLOSE_ACCESS_TOKEN=your_access_token close-mcp-server
```

## Configuration

Environment variables:
- `CLOSE_MCP_SERVER_PORT` - Port to run the server on (default: 5000)
- `CLOSE_ACCESS_TOKEN` - Your Close CRM access token (can also be passed in Authorization header)

## Error Handling

The server provides comprehensive error handling with detailed error messages for debugging. All errors are returned in JSON format with both user-friendly messages and developer-specific details.

## Rate Limits

The server respects Close CRM's API rate limits and implements appropriate request throttling to prevent API quota exhaustion.

## Contributing

This MCP server follows the same architecture pattern as other MCP servers in this repository. The codebase is organized into:

- `server.py` - Main server application
- `tools/` - Tool implementations organized by resource type
- `tools/base.py` - Base client and common utilities
- `tools/constants.py` - API constants and enums

When adding new features, follow the existing patterns and ensure proper error handling and logging. 