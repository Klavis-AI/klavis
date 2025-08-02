# Cal.com API Integration Server

A server that provides integration with Cal.com's API, offering tools for managing schedules, verified resources, and webhooks through both SSE and HTTP streaming interfaces.

## Features

- **Schedule Management**
  - Create, read, update, and delete schedules
  - Manage availability and overrides
  - Get default schedule


## API Endpoints

The server provides two transport mechanisms:

### 1. Server-Sent Events (SSE) Endpoint
- **URL**: `/sse`
- **Method**: GET
- **Headers**:
  - `x-auth-token`: Your Cal.com API token (optional, can be set per request)

### 2. Streamable HTTP Endpoint
- **URL**: `/mcp`
- **Method**: POST
- **Headers**:
  - `x-auth-token`: Your Cal.com API token (optional, can be set per request)
- **Content-Type**: `application/json`

## Available Tools

### Schedule Tools
- `cal_get_all_schedules`: List all schedules
- `cal_create_a_schedule`: Create new schedule
- `cal_update_a_schedule`: Update existing schedule
- `cal_get_default_schedule`: Get default schedule
- `cal_get_schedule`: Get specific schedule by ID
- `cal_delete_a_schedule`: Delete schedule by ID