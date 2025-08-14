# Mixpanel MCP Server

An MCP (Model Context Protocol) server that provides integration with [Mixpanel](https://mixpanel.com) analytics platform through their REST API.

## Features

This MCP server provides tools to interact with Mixpanel analytics, including:

### Event Tracking
- Track single events with custom properties
- Track batch events for better performance (up to 50 events per batch)
- Support for user identification and custom properties

### User Profile Management  
- Set user profile properties with various operations
- Get user profile data
- Get user event activity and timeline
- Support for all Mixpanel People operations

### Analytics & Reporting
- Query raw event data with advanced filtering
- Get event counts for specific time periods
- Get top events by popularity
- Get today's top events for real-time insights
- Filter by date range, event type, and custom properties

### Funnels
- List all saved funnels with metadata
- Access funnel information including steps and creators

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

The server uses custom authentication headers with your Mixpanel credentials. You can find these in your Mixpanel project settings:

```
x-project-token: your_project_token_here
x-api-secret: your_api_secret_here
```

- **Project Token**: Required for event tracking and user profile operations
- **API Secret**: Required for data querying, user profile retrieval, and analytics

**Alternative Authentication (Service Account):**
For some operations, you can also use service account credentials:
- Service Account Username
- Service Account Secret

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

### Get Event Count
```json
{
  "name": "mixpanel_get_event_count",
  "arguments": {
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "event": "Purchase"
  }
}
```

### Get Top Events
```json
{
  "name": "mixpanel_get_top_events",
  "arguments": {
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "limit": 20
  }
}
```

### Get User Event Activity
```json
{
  "name": "mixpanel_get_profile_event_activity",
  "arguments": {
    "distinct_id": "user123",
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "limit": 50
  }
}
```

## Available Tools

The server provides the following tools:

| Tool Name | Description | Required Parameters |
|-----------|-------------|-------------------|
| `mixpanel_track_event` | Track custom events with properties | `event` |
| `mixpanel_set_user_profile` | Set/update user profile properties | `distinct_id` |
| `mixpanel_get_user_profile` | Retrieve user profile data | `distinct_id` |
| `mixpanel_query_events` | Query raw event data with filtering | `from_date`, `to_date` |
| `mixpanel_track_batch_events` | Track multiple events in batch | `events` |
| `mixpanel_get_event_count` | Get total event counts for date range | `from_date`, `to_date` |
| `mixpanel_get_top_events` | Get most popular events by count | `from_date`, `to_date` |
| `mixpanel_get_todays_top_events` | Get today's most popular events | None |
| `mixpanel_get_profile_event_activity` | Get user's event activity timeline | `distinct_id` |
| `mixpanel_list_saved_funnels` | List all saved funnels with metadata | None |

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters (project token, API secret, distinct_id, etc.)
- Authentication failures (invalid credentials)
- API rate limiting (automatic handling with appropriate error messages)
- Network connectivity issues
- Invalid data formats and malformed requests
- Mixpanel-specific errors (quota exceeded, plan limitations)

## Rate Limiting

Mixpanel API has rate limits that vary by plan type. The server will handle rate limit responses appropriately with informative error messages. For current limits, see the [Mixpanel API documentation](https://developer.mixpanel.com/reference/api-rate-limits).

## Contributing

1. Follow the existing code structure
2. Add new tools to the appropriate files in the `tools/` directory
3. Update `tools/__init__.py` to export new functions
4. Add tool definitions to `server.py`
5. Update this README with new functionality

## License

This project follows the same license as the parent Klavis project.