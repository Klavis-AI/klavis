# Fireflies MCP Server

This directory contains a Model Context Protocol (MCP) server for integrating [Fireflies.ai](https://fireflies.ai/) capabilities into applications like Claude, Cursor, and other LLM clients. It allows leveraging Fireflies' powerful meeting transcription and AI-powered analysis features through a standardized protocol.

## Features

This server exposes **5 comprehensive tools** covering the full Fireflies.ai functionality:

### Meeting Management (1 tool)

- `fireflies_list_meetings`: Retrieve recent meetings with optional filters for date range and user

### Transcript Operations (2 tools)

- `fireflies_get_transcript`: Fetch full meeting transcript by transcript ID with optional summary and action items
- `fireflies_export_transcript`: Download transcript in various formats (txt, pdf, docx, srt, vtt)

### Search and Analysis (2 tools)

- `fireflies_search_meetings`: Search across meeting content using natural language queries with optional filters
- `fireflies_get_meeting_summary`: Extract key insights, action items, decisions, and topics from meeting transcripts

## Prerequisites

- **Node.js:** Version 18.0.0 or higher
- **npm:** Node Package Manager (usually comes with Node.js)
- **TypeScript:** For development and building
- **Fireflies API Key:** Obtainable from your [Fireflies.ai account](https://fireflies.ai/)

## Environment Setup

Before running the server, you need to configure your Fireflies API credentials.

1. Create an environment file:
   cp .env.example .env

**Note:** If `.env.example` doesn't exist, create `.env` directly:

touch .env

2. Edit `.env` and add your Fireflies API key:

Fireflies API credentials
FIREFLIES_API_KEY=your-actual-api-key-here
PORT=5000

- `FIREFLIES_API_KEY` (Required): Your API key for the Fireflies.ai API. You can obtain this from your Fireflies account settings.
- `PORT` (Optional): The port number for the server to listen on. Defaults to 5000.

## Getting Your Fireflies API Key

### For Development (API Key):

1. Visit [Fireflies.ai](https://fireflies.ai/) and sign in to your account
2. Navigate to your account settings or integrations section
3. Look for "API" or "Developer" settings
4. Generate or copy your API key
5. Use this key as your `FIREFLIES_API_KEY`

**Note:** Fireflies.ai currently does not offer a public API. This server implementation is designed for when the API becomes available or for integration with reverse-engineered endpoints.

## Running Locally

### Using Node.js / npm

1. **Install Dependencies:**
   npm install

2. **Build the Server Code:**

npm run build

3. **Start the Server:**

npm start

The server will start using the environment variables defined in `.env` and listen on port 5000 (or the port specified by the `PORT` environment variable).

## API Reference

### Key Tool Examples

#### Meeting Management

##### `fireflies_list_meetings`

Retrieve recent meetings from Fireflies with optional filters.

**Parameters:**

- `limit` (number, optional): Number of meetings to retrieve (1-100), default: 10
- `offset` (number, optional): Number of meetings to skip for pagination, default: 0
- `start_date` (string, optional): Start date filter (YYYY-MM-DD format)
- `end_date` (string, optional): End date filter (YYYY-MM-DD format)
- `user_id` (string, optional): Filter meetings by specific user ID

#### Transcript Operations

##### `fireflies_get_transcript`

Fetch full meeting transcript by transcript ID.

**Parameters:**

- `transcript_id` (string, required): The ID of the transcript to retrieve
- `include_summary` (boolean, optional): Include meeting summary in response, default: false
- `include_action_items` (boolean, optional): Include action items in response, default: false

##### `fireflies_export_transcript`

Download transcript in various formats.

**Parameters:**

- `transcript_id` (string, required): The ID of the transcript to export
- `format` (string, optional): Export format ("txt", "pdf", "docx", "srt", "vtt"), default: "txt"
- `include_timestamps` (boolean, optional): Include timestamps in export, default: true
- `include_speaker_labels` (boolean, optional): Include speaker labels in export, default: true

#### Search and Analysis

##### `fireflies_search_meetings`

Search across meeting content using natural language queries.

**Parameters:**

- `query` (string, required): Search query to find in meeting content
- `limit` (number, optional): Number of results to return (1-50), default: 10
- `filters` (object, optional): Additional search filters
  - `start_date` (string, optional): Start date filter (YYYY-MM-DD)
  - `end_date` (string, optional): End date filter (YYYY-MM-DD)
  - `user_id` (string, optional): Filter by user ID
  - `meeting_title` (string, optional): Filter by meeting title

**Example:**
{
"query": "action items discussed",
"limit": 20,
"filters": {
"start_date": "2024-01-01",
"end_date": "2024-01-31"
}
}

##### `fireflies_get_meeting_summary`

Extract key insights and summaries from meeting transcripts.

**Parameters:**

- `transcript_id` (string, required): The ID of the transcript to summarize
- `summary_type` (string, optional): Type of summary ("overview", "action_items", "key_topics", "decisions"), default: "overview"
- `include_timestamps` (boolean, optional): Include timestamps in summary, default: false

## Authentication

The server supports two methods of authentication:

1. **Environment Variable (Recommended):** Set `FIREFLIES_API_KEY` in your `.env` file.
2. **HTTP Header:** Pass the API key as `x-auth-token` header in requests to the MCP server.

## Protocol Support

This server supports both MCP protocol versions:

- **Streamable HTTP Transport** (Protocol Version 2025-03-26) - **Recommended**
  - Endpoint: `POST /mcp`
  - Single request/response model
  - Simpler implementation and better performance

- **HTTP+SSE Transport** (Protocol Version 2024-11-05) - **Legacy Support**
  - Endpoints: `GET /sse`, `POST /messages`, `DELETE /sse/:sessionId`
  - Persistent connections with session management
  - Server-Sent Events for real-time communication

### Additional Endpoints

- `GET /health` - Health check endpoint
- `GET /status` - Detailed status with system information and available tools
- `GET /sse/status` - SSE connection status and monitoring

## Testing with MCP Clients

### Claude Desktop

Add to your MCP configuration:

{
"mcpServers": {
"fireflies": {
"command": "node",
"args": ["path/to/your/server/dist/index.js"],
"env": {
"FIREFLIES_API_KEY": "your_actual_api_key_here"
}
}
}
}

### Cursor IDE

1. Create `.cursor/mcp.json` in your project:

{
"mcpServers": {
"fireflies": {
"url": "http://localhost:5000/mcp",
"headers": {
"x-auth-token": "your_actual_api_key_here"
}
}
}
}

2. Test with natural language:

- "List my recent meetings from this week"
- "Get the transcript for meeting ID abc123"
- "Search for meetings where we discussed project deadlines"
- "Generate a summary of action items from transcript xyz789"
- "Export the transcript as a PDF with timestamps"

## Error Handling

The server includes comprehensive error handling:

- **Authentication errors**: Invalid or missing API keys, insufficient permissions
- **API errors**: Fireflies API rate limits, invalid parameters, resource not found
- **Connection errors**: Network issues and timeouts
- **Validation errors**: Invalid input parameters, missing required fields

All errors are returned in proper JSON-RPC format with descriptive error messages and appropriate HTTP status codes.

## Rate Limiting

The server respects Fireflies' API rate limits and includes:

- Automatic retry logic with exponential backoff
- Connection pooling for efficient API usage
- Request queuing to prevent rate limit violations

## Development

- **Building:** `npm run build` (compile TypeScript to JavaScript)
- **Development:** `npm run dev` (build and run with file watching)
- **Linting:** `npm run lint` (check code style)
- **Format:** `npm run format` (format code with Prettier)
- **Testing:** `npm test` (run test suite)
- **Docker:** `npm run docker:build` and `npm run docker:run` (containerized deployment)

## Docker Support

### Building Docker Image

npm run docker:build

### Running with Docker

npm run docker:run

Make sure to create a `.env` file with your `FIREFLIES_API_KEY` before running the Docker container.

## Support

For issues related to this MCP server, please create an issue in the repository.
For Fireflies API questions, consult the [Fireflies.ai documentation](https://fireflies.ai/) or contact their support team.
