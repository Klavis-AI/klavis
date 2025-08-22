# Zoom MCP Server

A Model Context Protocol (MCP) server that provides access to Zoom API functionality through various AI platforms using OAuth authentication.

## Features

- **Meeting Management**: Create, update, and delete Zoom meetings
- **User Management**: Manage Zoom users and their settings
- **Webinar Operations**: Handle webinar creation and management
- **Recording Management**: Access and manage meeting recordings
- **Real-time Communication**: Get live meeting status and participant information
- **OAuth Authentication**: Secure authentication using OAuth access tokens

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python server.py
   ```

## Authentication

**⚠️ IMPORTANT**: This server requires OAuth authentication for every request. The LLM client handles OAuth flow and provides access tokens.

### Required Header

All requests must include this authentication header:

- `x-zoom-access-token`: Your Zoom OAuth access token

### OAuth Flow (Handled by LLM Client)

The LLM client should handle the OAuth flow:

1. **Redirect User**: Send user to Zoom OAuth authorization URL
2. **Get Authorization Code**: User authorizes and returns code
3. **Exchange for Access Token**: Exchange code for access token
4. **Use Access Token**: Include token in `x-zoom-access-token` header

### OAuth Configuration

The LLM client needs to configure:

- **Client ID**: From your Zoom App
- **Client Secret**: From your Zoom App  
- **Redirect URI**: Your app's callback URL
- **Scopes**: Required permissions (e.g., `meeting:write`, `user:read`)

## API Endpoints

- **SSE**: `http://localhost:5000/sse`
- **StreamableHTTP**: `http://localhost:5000/mcp`

## Usage Examples

### Using with curl (StreamableHTTP)

```bash
curl -X POST http://localhost:5000/mcp \
  -H "x-zoom-access-token: YOUR_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Using with SSE

```bash
curl -N http://localhost:5000/sse \
  -H "x-zoom-access-token: YOUR_OAUTH_ACCESS_TOKEN"
```

### Using with MCP Client

```python
import mcp.client

client = mcp.client.ClientSession(
    "http://localhost:5000/mcp",
    headers={"x-zoom-access-token": "your_oauth_token"}
)

# List available tools
tools = await client.list_tools()

# Create a meeting
result = await client.call_tool("zoom_create_meeting", {
    "topic": "Team Standup",
    "duration": 30
})
```

## Tools Available

- `zoom_create_meeting`: Create a new Zoom meeting
- `zoom_get_meeting`: Retrieve meeting details
- `zoom_update_meeting`: Update meeting settings
- `zoom_delete_meeting`: Delete a meeting
- `zoom_list_meetings`: List all meetings for a user
- `zoom_get_meeting_participants`: Get meeting participant list
- `zoom_create_webinar`: Create a new webinar
- `zoom_get_user`: Get user information
- `zoom_list_users`: List all users in the account

## Security Features

- **OAuth Based**: Uses industry-standard OAuth 2.0 flow
- **No Stored Credentials**: Access tokens are never stored on the server
- **Per-Request Authentication**: Each request must provide valid access token
- **Token Validation**: Access tokens are validated before processing requests
- **Context Isolation**: Tokens are isolated per request using context variables

## Error Handling

The server returns appropriate HTTP status codes:

- `401 Unauthorized`: Missing or invalid OAuth access token
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Server-side errors

## Docker Deployment

```bash
docker build -t zoom-mcp-server .
docker run -p 5000:5000 zoom-mcp-server
```

## Testing

Run the test script to verify functionality:

```bash
python test_server.py
```

**Note**: The test script requires a valid Zoom OAuth access token to be provided.

## OAuth Scopes Required

For full functionality, the Zoom App should request these scopes:

- `meeting:write` - Create/edit/delete meetings
- `meeting:read` - Read meeting information
- `user:read` - Read user information
- `webinar:write` - Create/edit webinars
- `webinar:read` - Read webinar information

## Client Integration

### For LLM Platforms

The LLM client should:

1. **Handle OAuth Flow**: Manage the complete OAuth authorization process
2. **Store Tokens Securely**: Store access tokens securely (encrypted, not in plain text)
3. **Refresh Tokens**: Handle token refresh when they expire
4. **Include in Headers**: Add `x-zoom-access-token` to all MCP requests

### Example Client Flow

```python
# 1. Start OAuth flow
auth_url = f"https://zoom.us/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

# 2. User authorizes and returns code
# 3. Exchange code for access token
token_response = requests.post("https://zoom.us/oauth/token", data={
    "grant_type": "authorization_code",
    "code": auth_code,
    "redirect_uri": REDIRECT_URI
}, auth=(CLIENT_ID, CLIENT_SECRET))

access_token = token_response.json()["access_token"]

# 4. Use with MCP server
mcp_headers = {"x-zoom-access-token": access_token}
```
