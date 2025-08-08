# Google Meet MCP Server

A TypeScript MCP server for Google Meet that lets you create meeting spaces and access conference records through the Meet API v2.

## What it does

- Create new Google Meet spaces and get meeting links
- Retrieve details about existing meeting spaces
- Access conference records from completed meetings
- View participant information from past meetings
- Works directly with Meet API v2 (no Calendar API needed)

## Available Tools

### Meeting Space Operations
- `google_meet_create_space`: Create a new Google Meet space
- `google_meet_get_space`: Retrieve details of a Google Meet space

### Conference Records Operations  
- `google_meet_list_conference_records`: List conference records for completed meetings
- `google_meet_get_conference_record`: Get details of a specific conference record
- `google_meet_list_participants`: List participants from a conference record

## Requirements

- Node.js 18+ (Node 22 recommended)
- A Google Cloud project with required APIs enabled

### Google Cloud Setup

1. Create or select a project in Google Cloud Console
2. Enable the Google Meet API
3. Set up OAuth 2.0 credentials
4. Get access tokens with the right scopes
5. Pass tokens in the `x-auth-token` header

## Configuration

Create a `.env` file in `mcp_servers/google_meet/` (or configure environment variables in your deployment):

```bash
# Server
GOOGLE_MEET_MCP_SERVER_PORT=5000
```

## Authentication

Send your OAuth access token in the `x-auth-token` header with each request. Make sure the token has the required scopes.

This works the same way as our other Google MCP servers.

## Running the Server

### Local Development
```bash
cd mcp_servers/google_meet
npm install
npm run build
npm start
```

The server runs on port `5000` by default (configurable via `GOOGLE_MEET_MCP_SERVER_PORT`).

**Endpoints:**
- HTTP: `POST /mcp`
- SSE: `GET /sse`

### Docker
```bash
# From repo root
docker build -t google-meet-mcp-server -f mcp_servers/google_meet/Dockerfile .

# Using .env
docker run --rm -p 5000:5000 --env-file mcp_servers/google_meet/.env google-meet-mcp-server
```

## API Endpoints

- **SSE**: `GET /sse` — Server-Sent Events endpoint for MCP communication
- **Streamable HTTP**: `POST /mcp` — Streamable HTTP endpoint for MCP communication

## Usage Examples

### Create a Meeting Space
```json
{
  "name": "google_meet_create_space",
  "arguments": {}
}
```

The Meet API doesn't let you set custom names or descriptions when creating spaces - you just get a working meeting link.

### Get Meeting Space Details
```json
{
  "name": "google_meet_get_space", 
  "arguments": {
    "space_id": "spaces/abc123"
  }
}
```

### List Conference Records
```json
{
  "name": "google_meet_list_conference_records",
  "arguments": {
    "page_size": 10
  }
}
```

### Get Participants from Conference Record
```json
{
  "name": "google_meet_list_participants",
  "arguments": {
    "conference_record_id": "conferenceRecords/abc123",
    "page_size": 50
  }
}
```

## Permissions & Scopes

Required scopes:
- `https://www.googleapis.com/auth/meetings.space.created` (for creating meeting spaces)
- `https://www.googleapis.com/auth/meetings.space.readonly` (for reading meeting space information)
- `https://www.googleapis.com/auth/meetings.readonly` (for conference records and participant information)

## Important Notes

- Conference records only show up after meetings end
- Meeting spaces stick around until deleted
- The public Meet API is pretty limited - you can't list all spaces, update names, or delete spaces
- Error messages will tell you what went wrong (auth issues, bad requests, etc.)

## Tech Stack

- TypeScript, Express
- `@modelcontextprotocol/sdk`
- `node-fetch` (for REST API calls)
- `zod`, `zod-to-json-schema`
- `dotenv`

## License

This project follows the same license as the parent Klavis project.