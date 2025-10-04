# Zendesk MCP Server

A Model Context Protocol (MCP) server that provides access to Zendesk's customer support platform through a standardized interface.

## Features

### Ticket Management
- **List tickets** with filtering and pagination
- **Get ticket details** by ID
- **Create new tickets** with customizable fields
- **Update existing tickets** (subject, description, assignee, status, priority, tags)
- **Delete tickets**
- **Add comments** to tickets (public or private)
- **Get ticket comments** with pagination
- **Assign tickets** to specific agents
- **Change ticket status** (new, open, pending, hold, solved, closed)
- **Search tickets** using Zendesk search syntax

### User Management
- **List users** with role and organization filtering
- **Get user details** by ID
- **Create new users** (end-users, agents, admins)
- **Update user information** (name, email, role, organization, phone, tags)
- **Delete users**
- **Search users** using Zendesk search syntax
- **Get user tickets** (tickets requested by a user)
- **Get user organizations** (organizations associated with a user)
- **Suspend/reactivate** user accounts
- **Get current authenticated user** information

### Organization Management
- **List organizations** with pagination
- **Get organization details** by ID
- **Create new organizations** with domain and tags
- **Update organization information** (name, domain, tags)
- **Delete organizations**
- **Search organizations** using Zendesk search syntax
- **Get organization tickets** (tickets for a specific organization)
- **Get organization users** (users in a specific organization)

## Authentication

The server uses Zendesk's API token authentication method. You need to provide:

- **API Token**: Your Zendesk API token
- **Email**: Your Zendesk account email address
- **Base URL**: Your Zendesk subdomain (e.g., `https://yourcompany.zendesk.com`)

### Environment Variables

Set these environment variables:

```bash
export ZENDESK_SUBDOMAIN="yourcompany"
export ZENDESK_API_TOKEN="your_api_token"
export ZENDESK_EMAIL="your_email@example.com"
export ZENDESK_MCP_SERVER_PORT=5002
```

**Note**: The `ZENDESK_SUBDOMAIN` should be just the subdomain part (e.g., "company" for https://company.zendesk.com), not the full URL.

### Authentication

The server uses environment variables for authentication. Make sure to set:
- `ZENDESK_API_TOKEN`: Your Zendesk API token (get this from Zendesk Admin Center > Channels > API)
- `ZENDESK_EMAIL`: Your Zendesk account email address
- `ZENDESK_SUBDOMAIN`: Your Zendesk subdomain

## Installation

### Prerequisites

- Python 3.11+
- Zendesk account with API access

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export ZENDESK_SUBDOMAIN="yourcompany"
   export ZENDESK_API_TOKEN="your_api_token"
   export ZENDESK_EMAIL="your_email@example.com"
   ```

4. Run the server:
   ```bash
   python server.py --port 5000
   ```

### Docker

1. Build the image:
   ```bash
   docker build -t zendesk-mcp-server .
   ```

2. Run the container:
   ```bash
   docker run -p 5002:5002 \
     -e ZENDESK_SUBDOMAIN="yourcompany" \
     -e ZENDESK_API_TOKEN="your_api_token" \
     -e ZENDESK_EMAIL="your_email@example.com" \
     zendesk-mcp-server
   ```

## Usage

### Starting the Server

```bash
# Basic usage
python server.py

# Custom port
python server.py --port 8080

# Debug logging
python server.py --log-level DEBUG

# JSON responses for StreamableHTTP
python server.py --json-response
```

### Available Endpoints

- **SSE**: `http://localhost:5002/sse`
- **StreamableHTTP**: `http://localhost:5002/mcp`

### Example Tool Calls

#### List Tickets
```json
{
  "name": "zendesk_list_tickets",
  "arguments": {
    "status": "open",
    "per_page": 10
  }
}
```

#### Create Ticket
```json
{
  "name": "zendesk_create_ticket",
  "arguments": {
    "subject": "Technical Issue",
    "description": "I'm experiencing a problem with the application.",
    "priority": "high",
    "tags": ["technical", "urgent"]
  }
}
```

#### Search Users
```json
{
  "name": "zendesk_search_users",
  "arguments": {
    "query": "role:agent organization:123"
  }
}
```

## API Reference

### Ticket Statuses
- `new`: New ticket
- `open`: Open ticket
- `pending`: Pending ticket
- `hold`: On hold
- `solved`: Solved ticket
- `closed`: Closed ticket

### Ticket Priorities
- `urgent`: Urgent priority
- `high`: High priority
- `normal`: Normal priority
- `low`: Low priority

### User Roles
- `end-user`: End user (customer)
- `agent`: Support agent
- `admin`: Administrator

### Search Syntax

The server supports Zendesk's search syntax for tickets, users, and organizations:

- **Status filtering**: `status:open`
- **Role filtering**: `role:agent`
- **Organization filtering**: `organization:123`
- **Date filtering**: `created>2024-01-01`
- **Text search**: `"error message"`

## Error Handling

The server provides comprehensive error handling:

- **Authentication errors**: Invalid credentials or missing environment variables
- **Rate limiting**: Automatic retry-after handling
- **Validation errors**: Invalid input parameters
- **API errors**: Zendesk API response errors
- **Network errors**: Connection and timeout issues

## Rate Limiting

Zendesk has rate limits on API calls. The server automatically handles:
- Rate limit detection (HTTP 429)
- Retry-after header parsing
- Appropriate error messages with retry timing

## Development

### Project Structure

```
zendesk/
├── tools/
│   ├── __init__.py      # Tool exports
│   ├── base.py          # Base utilities and auth
│   ├── tickets.py       # Ticket management tools
│   ├── users.py         # User management tools
│   └── organizations.py # Organization management tools
├── server.py            # Main MCP server
├── test_server.py       # Comprehensive test suite for all tools
├── custom_mcp_client.py # Custom MCP client for benchmarking
├── streamable_http_benchmarks.py # Performance benchmarks
├── requirements.txt     # Python dependencies
├── requirements_custom_client.txt # Custom client dependencies
├── Dockerfile          # Docker configuration
└── README.md           # This file
```

### Adding New Tools

1. Create the tool function in the appropriate module
2. Add the tool to the `__init__.py` exports
3. Register the tool in `server.py` with proper schema
4. Add the tool call handler in the `call_tool` function

### Testing

Test the server locally:

```bash
# Run comprehensive tests for all tools
python test_server.py

# Test basic functionality
curl http://localhost:5002/sse

# Test StreamableHTTP
curl http://localhost:5002/mcp
```

**Note**: The `test_server.py` script runs comprehensive tests for all Zendesk tools including ticket management, user management, and organization management. Make sure your environment variables are set before running the tests.


### Logs

Enable debug logging for detailed information:

```bash
python server.py --log-level DEBUG
```


## License

This project is licensed under the same license as the main Klavis project.

