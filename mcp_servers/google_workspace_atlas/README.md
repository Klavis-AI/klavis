# Google Workspace MCP Server

[![smithery badge](https://smithery.ai/badge/@rishipradeep-think41/gsuite-mcp)](https://smithery.ai/server/@rishipradeep-think41/gsuite-mcp)

A Model Context Protocol (MCP) server that provides tools for interacting with Gmail and Calendar APIs. This server enables you to manage your emails and calendar events programmatically through the MCP interface.

## Features

### Gmail Tools
- `list_emails`: List recent emails from your inbox with optional filtering
- `search_emails`: Advanced email search with Gmail query syntax
- `send_email`: Send new emails with support for CC and BCC
- `modify_email`: Modify email labels (archive, trash, mark read/unread)

### Calendar Tools
- `list_events`: List upcoming calendar events with date range filtering
- `create_event`: Create new calendar events with attendees
- `update_event`: Update existing calendar events
- `delete_event`: Delete calendar events

## Prerequisites

1. **Node.js**: Install Node.js version 14 or higher
2. **Google Cloud Console Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API and Google Calendar API:
     1. Go to "APIs & Services" > "Library"
     2. Search for and enable "Gmail API"
     3. Search for and enable "Google Calendar API"
   - Set up OAuth 2.0 credentials:
     1. Go to "APIs & Services" > "Credentials"
     2. Click "Create Credentials" > "OAuth client ID"
     3. Choose "Web application"
     4. Set "Authorized redirect URIs" to include: `http://localhost:4100/code`
     5. Note down the Client ID and Client Secret

## Setup Instructions

### Installing via Smithery

To install gsuite-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@rishipradeep-think41/gsuite-mcp):

```bash
npx -y @smithery/cli install @rishipradeep-think41/gsuite-mcp --client claude
```

### Installing Manually
1. **Clone and Install**:
   ```bash
   git clone https://github.com/epaproditus/google-workspace-mcp-server.git
   cd google-workspace-mcp-server
   npm install
   ```

2. **Create OAuth Credentials**:
   Create a `credentials.json` file in the root directory:
   ```json
   {
       "web": {
           "client_id": "YOUR_CLIENT_ID",
           "client_secret": "YOUR_CLIENT_SECRET",
           "redirect_uris": ["http://localhost:4100/code"],
           "auth_uri": "https://accounts.google.com/o/oauth2/auth",
           "token_uri": "https://oauth2.googleapis.com/token"
       }
   }
   ```

3. **Get Refresh Token**:
   ```bash
   node get-refresh-token.js
   ```
   This will:
   - Open your browser for Google OAuth authentication
   - Request the following permissions:
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/gmail.send`
   - Save the credentials to `token.json`
   - Display the refresh token in the console

4. **Configure MCP Settings**:
   Add the server configuration to your MCP settings file:
   - For VSCode Claude extension: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - For Claude desktop app: `~/Library/Application Support/Claude/claude_desktop_config.json`

   Add this to the `mcpServers` object:
   ```json
   {
     "mcpServers": {
       "google-workspace": {
         "command": "node",
         "args": ["/path/to/google-workspace-server/build/index.js"],
         "env": {
           "GOOGLE_CLIENT_ID": "your_client_id",
           "GOOGLE_CLIENT_SECRET": "your_client_secret",
           "GOOGLE_REFRESH_TOKEN": "your_refresh_token"
         }
       }
     }
   }
   ```

5. **Build and Run**:
   ```bash
   npm run build
   ```

## Usage Examples

### Gmail Operations

1. **List Recent Emails**:
   ```json
   {
     "maxResults": 5,
     "query": "is:unread"
   }
   ```

2. **Search Emails**:
   ```json
   {
     "query": "from:example@gmail.com has:attachment",
     "maxResults": 10
   }
   ```

3. **Send Email**:
   ```json
   {
     "to": "recipient@example.com",
     "subject": "Hello",
     "body": "Message content",
     "cc": "cc@example.com",
     "bcc": "bcc@example.com"
   }
   ```

4. **Modify Email**:
   ```json
   {
     "id": "message_id",
     "addLabels": ["UNREAD"],
     "removeLabels": ["INBOX"]
   }
   ```

### Calendar Operations

1. **List Events**:
   ```json
   {
     "maxResults": 10,
     "timeMin": "2024-01-01T00:00:00Z",
     "timeMax": "2024-12-31T23:59:59Z"
   }
   ```

2. **Create Event**:
   ```json
   {
     "summary": "Team Meeting",
     "location": "Conference Room",
     "description": "Weekly sync-up",
     "start": "2024-01-24T10:00:00Z",
     "end": "2024-01-24T11:00:00Z",
     "attendees": ["colleague@example.com"]
   }
   ```

3. **Update Event**:
   ```json
   {
     "eventId": "event_id",
     "summary": "Updated Meeting Title",
     "location": "Virtual",
     "start": "2024-01-24T11:00:00Z",
     "end": "2024-01-24T12:00:00Z"
   }
   ```

4. **Delete Event**:
   ```json
   {
     "eventId": "event_id"
   }
   ```

## Troubleshooting

1. **Authentication Issues**:
   - Ensure all required OAuth scopes are granted
   - Verify client ID and secret are correct
   - Check if refresh token is valid

2. **API Errors**:
   - Check Google Cloud Console for API quotas and limits
   - Ensure APIs are enabled for your project
   - Verify request parameters match the required format

## License

This project is licensed under the MIT License.
