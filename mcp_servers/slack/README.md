# Slack MCP Server (Python)

A Model Context Protocol (MCP) server implementation for Slack integration using Python. This server provides comprehensive tools for interacting with Slack workspaces using both bot and user tokens, enabling both general workspace operations and user-specific actions.

## Features

### Bot Tools (Using Bot Token)
These tools use the bot token for general workspace operations:

#### Channel Management
- **List Channels**: Browse workspace channels with pagination support
- **Get Channel History**: Retrieve recent messages from channels

#### Messaging
- **Post Message**: Send new messages to channels
- **Reply to Thread**: Respond to existing message threads
- **Add Reaction**: React to messages with emojis
- **Get Thread Replies**: Fetch all replies in a thread

#### User Management
- **List Users**: Get workspace users with profile information
- **Get User Profile**: Retrieve detailed profile for specific users

#### Search
- **Search Messages**: Search across public workspace messages

### User Tools (Using User Token)
These tools use the user token for user-specific operations:

#### User Profile Management
- **Set Status**: Update the authenticated user's custom status
- **Get Profile**: Get the authenticated user's profile
- **Set Presence**: Set user presence to auto or away

#### User Search
- **Search Messages**: Search messages with user permissions (includes private channels and DMs)
- **Search Files**: Search files accessible to the user

#### Direct Messages
- **Open DM**: Open a direct message channel with users
- **Send DM**: Send direct messages to users
- **Post Ephemeral**: Post ephemeral messages visible only to specific users

## Installation

### Using pip

```bash
pip install -r requirements.txt
```

### Using Docker

```bash
docker build -t slack-mcp-server .
docker run -p 5000:5000 slack-mcp-server
```

## Configuration

### Environment Variables

Copy the `.env.example` file to `.env` and update with your values:

```bash
cp .env.example .env
# Edit .env with your Slack credentials
```

- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...) for bot operations
- `SLACK_USER_TOKEN`: Your Slack user token (xoxp-...) for user-specific operations
- `SLACK_MCP_SERVER_PORT`: Server port (default: 5000)

### Authentication

The server supports dual-token authentication for different operation types:

#### For Local Development
Set environment variables:
- `SLACK_BOT_TOKEN`: Bot token for workspace operations
- `SLACK_USER_TOKEN`: User token for user-specific operations

#### For Klavis Cloud Deployment
Tokens are provided via `x-auth-data` header containing base64-encoded JSON:
```json
{
  "access_token": "xoxb-...",  // Bot token
  "authed_user": {
    "access_token": "xoxp-..."  // User token
  }
}
```

## Usage

### Starting the Server

```bash
# Basic usage
python server.py

# With custom port
python server.py --port 8080

# With debug logging
python server.py --log-level DEBUG

# With JSON responses for StreamableHTTP
python server.py --json-response
```

### Endpoints

The server provides two transport endpoints:

- **SSE Transport**: `http://localhost:5000/sse` (legacy)
- **StreamableHTTP Transport**: `http://localhost:5000/mcp` (recommended)

## Tools Reference

### Bot Tools (Require Bot Token)

### slack_list_channels
List channels in the workspace with pagination support.

**Parameters:**
- `limit` (optional): Maximum channels to return (default: 100, max: 200)
- `cursor` (optional): Pagination cursor for next page
- `types` (optional): Channel types (public_channel, private_channel, mpim, im)

### slack_get_channel_history
Get recent messages from a channel.

**Parameters:**
- `channel_id` (required): The channel ID
- `limit` (optional): Number of messages to retrieve (default: 10)

### slack_post_message
Post a new message to a channel.

**Parameters:**
- `channel_id` (required): The channel ID
- `text` (required): Message text to post

### slack_reply_to_thread
Reply to a message thread.

**Parameters:**
- `channel_id` (required): The channel ID
- `thread_ts` (required): Parent message timestamp
- `text` (required): Reply text

### slack_add_reaction
Add an emoji reaction to a message.

**Parameters:**
- `channel_id` (required): The channel ID
- `timestamp` (required): Message timestamp
- `reaction` (required): Emoji name (without colons)

### slack_get_thread_replies
Get all replies in a thread.

**Parameters:**
- `channel_id` (required): The channel ID
- `thread_ts` (required): Parent message timestamp

### slack_get_users
List workspace users.

**Parameters:**
- `cursor` (optional): Pagination cursor
- `limit` (optional): Maximum users to return (default: 100, max: 200)

### slack_get_user_profile
Get detailed user profile.

**Parameters:**
- `user_id` (required): The user ID

### slack_search_messages
Search workspace messages (public channels only with bot token).

**Parameters:**
- `query` (required): Search query (supports Slack search operators)
- `channel_ids` (optional): List of channel IDs to search within
- `sort` (optional): Sort by 'score' or 'timestamp' (default: score)
- `sort_dir` (optional): Sort direction 'asc' or 'desc' (default: desc)
- `count` (optional): Results per page (default: 20, max: 100)
- `cursor` (optional): Pagination cursor
- `highlight` (optional): Include match highlighting (default: true)

### User Tools (Require User Token)

### slack_user_set_status
Set the authenticated user's custom status.

**Parameters:**
- `status_text` (required): The status text to display
- `status_emoji` (optional): The emoji to display (e.g., ':coffee:')
- `status_expiration` (optional): Unix timestamp when status expires

### slack_user_get_profile
Get the authenticated user's profile information.

**Parameters:** None

### slack_user_set_presence
Set the user's presence status.

**Parameters:**
- `presence` (required): Either 'auto' or 'away'

### slack_user_search_messages
Search messages with user permissions (includes private channels and DMs).

**Parameters:**
- `query` (required): Search query string
- `sort` (optional): Sort by 'score' or 'timestamp' (default: score)
- `sort_dir` (optional): Sort direction 'asc' or 'desc' (default: desc)
- `count` (optional): Results per page (default: 20, max: 100)
- `cursor` (optional): Pagination cursor

### slack_user_search_files
Search files accessible to the user.

**Parameters:**
- `query` (required): Search query string
- `count` (optional): Results per page (default: 20, max: 100)
- `cursor` (optional): Pagination cursor

### slack_user_open_dm
Open a direct message channel with one or more users.

**Parameters:**
- `users` (required): Comma-separated list of user IDs

### slack_user_post_dm
Send a direct message to a user.

**Parameters:**
- `user_id` (required): The user ID to send a DM to
- `text` (required): The message text

### slack_user_post_ephemeral
Post an ephemeral message visible only to a specific user.

**Parameters:**
- `channel_id` (required): The channel where the message appears
- `user_id` (required): The user who will see the message
- `text` (required): The message text

## Development

### Project Structure

```
slack/
├── server.py           # Main server implementation
├── bot_tools/          # Bot token operations
│   ├── __init__.py     # Module exports
│   ├── base.py         # Bot client and authentication
│   ├── channels.py     # Channel-related tools
│   ├── messages.py     # Message-related tools
│   ├── users.py        # User-related tools
│   └── search.py       # Search functionality
├── user_tools/         # User token operations
│   ├── __init__.py     # Module exports
│   ├── base.py         # User client and authentication
│   ├── user_profile.py # User profile management
│   ├── user_search.py  # User-scoped search
│   └── direct_messages.py # DM operations
├── requirements.txt    # Python dependencies
├── env.example         # Example environment configuration
├── Dockerfile          # Docker configuration
└── README.md           # Documentation
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

## Error Handling

The server includes comprehensive error handling:

- **Authentication Errors**: When token is missing or invalid
- **API Errors**: When Slack API returns error responses
- **Validation Errors**: When required parameters are missing
- **Network Errors**: When connection to Slack fails

All errors are logged and returned with descriptive messages.

## Security Considerations

- Always use HTTPS in production environments
- Store tokens securely and never commit them to version control
- Use environment variables or secure secret management systems
- Implement rate limiting for production deployments
- Regularly rotate API tokens

## License

MIT License

## Support

For issues or questions, please refer to the main Klavis documentation or create an issue in the repository.
