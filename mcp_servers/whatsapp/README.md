# WhatsApp MCP Server

A Model Context Protocol (MCP) server for integrating with the WhatsApp Business API. This server provides tools to send text messages through WhatsApp.

## Features

- **Send Text Messages**: Send text messages with optional URL preview

## Prerequisites

- Node.js 18.0.0 or higher
- WhatsApp Business API access
- WhatsApp Business Phone Number ID
- Access Token for WhatsApp Business API

## Installation

1. Navigate to the WhatsApp MCP server directory:
```bash
cd mcp_servers/whatsapp
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

## Configuration

Set the following environment variable:

- `WHATSAPP_ACCESS_TOKEN`: Your WhatsApp Business API access token

Alternatively, you can provide the access token via request header:
- `x-access-token`: WhatsApp access token

Note: The WhatsApp Business Phone Number ID is provided as a parameter in each tool call, not as an environment variable.

## Usage

### Starting the Server

```bash
npm start
```

The server will start on port 5000 and supports both:
- **Streamable HTTP Transport** (recommended): POST `/mcp`
- **HTTP+SSE Transport** (deprecated): GET `/sse` and POST `/messages`

### Available Tools

#### whatsapp_send_text
Send a text message to a WhatsApp user.

**Parameters:**
- `phone_number_id` (required): WhatsApp Business phone number ID (e.g., 123456789012345)
- `to` (required): WhatsApp user phone number in international format (e.g., +16505551234)
- `text` (required): Body text of the message (max 1024 characters)
- `preview_url` (optional): Enable link preview for URLs in the text (default: false)

**Example:**
```json
{
  "phone_number_id": "123456789012345",
  "to": "+16505551234",
  "text": "Hello! Check out our website: https://example.com",
  "preview_url": true
}
```

## API Endpoints

### Streamable HTTP Transport (Recommended)
- **POST** `/mcp`: Handle MCP requests using the streamable HTTP transport
- **GET** `/mcp`: Returns 405 Method Not Allowed
- **DELETE** `/mcp`: Returns 405 Method Not Allowed

### HTTP+SSE Transport (Deprecated)
- **GET** `/sse`: Establish SSE connection for MCP communication
- **POST** `/messages`: Handle MCP messages with session ID

## Development

### Scripts

- `npm run build`: Build the TypeScript project
- `npm start`: Start the server
- `npm run lint`: Run ESLint
- `npm run lint:fix`: Fix ESLint issues
- `npm run format`: Format code with Prettier

### Project Structure

```
mcp_servers/whatsapp/
├── index.ts          # Main server implementation
├── package.json      # Project configuration
├── tsconfig.json     # TypeScript configuration
├── .eslintrc.json    # ESLint configuration
└── README.md         # This file
```

## Error Handling

The server includes comprehensive error handling for:
- Missing authentication credentials
- Invalid phone number formats
- API errors from WhatsApp Business API
- Network connectivity issues

All errors are logged and returned in a structured format.

## Technical Details

- Uses WhatsApp Business API v23.0
- Supports AsyncLocalStorage for request context management
- Built with Express.js and MCP SDK
- Implements both current and legacy MCP transport protocols

## License

MIT License 