# Mixpanel MCP Server

MCP server for [Mixpanel](https://mixpanel.com) analytics platform.

## Features

- **Event Tracking**: Track single or batch events
- **User Profiles**: Manage user profile data
- **Analytics**: Query events, get counts, and top events
- **Funnels**: List and access saved funnels

## Setup

### Prerequisites
- Python 3.12+
- Mixpanel Service Account (Owner/Admin role)

### Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export MIXPANEL_SERVICE_ACCOUNT_USERNAME=sa_abc123.mixpanel
export MIXPANEL_SERVICE_ACCOUNT_SECRET=your_secret
```

3. Run the server:
```bash
python server.py
```

## Authentication

Provide credentials via HTTP header (includes project ID):
```
x-auth-token: serviceaccount_username:serviceaccount_secret:project_id
```

Or set environment variables (project ID provided in header):
```bash
export MIXPANEL_SERVICE_ACCOUNT_USERNAME=sa_abc123.mixpanel
export MIXPANEL_SERVICE_ACCOUNT_SECRET=your_secret
```

## Available Tools

| Tool | Description |
|------|-------------|
| `mixpanel_send_events` | Send events to Mixpanel using /import endpoint |
| `mixpanel_get_events` | Get all event names in a project |
| `mixpanel_get_event_properties` | Get available properties for an event |
| `mixpanel_get_event_property_values` | Get possible values for an event property |
| `mixpanel_run_funnels_query` | Run funnel analysis for conversion tracking |
| `mixpanel_run_segmentation_query` | Analyze events with filters and grouping |
| `mixpanel_run_retention_query` | Track user retention over time |
| `mixpanel_run_frequency_query` | Analyze user engagement frequency |
| `mixpanel_get_projects` | Get all accessible projects |

## Docker

```bash
# Build
docker build -f mcp_servers/mixpanel/Dockerfile -t mixpanel-mcp-server .

# Run
docker run -p 5000:5000 mixpanel-mcp-server
```