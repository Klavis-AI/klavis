# Cal.com API Integration Server

A server that provides integration with Cal.com's API, offering tools for managing schedules, verified resources, and webhooks through both SSE and HTTP streaming interfaces.

## Features

- **Schedule Management**
  - Create, read, update, and delete schedules
  - Manage availability and overrides
  - Get default schedule

- **Verified Resources**
  - Email verification (request code, verify code)
  - Get verified emails and phones
  - Phone verification (currently limited functionality)

- **Webhooks**
  - Create, read, update, and delete webhooks
  - Configure webhook triggers and payload templates
  - Paginated listing of webhooks

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

### Verified Resources Tools
- `cal_request_email_verification_code`: Request email verification code
- `cal_verify_email_code`: Verify email with received code
- `cal_get_verified_emails`: List all verified emails
- `cal_get_verified_email_by_id`: Get specific verified email by ID
- `cal_get_verified_phones`: List verified phone numbers (paginated)
- `cal_get_verified_phone_by_id`: Get specific verified phone by ID

### Webhook Tools
- `cal_get_all_webhooks`: List all webhooks (paginated)
- `cal_create_webhook`: Create new webhook
- `cal_get_webhook`: Get specific webhook by ID
- `cal_update_webhook`: Update existing webhook
- `cal_delete_webhook`: Delete webhook by ID

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash