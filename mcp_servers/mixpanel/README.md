# Mixpanel MCP Server

An MCP (Model Context Protocol) server that provides integration with [Mixpanel](https://mixpanel.com) analytics platform through their REST API.

## Features

This MCP server provides tools to interact with Mixpanel analytics, including:

### Event Tracking
- Track single events with custom properties
- Track batch events for better performance
- Support for user identification and custom properties

### User Profile Management
- Set user profile properties
- Get user profile data
- Support for various operations ($set, $set_once, $add, etc.)

### Data Querying
- Query raw event data
- Filter by date range, event type, and custom properties

## Setup

### Prerequisites
- Python 3.12 or higher
- A Mixpanel account with API access
- Mixpanel project token and API secret

### Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
export MIXPANEL_MCP_SERVER_PORT=5000  # Optional, defaults to 5000
```

3. Run the server:
```bash
python server.py
```

### Docker Setup

1. Build the Docker image:
```bash
docker build -f mcp_servers/mixpanel/Dockerfile -t mixpanel-mcp-server .
```

2. Run the container:
```bash
docker run -p 5000:5000 mixpanel-mcp-server
```

## Authentication

The server uses custom authentication headers with your Mixpanel credentials:

```
x-project-token: your_project_token_here
x-api-secret: your_api_secret_here
```

- **Project Token**: Required for event tracking and user profile operations
- **API Secret**: Required for data querying and user profile retrieval

## API Endpoints

The server provides endpoints for both transport methods:

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/messages/` - SSE message handling endpoint
- `/mcp` - StreamableHTTP endpoint for direct API calls

## Tool Usage Examples

### Track an Event
```json
{
  "name": "mixpanel_track_event",
  "arguments": {
    "event": "Page View",
    "properties": {
      "page": "/dashboard",
      "browser": "Chrome"
    },
    "distinct_id": "user123"
  }
}
```

### Set User Profile
```json
{
  "name": "mixpanel_set_user_profile",
  "arguments": {
    "distinct_id": "user123",
    "properties": {
      "name": "John Doe",
      "email": "john@example.com",
      "plan": "premium"
    },
    "operation": "$set"
  }
}
```

### Query Events
```json
{
  "name": "mixpanel_query_events",
  "arguments": {
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "event": "Purchase",
    "limit": 100
  }
}
```

### Track Batch Events
```json
{
  "name": "mixpanel_track_batch_events",
  "arguments": {
    "events": [
      {
        "event": "Page View",
        "properties": {"page": "/home"},
        "distinct_id": "user123"
      },
      {
        "event": "Button Click",
        "properties": {"button": "subscribe"},
        "distinct_id": "user123"
      }
    ]
  }
}
```

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters
- Authentication failures
- API rate limiting
- Network connectivity issues
- Invalid data formats

## Rate Limiting

Mixpanel API has rate limits. The server will handle rate limit responses appropriately. See the [Mixpanel API documentation](https://developer.mixpanel.com/reference/api-rate-limits) for current limits.

## Contributing

1. Follow the existing code structure
2. Add new tools to the appropriate files in the `tools/` directory
3. Update `tools/__init__.py` to export new functions
4. Add tool definitions to `server.py`
5. Update this README with new functionality

## License

This project follows the same license as the parent Klavis project.