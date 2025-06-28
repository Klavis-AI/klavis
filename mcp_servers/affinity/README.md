# Affinity MCP Server

An MCP (Model Context Protocol) server that provides integration with [Affinity CRM](https://affinity.co) through their REST API.

## Features

This MCP server provides tools to interact with Affinity CRM, including:

### Lists
- Get all lists
- Get a specific list by ID
- Create new lists

### List Entries
- Get list entries for a specific list
- Get a specific list entry by ID
- Create new list entries
- Delete list entries

### Persons
- Search for persons
- Get a specific person by ID
- Create new persons
- Update existing persons
- Delete persons

### Organizations
- Search for organizations
- Get a specific organization by ID
- Create new organizations
- Update existing organizations
- Delete organizations

### Opportunities
- Search for opportunities
- Get a specific opportunity by ID
- Create new opportunities
- Update existing opportunities
- Delete opportunities

### Notes
- Get notes (optionally filtered by person, organization, or opportunity)
- Get a specific note by ID
- Create new notes
- Update existing notes
- Delete notes

### Field Values
- Get field values for entities
- Create new field values
- Update existing field values
- Delete field values

## Setup

### Prerequisites
- Python 3.12 or higher
- An Affinity account with API access
- Affinity API key (obtain from Settings Panel in Affinity web app)

### Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
export AFFINITY_MCP_SERVER_PORT=5000  # Optional, defaults to 5000
```

3. Run the server:
```bash
python server.py
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -f mcp_servers/affinity/Dockerfile -t affinity-mcp-server .
```

2. Run the container:
```bash
docker run -p 5000:5000 affinity-mcp-server
```

## Authentication

The server uses a custom authentication header with your Affinity API key. The API key should be provided in the `x-auth-token` header:

```
x-auth-token: your_api_key_here
```

## API Endpoints

The server provides endpoints for both transport methods:

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/messages/` - SSE message handling endpoint
- `/mcp` - StreamableHTTP endpoint for direct API calls

## Tool Usage Examples

### Get All Lists
```json
{
  "name": "affinity_get_lists",
  "arguments": {}
}
```

### Search for Persons
```json
{
  "name": "affinity_search_persons",
  "arguments": {
    "term": "john@example.com",
    "page_size": 10
  }
}
```

### Create a Person
```json
{
  "name": "affinity_create_person",
  "arguments": {
    "first_name": "John",
    "last_name": "Doe",
    "emails": ["john@example.com"],
    "organization_ids": [123]
  }
}
```

### Create a Note
```json
{
  "name": "affinity_create_note",
  "arguments": {
    "content": "Meeting notes from today's call",
    "person_ids": [456],
    "type": 0
  }
}
```

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters
- Authentication failures
- API rate limiting
- Network connectivity issues

## Rate Limiting

Affinity API has rate limits. The server will handle rate limit responses appropriately. See the [Affinity API documentation](https://api-docs.affinity.co/#rate-limits) for current limits.

## Contributing

1. Follow the existing code structure
2. Add new tools to the appropriate files in the `tools/` directory
3. Update `tools/__init__.py` to export new functions
4. Add tool definitions to `server.py`
5. Update this README with new functionality

## License

This project follows the same license as the parent Klavis project. 