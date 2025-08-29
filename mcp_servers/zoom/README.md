# Zoom MCP Server

A Model Context Protocol (MCP) server that provides access to Zoom API functionality through various AI platforms using OAuth authentication with device flow support.

## Features

- **Meeting Management**: Create, update, and delete Zoom meetings
- **User Management**: Manage Zoom users and their settings
- **Webinar Operations**: Handle webinar creation and management
- **Recording Management**: Access and manage meeting recordings
- **Real-time Communication**: Get live meeting status and participant information
- **OAuth Authentication**: Secure authentication using OAuth access tokens
- **Device Flow OAuth**: Easy authentication via URL and code entry

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your Zoom App Client ID:
   ```python
   # In tools/auth.py, update the ZOOM_OAUTH_CONFIG
   ZOOM_OAUTH_CONFIG = {
       "client_id": "your_zoom_client_id_here",  # Replace with your actual Client ID
       # ... other config
   }
   ```

3. Run the server:
   ```bash
   python server.py
   ```

## Authentication

### **Option 1: Device Flow OAuth (Recommended)**

The easiest way to authenticate is using the built-in device flow OAuth:

#### **Using the Authentication Tool**
```python
import mcp.client

client = mcp.client.ClientSession("http://localhost:5000/mcp")

# Call the zoom_authenticate_device_flow tool
result = await client.call_tool("zoom_authenticate_device_flow", {})
# This will provide a URL and code for the user to visit
```

#### **Using the Test Script**
```bash
python auth_test.py
```

This will:
1. Start the device flow
2. Display a URL and code
3. Wait for user authorization
4. Return an access token

### **Option 2: Manual OAuth Flow**

The LLM client handles the OAuth flow:

1. **Redirect User**: Send user to Zoom OAuth authorization URL
2. **Get Authorization Code**: User authorizes and returns code
3. **Exchange for Access Token**: Exchange code for access token
4. **Use Access Token**: Include token in `x-zoom-access-token` header

### **Required Header**

All requests must include this authentication header:

- `x-zoom-access-token`: Your Zoom OAuth access token

### **Getting Zoom App Credentials**

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/)
2. Sign in with your Zoom account
3. Click "Develop" → "Build App"
4. Choose "OAuth" app type
5. Fill in app information and create
6. Copy the Client ID and configure it in the server

## API Endpoints

- **SSE**: `http://localhost:5000/sse`
- **StreamableHTTP**: `http://localhost:5000/mcp`

## Usage Examples

### **Device Flow Authentication**

```python
import mcp.client

client = mcp.client.ClientSession("http://localhost:5000/mcp")

# Authenticate using device flow
auth_result = await client.call_tool("zoom_authenticate_device_flow", {})
print(auth_result)  # Will show URL and code to visit
```

### **Using with curl (StreamableHTTP)**

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

### **Using with SSE**

```bash
curl -N http://localhost:5000/sse \
  -H "x-zoom-access-token: YOUR_OAUTH_ACCESS_TOKEN"
```

### **Using with MCP Client**

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

- `zoom_authenticate_device_flow`: Authenticate with Zoom using device flow OAuth
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
- **Device Flow**: Secure authentication without redirect URLs
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

### **Test Device Flow Authentication**
```bash
python auth_test.py
```

### **Test Server Endpoints**
```bash
python test_server.py
```

**Note**: The test scripts require a valid Zoom OAuth access token to be provided.

## OAuth Scopes Required

For full functionality, the Zoom App should request these scopes:

- `meeting:write` - Create/edit/delete meetings
- `meeting:read` - Read meeting information
- `user:read` - Read user information
- `webinar:write` - Create/edit webinars
- `webinar:read` - Read webinar information

## Client Integration

### **For LLM Platforms**

The LLM client should:

1. **Handle OAuth Flow**: Use the `zoom_authenticate_device_flow` tool for easy authentication
2. **Store Tokens Securely**: Store access tokens securely (encrypted, not in plain text)
3. **Refresh Tokens**: Handle token refresh when they expire
4. **Include in Headers**: Add `x-zoom-access-token` to all MCP requests

### **Device Flow Process**

1. **Start Flow**: Call `zoom_authenticate_device_flow` tool
2. **Display Instructions**: Show user the URL and code
3. **Wait for Authorization**: Poll for completion
4. **Get Token**: Receive access token when authorized
5. **Use Token**: Include in subsequent requests

### **Example Client Flow**

```python
import mcp.client

client = mcp.client.ClientSession("http://localhost:5000/mcp")

# 1. Start device flow
auth_result = await client.call_tool("zoom_authenticate_device_flow", {})

# 2. Display instructions to user
print(f"Visit: {auth_result['verification_url']}")
print(f"Enter code: {auth_result['user_code']}")

# 3. Wait for authorization (handled automatically)
# 4. Get access token
access_token = auth_result['access_token']

# 5. Use with MCP server
mcp_headers = {"x-zoom-access-token": access_token}
```

## Configuration

### **Zoom App Setup**

1. **Create Zoom App**: Go to Zoom App Marketplace
2. **Configure OAuth**: Set up OAuth app with device flow enabled
3. **Set Scopes**: Configure required scopes
4. **Get Client ID**: Copy the Client ID
5. **Update Config**: Set Client ID in `tools/auth.py`

### **Environment Variables**

```bash
export ZOOM_MCP_SERVER_PORT=5000
export ZOOM_CLIENT_ID=your_client_id_here
```
