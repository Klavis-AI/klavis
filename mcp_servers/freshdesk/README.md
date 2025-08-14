# Freshdesk MCP Server

A production-ready Model Context Protocol (MCP) server for integrating with Freshdesk's customer support platform.

## Features

- **Full CRUD Operations**: Create, read, update, and delete tickets
- **Advanced Filtering**: List tickets with various filters and pagination
- **Production Ready**: Comprehensive error handling, retry logic, and validation
- **Secure**: Token-based authentication with proper input validation
- **Monitoring**: Health check endpoint and structured logging
- **Docker Support**: Containerized deployment with security best practices

## Prerequisites

- Python 3.12+
- Freshdesk account with API access
- Freshdesk API key

## Environment Variables

Create a `.env` file in the project root:

```bash
FRESHDESK_API_KEY=your_api_key_here
FRESHDESK_DOMAIN=yourcompany.freshdesk.com
FRESHDESK_MCP_SERVER_PORT=5000
```

### Configuration Details

- **FRESHDESK_API_KEY**: Your Freshdesk API key (required)
- **FRESHDESK_DOMAIN**: Your Freshdesk domain (e.g., 'yourcompany' or 'yourcompany.freshdesk.com')
- **FRESHDESK_MCP_SERVER_PORT**: Port for the MCP server (default: 5000)

## Installation

### Local Development

1. Clone the repository and navigate to the freshdesk server directory:
```bash
cd mcp_servers/freshdesk
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
python server.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t freshdesk-mcp-server .
```

2. Run the container:
```bash
docker run -p 5000:5000 \
  -e FRESHDESK_API_KEY=your_api_key \
  -e FRESHDESK_DOMAIN=yourcompany.freshdesk.com \
  freshdesk-mcp-server
```

## Available Tools

### 1. Create Ticket (`freshdesk_create_ticket`)

Creates a new support ticket.

**Required Parameters:**
- `subject`: Ticket subject
- `email`: Requester email

**Optional Parameters:**
- `description`: Ticket description (HTML or text)
- `priority`: Priority level (1=Low, 2=Medium, 3=High, 4=Urgent)
- `status`: Ticket status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
- `cc_emails`: List of CC email addresses
- `tags`: List of tags

**Example:**
```json
{
  "subject": "Login Issue",
  "email": "user@example.com",
  "description": "Unable to login to the application",
  "priority": 3,
  "tags": ["login", "urgent"]
}
```

### 2. Get Ticket (`freshdesk_get_ticket`)

Retrieves a specific ticket by ID.

**Required Parameters:**
- `ticket_id`: Numeric ticket ID

**Example:**
```json
{
  "ticket_id": 12345
}
```

### 3. Update Ticket (`freshdesk_update_ticket`)

Updates an existing ticket.

**Required Parameters:**
- `ticket_id`: Numeric ticket ID

**Optional Parameters:**
- `subject`: New subject
- `description`: New description
- `priority`: New priority level
- `status`: New status
- `cc_emails`: New CC email list
- `tags`: New tag list

**Example:**
```json
{
  "ticket_id": 12345,
  "status": 4,
  "description": "Issue resolved by updating password"
}
```

### 4. Delete Ticket (`freshdesk_delete_ticket`)

Deletes a ticket.

**Required Parameters:**
- `ticket_id`: Numeric ticket ID

**Example:**
```json
{
  "ticket_id": 12345
}
```

### 5. List Tickets (`freshdesk_list_tickets`)

Lists tickets with optional filtering and pagination.

**Optional Parameters:**
- `email`: Filter by requester email
- `updated_since`: ISO timestamp for filtering by last updated
- `per_page`: Results per page (1-100, default 30)
- `page`: Page number (default 1)
- `order_type`: Sort order ("asc" or "desc")

**Example:**
```json
{
  "email": "user@example.com",
  "per_page": 50,
  "order_type": "desc"
}
```

## API Endpoints

- **Health Check**: `GET /health` - Server health status
- **SSE**: `GET /sse` - Server-Sent Events endpoint
- **MCP**: `POST /mcp` - Model Context Protocol endpoint
- **Messages**: `POST /messages/*` - Message handling endpoints

## Error Handling

The server provides comprehensive error handling:

- **Input Validation**: All parameters are validated before processing
- **Retry Logic**: Automatic retry for transient errors (429, 500, 502, 503, 504)
- **Structured Errors**: Clear error messages with developer details
- **Logging**: Comprehensive logging for debugging and monitoring

## Production Deployment

### Security Considerations

- Run as non-root user in Docker
- Use environment variables for sensitive configuration
- Implement proper network security (firewalls, VPNs)
- Monitor API usage and implement rate limiting if needed

### Monitoring

- Health check endpoint for load balancers
- Structured logging for observability
- Docker health checks for container orchestration

### Scaling

- Stateless design allows horizontal scaling
- Use load balancers for multiple instances
- Consider implementing Redis for session management if needed

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify API key and domain configuration
2. **Rate Limiting**: Implement exponential backoff for retries
3. **Network Issues**: Check firewall and network connectivity
4. **Validation Errors**: Review input parameter formats

### Logs

Check server logs for detailed error information:
```bash
docker logs freshdesk-mcp-server
```

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive error handling and validation
3. Include proper logging for all operations
4. Update documentation for new features

## License

This project is part of the MCP Servers collection. See the main repository for license information.
