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
- A Mixpanel account with Service Account API access (Owner or Admin role for event tracking)
- Mixpanel Service Account credentials (username and secret)
- Mixpanel Project ID

### Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
export MIXPANEL_MCP_SERVER_PORT=5000  # Optional, defaults to 5000
export MIXPANEL_PROJECT_ID=your_project_id  # Required - your Mixpanel project ID
export MIXPANEL_SERVICE_ACCOUNT_USERNAME=your_service_account_username  # Optional, can be provided via header
export MIXPANEL_SERVICE_ACCOUNT_SECRET=your_service_account_secret  # Optional, can be provided via header
export MIXPANEL_PROJECT_TOKEN=your_project_token  # Optional, legacy token support
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

The server uses unified Mixpanel Service Account API authentication for all operations. Service accounts provide secure access to both data querying and event ingestion endpoints using Basic Authentication.

### Service Account Credentials

You can provide Service Account credentials and Project ID in two ways:

1. **Via HTTP Header** (recommended for per-request authentication):
```
x-auth-token: serviceaccount_username:serviceaccount_secret:project_id
```
Example:
```
x-auth-token: sa_abc123.mixpanel:def456ghi789:12345
```

Or without project_id (will use environment variable):
```
x-auth-token: sa_abc123.mixpanel:def456ghi789
```

2. **Via Environment Variables** (fallback if not provided in header):
```bash
export MIXPANEL_SERVICE_ACCOUNT_USERNAME=sa_abc123.mixpanel
export MIXPANEL_SERVICE_ACCOUNT_SECRET=def456ghi789
export MIXPANEL_PROJECT_ID=12345
```

### Requirements

- **Service Account Role**: Must be Owner or Admin for event tracking operations (/import endpoint)
- **Project ID**: Required for all operations to identify which project to work with
- **Legacy Token Support**: If `MIXPANEL_PROJECT_TOKEN` is set, it will be used for /track endpoint compatibility

### API Organization

Based on the [Mixpanel API documentation](https://developer.mixpanel.com/reference/overview), the server uses 4 distinct API endpoints:

1. **Ingestion API** (`api.mixpanel.com`): For importing events and updating user profiles
2. **Raw Data Export API** (`data.mixpanel.com/api/2.0/export`): For exporting raw event data
3. **Query API** (`mixpanel.com/api`): For calculated data (Insights, Funnels, Retention)
4. **App Management API** (`mixpanel.com/api/app`): For project management and administrative operations

### Client Architecture

The server uses 4 dedicated clients, one for each API endpoint:

- **`MixpanelIngestionClient`**: Handles Ingestion API (events & profiles)
- **`MixpanelExportClient`**: Handles Raw Data Export API (raw event export)
- **`MixpanelQueryClient`**: Handles Query API (calculated metrics, user profile queries)
- **`MixpanelAppAPIClient`**: Handles App Management API (projects, GDPR, schemas)

### API Usage Examples

```bash
# Test authentication (App Management API)
curl https://mixpanel.com/api/app/me \
  --user "serviceaccount_username:serviceaccount_secret"

# Import events (Ingestion API)
curl https://api.mixpanel.com/import?project_id=12345 \
  --user "serviceaccount_username:serviceaccount_secret" \
  -H "Content-Type: application/json" \
  -d '[{"event": "Test", "properties": {"time": 1618716477000, "distinct_id": "user123", "$insert_id": "unique-id"}}]'
```

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

## Available Tools

The server provides the following tools:

| Tool Name | Description | Required Parameters |
|-----------|-------------|-------------------|
| `mixpanel_import_events` | Import events using /import endpoint | `project_id`, `events` |
| `mixpanel_query_events` | Query raw event data with filtering | `from_date`, `to_date` |
| `mixpanel_get_event_count` | Get total event counts for date range | `from_date`, `to_date` |
| `mixpanel_get_top_events` | Get most popular events by count | `from_date`, `to_date` |
| `mixpanel_get_todays_top_events` | Get today's most popular events | None |
| `mixpanel_list_saved_funnels` | List all saved funnels with metadata | None |
| `mixpanel_get_projects` | Get all accessible projects | None |
| `mixpanel_get_project_info` | Get detailed project information | `project_id` |

## Error Handling

The server provides detailed error messages for common issues:
- Missing required parameters (service account credentials, project_id, distinct_id, etc.)
- Authentication failures (invalid service account credentials or insufficient permissions)
- API rate limiting (automatic handling with appropriate error messages)
- Network connectivity issues
- Invalid data formats and malformed requests
- Mixpanel-specific errors (quota exceeded, plan limitations)
- Service Account role errors (Owner/Admin required for event ingestion)

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