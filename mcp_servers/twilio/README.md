# Twilio MCP Server

A Model Context Protocol (MCP) server for Twilio communications API, providing tools for sending SMS/MMS messages, managing phone numbers, and handling message operations.

## Features

- **Send SMS**: Send text messages to phone numbers
- **Send MMS**: Send multimedia messages with media URLs
- **List Messages**: Retrieve recent messages from your Twilio account
- **Get Message Details**: Get detailed information about specific messages
- **Redact Messages**: Clear message body content (Twilio's version of deletion)
- **List Phone Numbers**: View available phone numbers in your account

## Prerequisites

- Python 3.12+
- Twilio account with Account SID, Auth Token, and Phone Number
- Docker (optional, for containerized deployment)

## Environment Variables

Set the following environment variables:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
TWILIO_MCP_SERVER_PORT=5000  # Optional, defaults to 5000
```

## Installation

### Local Development

1. Clone the repository
2. Navigate to the twilio server directory:
   ```bash
   cd mcp_servers/twilio
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables (see above)

5. Run the server:
   ```bash
   python server.py
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t twilio-mcp-server .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 \
     -e TWILIO_ACCOUNT_SID=your_account_sid \
     -e TWILIO_AUTH_TOKEN=your_auth_token \
     -e TWILIO_PHONE_NUMBER=your_twilio_phone_number \
     twilio-mcp-server
   ```

## Usage

The server exposes the following MCP tools:

### `twilio_send_sms`
Send an SMS message.
- **Parameters**:
  - `to` (string, required): Phone number to send to (e.g., "+1234567890")
  - `body` (string, required): Message content

### `twilio_send_mms`
Send an MMS message with media.
- **Parameters**:
  - `to` (string, required): Phone number to send to
  - `media_url` (string, required): URL of the media to send
  - `body` (string, optional): Optional message text

### `twilio_list_messages`
List recent messages from your account.
- **Parameters**:
  - `limit` (integer, optional): Number of messages to retrieve (default: 20, max: 100)

### `twilio_get_message_details`
Get detailed information about a specific message.
- **Parameters**:
  - `sid` (string, required): Message SID

### `twilio_redact_message`
Redact (clear the body of) a message.
- **Parameters**:
  - `sid` (string, required): Message SID

### `twilio_list_phone_numbers`
List phone numbers available in your account.
- **Parameters**: None

## API Endpoints

The server runs on port 5001 by default and provides:

- `/sse` - Server-Sent Events transport
- `/messages/` - SSE message handling
- `/mcp` - StreamableHTTP transport

## Error Handling

The server includes comprehensive error handling for:
- Missing environment variables
- Invalid Twilio credentials
- API rate limits
- Network connectivity issues
- Invalid message parameters

## Security

- Credentials are loaded from environment variables
- Auth tokens can be passed via HTTP headers (`x-auth-token`)
- All API calls are logged for debugging purposes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Klavis AI open-source ecosystem. 