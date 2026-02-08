# Calendar AutoAuth MCP Server

A Model Context Protocol (MCP) server for Google Calendar integration in Cluade Desktop with auto authentication support. This server enables AI assistants to manage Google Calendar events through natural language interactions.

![](https://badge.mcpx.dev?type=server 'MCP Server')
[![smithery badge](https://smithery.ai/badge/@gongrzhe/server-calendar-autoauth-mcp)](https://smithery.ai/server/@gongrzhe/server-calendar-autoauth-mcp)
[![npm version](https://badge.fury.io/js/%40gongrzhe%2Fserver-calendar-autoauth-mcp.svg)](https://www.npmjs.com/package/@gongrzhe/server-calendar-autoauth-mcp)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

## Features

- Create calendar events with title, time, description, and location
- Retrieve event details by event ID
- Update existing events (title, time, description, location)
- Delete events
- List events within a specified time range
- Full integration with Google Calendar API
- Simple OAuth2 authentication flow with auto browser launch
- Support for both Desktop and Web application credentials
- Global credential storage for convenience

## Installation & Authentication

### Installing via Smithery

To install Calendar AutoAuth Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@gongrzhe/server-calendar-autoauth-mcp):

```bash
npx -y @smithery/cli install @gongrzhe/server-calendar-autoauth-mcp --client claude
```

1. Create a Google Cloud Project and obtain credentials:

   a. Create a Google Cloud Project:
      - Go to [Google Cloud Console](https://console.cloud.google.com/)
      - Create a new project or select an existing one
      - Enable the Google Calendar API for your project

   b. Create OAuth 2.0 Credentials:
      - Go to "APIs & Services" > "Credentials"
      - Click "Create Credentials" > "OAuth client ID"
      - Choose either "Desktop app" or "Web application" as application type
      - Give it a name and click "Create"
      - For Web application, add `http://localhost:3000/oauth2callback` to the authorized redirect URIs
      - Download the JSON file of your client's OAuth keys
      - Rename the key file to `gcp-oauth.keys.json`

2. Run Authentication:

   You can authenticate in two ways:

   a. Global Authentication (Recommended):
   ```bash
   # First time: Place gcp-oauth.keys.json in your home directory's .calendar-mcp folder
   mkdir -p ~/.calendar-mcp
   mv gcp-oauth.keys.json ~/.calendar-mcp/

   # Run authentication from anywhere
   npx @gongrzhe/server-calendar-autoauth-mcp auth
   ```

   b. Local Authentication:
   ```bash
   # Place gcp-oauth.keys.json in your current directory
   # The file will be automatically copied to global config
   npx @gongrzhe/server-calendar-autoauth-mcp auth
   ```

   The authentication process will:
   - Look for `gcp-oauth.keys.json` in the current directory or `~/.calendar-mcp/`
   - If found in current directory, copy it to `~/.calendar-mcp/`
   - Open your default browser for Google authentication
   - Save credentials as `~/.calendar-mcp/credentials.json`

   > **Note**: 
   > - After successful authentication, credentials are stored globally in `~/.calendar-mcp/` and can be used from any directory
   > - Both Desktop app and Web application credentials are supported
   > - For Web application credentials, make sure to add `http://localhost:3000/oauth2callback` to your authorized redirect URIs

3. Configure in Claude Desktop:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "npx",
      "args": [
        "@gongrzhe/server-calendar-autoauth-mcp"
      ]
    }
  }
}
```

### Docker Support

If you prefer using Docker:

1. Authentication:
```bash
docker run -i --rm \
  --mount type=bind,source=/path/to/gcp-oauth.keys.json,target=/gcp-oauth.keys.json \
  -v mcp-calendar:/calendar-server \
  -e CALENDAR_OAUTH_PATH=/gcp-oauth.keys.json \
  -e "CALENDAR_CREDENTIALS_PATH=/calendar-server/credentials.json" \
  -p 3000:3000 \
  mcp/calendar auth
```

2. Usage:
```json
{
  "mcpServers": {
    "calendar": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "mcp-calendar:/calendar-server",
        "-e",
        "CALENDAR_CREDENTIALS_PATH=/calendar-server/credentials.json",
        "mcp/calendar"
      ]
    }
  }
}
```

## Usage Examples

The server provides several tools that can be used through the Claude Desktop:

### Create Event
```json
{
  "summary": "Team Meeting",
  "start": {
    "dateTime": "2024-01-20T10:00:00Z"
  },
  "end": {
    "dateTime": "2024-01-20T11:00:00Z"
  },
  "description": "Weekly team sync",
  "location": "Conference Room A"
}
```

### List Events
```json
{
  "timeMin": "2024-01-01T00:00:00Z",
  "timeMax": "2024-12-31T23:59:59Z",
  "maxResults": 10,
  "orderBy": "startTime"
}
```

### Update Event
```json
{
  "eventId": "event123",
  "summary": "Updated Meeting Title",
  "start": {
    "dateTime": "2024-01-20T11:00:00Z"
  },
  "end": {
    "dateTime": "2024-01-20T12:00:00Z"
  }
}
```

### Delete Event
```json
{
  "eventId": "event123"
}
```

## Security Notes

- OAuth credentials are stored securely in your local environment (`~/.calendar-mcp/`)
- The server uses offline access to maintain persistent authentication
- Never share or commit your credentials to version control
- Regularly review and revoke unused access in your Google Account settings
- Credentials are stored globally but are only accessible by the current user

## Troubleshooting

1. **OAuth Keys Not Found**
   - Make sure `gcp-oauth.keys.json` is in either your current directory or `~/.calendar-mcp/`
   - Check file permissions

2. **Invalid Credentials Format**
   - Ensure your OAuth keys file contains either `web` or `installed` credentials
   - For web applications, verify the redirect URI is correctly configured

3. **Port Already in Use**
   - If port 3000 is already in use, please free it up before running authentication
   - You can find and stop the process using that port

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the ISC License.

## Author

gongrzhe

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
