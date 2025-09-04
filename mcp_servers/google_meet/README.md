# Google Meet MCP Server

A Model Context Protocol (MCP) server that provides tools for managing Google Meet meetings through the Google Calendar API.

## Features

This MCP server exposes the following tools for Google Meet management:

- **google_meet_create_meet**: Create a new Google Meet meeting
- **google_meet_list_meetings**: List upcoming Google Meet meetings
- **google_meet_get_meeting_details**: Get details of a specific meeting
- **google_meet_update_meeting**: Update an existing meeting
- **google_meet_delete_meeting**: Delete a meeting

## Setup

### Prerequisites

1. uv (fast Python package installer)
2. Google Cloud Project with Calendar API enabled
3. OAuth 2.0 credentials (Client ID and Client Secret)
4. Python 3.8+

### Installation

1. Install dependencies using uv:
```bash
uv venv  # Create virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .  # Install in editable mode
```

Or using the traditional requirements.txt:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_MEET_MCP_SERVER_PORT=5000
```

### Authentication

The server expects authentication data to be passed in the `x-auth-data` header as base64-encoded JSON containing an `access_token`:

```json
{
  "access_token": "your-google-oauth-access-token"
}
```

## Usage

### VS Code Configuration

To resolve import errors in VS Code:

1. **Select the Correct Python Interpreter:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose the interpreter from the virtual environment: `./.venv/Scripts/python.exe`

2. **Or use the provided settings:**
   - VS Code settings have been configured automatically in `.vscode/settings.json`
   - Restart VS Code or reload the window (`Ctrl+Shift+P` → "Developer: Reload Window")

### Running the Server

#### Option 1: Using the run script (Recommended)
```bash
# On Windows
run.bat --port 5000 --log-level INFO

# On Linux/Mac
./run.sh --port 5000 --log-level INFO
```

#### Option 2: Direct Python execution
```bash
# Activate virtual environment first
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/Mac

# Run the server
python server.py --port 5000 --log-level INFO
```

#### Option 3: Using uv directly
```bash
uv run python server.py --port 5000 --log-level INFO
```

#### Option 4: VS Code Debug/Run
- Press `F5` or go to Run → Start Debugging
- The launch configuration is already set up in `.vscode/launch.json`

The server supports both SSE and StreamableHTTP transports:

- **SSE endpoint**: `http://localhost:5000/sse`
- **StreamableHTTP endpoint**: `http://localhost:5000/mcp`

### Tool Examples

#### Create a Meeting
```json
{
  "name": "google_meet_create_meet",
  "arguments": {
    "summary": "Team Standup",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "attendees": ["user1@example.com", "user2@example.com"],
    "description": "Daily team standup meeting"
  }
}
```

#### List Meetings
```json
{
  "name": "google_meet_list_meetings",
  "arguments": {
    "max_results": 10
  }
}
```

#### Update a Meeting
```json
{
  "name": "google_meet_update_meeting",
  "arguments": {
    "event_id": "calendar-event-id",
    "summary": "Updated Meeting Title",
    "start_time": "2024-01-15T11:00:00Z",
    "end_time": "2024-01-15T11:30:00Z"
  }
}
```

## API Reference

### Tools

#### google_meet_create_meet
Creates a new Google Meet meeting via Google Calendar.

**Parameters:**
- `summary` (string, required): Meeting title
- `start_time` (string, required): Start time in ISO RFC3339 format
- `end_time` (string, required): End time in ISO RFC3339 format
- `attendees` (array, required): List of attendee email addresses
- `description` (string, optional): Meeting description

**Returns:** Meeting details including event ID, Meet URL, and timing

#### google_meet_list_meetings
Lists upcoming Google Meet meetings from the user's calendar.

**Parameters:**
- `max_results` (integer, optional): Maximum number of meetings to return (default: 10)

**Returns:** List of meetings with details

#### google_meet_get_meeting_details
Gets detailed information about a specific meeting.

**Parameters:**
- `event_id` (string, required): The calendar event ID

**Returns:** Complete meeting details including attendees and status

#### google_meet_update_meeting
Updates an existing Google Meet meeting.

**Parameters:**
- `event_id` (string, required): The calendar event ID
- `summary` (string, optional): New meeting title
- `start_time` (string, optional): New start time
- `end_time` (string, optional): New end time
- `attendees` (array, optional): New list of attendees
- `description` (string, optional): New description

**Returns:** Updated meeting details

#### google_meet_delete_meeting
Deletes a Google Meet meeting.

**Parameters:**
- `event_id` (string, required): The calendar event ID to delete

**Returns:** Success confirmation

## Error Handling

The server handles Google Calendar API errors and returns descriptive error messages. Common error scenarios:

- Invalid authentication tokens
- Permission denied for calendar access
- Invalid event IDs
- Malformed datetime strings
- API quota exceeded

## Development

### Project Structure
```
google_meet/
├── server.py          # Main MCP server implementation
├── requirements.txt   # Python dependencies
└── README.md         # This documentation
```

### Testing

To test the server locally:

1. Start the server
2. Use an MCP client or test the HTTP endpoints directly
3. Verify authentication and tool execution

## License

This project is licensed under the MIT License - see the LICENSE file for details.</content>
<parameter name="filePath">c:\Users\manis\klavis\mcp_servers\google_meet\README.md
