# Mixpanel MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Mixpanel analytics platform. This server enables tracking events, managing user profiles, and retrieving analytics data from Mixpanel.

## Features

### Event Tracking
- **Track Events**: Send events to Mixpanel with custom properties
- **Update User Profiles**: Set or update user profile properties
- **Increment Properties**: Increment numerical properties in user profiles

### Analytics & Reporting
- **Get Events Data**: Retrieve event data within date ranges
- **Event Properties Analysis**: Analyze specific event properties
- **Funnel Analysis**: Get funnel conversion data
- **Retention Analysis**: Analyze user retention metrics
- **Segmentation**: Segment users based on event properties
- **Export Events**: Export raw event data

## Setup

### Prerequisites
- Node.js (version 18 or higher)
- A Mixpanel account with:
  - Project Token (for event tracking)
  - Username and API Secret (for analytics queries)

### Installation

1. Clone this repository and navigate to the mixpanel directory:
```bash
cd mcp_servers/mixpanel
```

2. Install dependencies:
```bash
npm install
```

3. Copy the environment template and configure your credentials:
```bash
cp .env.example .env
```

4. Edit `.env` with your Mixpanel credentials:
```bash
MIXPANEL_PROJECT_TOKEN=your_project_token_here
MIXPANEL_USERNAME=your_username_here
MIXPANEL_SECRET=your_api_secret_here
```

### Getting Mixpanel Credentials

1. **Project Token**: Found in your Mixpanel project settings under "Access Keys"
2. **Username/Secret**: Create a service account in Mixpanel or use your account credentials

## Running the Server

### Local Development

Start the server:
```bash
npm start
```

The server will run on port 5001 by default.

### Docker

Build and run with Docker:
```bash
# Build the Docker image
npm run docker:build

# Run the container
npm run docker:run
```

Or manually:
```bash
# Build from the project root
docker build -t mixpanel-mcp-server -f mcp_servers/mixpanel/Dockerfile .

# Run with environment variables
docker run -p 5000:5000 --env-file .env mixpanel-mcp-server
```

## Available Tools

### Event Tracking Tools

#### `mixpanel_track_event`
Track an event with optional properties.
- `distinct_id` (required): User identifier
- `event_name` (required): Name of the event
- `properties` (optional): Additional event properties

#### `mixpanel_update_user_profile`
Update user profile properties.
- `distinct_id` (required): User identifier
- `properties` (required): Properties to set/update

#### `mixpanel_increment_user_property`
Increment a numerical property.
- `distinct_id` (required): User identifier
- `property` (required): Property name to increment
- `value` (optional): Increment value (default: 1)

### Analytics Tools

#### `mixpanel_get_events`
Get event data for specific events.
- `event_names` (required): Array of event names
- `from_date` (required): Start date (YYYY-MM-DD)
- `to_date` (required): End date (YYYY-MM-DD)
- `unit` (optional): Time unit (hour, day, week, month)

#### `mixpanel_get_event_properties`
Analyze event properties.
- `event_name` (required): Event name
- `property_name` (required): Property to analyze
- `values` (optional): Specific values to filter
- `from_date` (optional): Start date
- `to_date` (optional): End date

#### `mixpanel_get_funnel_data`
Get funnel analysis data.
- `funnel_id` (required): Funnel identifier
- `from_date` (required): Start date
- `to_date` (required): End date
- `unit` (optional): Time unit

#### `mixpanel_get_retention_data`
Get retention analysis.
- `from_date` (required): Start date
- `to_date` (required): End date
- `retention_type` (optional): birth or compounded
- `born_event` (optional): Event defining user birth

#### `mixpanel_get_segmentation_data`
Get segmentation analysis.
- `event` (required): Event to analyze
- `from_date` (required): Start date
- `to_date` (required): End date
- `on` (optional): Property to segment on
- `unit` (optional): Time unit

#### `mixpanel_export_events`
Export raw event data.
- `from_date` (required): Start date
- `to_date` (required): End date
- `events` (optional): Specific events to export

## Usage Examples

### Track a User Registration Event
```json
{
  "tool": "mixpanel_track_event",
  "arguments": {
    "distinct_id": "user123",
    "event_name": "User Registered",
    "properties": {
      "source": "organic",
      "plan": "premium"
    }
  }
}
```

### Update User Profile
```json
{
  "tool": "mixpanel_update_user_profile",
  "arguments": {
    "distinct_id": "user123",
    "properties": {
      "$email": "user@example.com",
      "$name": "John Doe",
      "plan": "premium"
    }
  }
}
```

### Get Event Data
```json
{
  "tool": "mixpanel_get_events",
  "arguments": {
    "event_names": ["User Registered", "Purchase"],
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "unit": "day"
  }
}
```

## Error Handling

The server includes comprehensive error handling for:
- Missing or invalid credentials
- API rate limiting
- Invalid date formats
- Network connectivity issues

## Security

- Store credentials securely in environment variables
- Use service accounts with minimal required permissions
- Regularly rotate API secrets
- Monitor API usage in Mixpanel dashboard

## Development

To run in development mode with auto-reload:
```bash
npm run dev
```

For TypeScript compilation:
```bash
npm run build
```

## License

MIT License - see LICENSE file for details.
