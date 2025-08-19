# Slack MCP Server (Python)

A Model Context Protocol (MCP) server implementation for Slack integration using Python. This server provides tools for interacting with Slack workspaces, including channels, messages, users, and search functionality.

## Features

### Channel Management
- **List Channels**: Browse workspace channels with pagination support
- **Get Channel History**: Retrieve recent messages from channels

### Messaging
- **Post Message**: Send new messages to channels
- **Reply to Thread**: Respond to existing message threads
- **Add Reaction**: React to messages with emojis
- **Get Thread Replies**: Fetch all replies in a thread

### User Management
- **List Users**: Get workspace users with profile information
- **Get User Profile**: Retrieve detailed profile for specific users

### Search
- **Search Messages**: Search across workspace messages with advanced query support

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

- `SLACK_AUTH_TOKEN`: Your Slack bot token (optional if using x-auth-data header)
- `SLACK_TEAM_ID`: Your Slack team ID (optional, for team-specific operations)
- `SLACK_MCP_SERVER_PORT`: Server port (default: 5000)
- `AUTH_DATA`: Base64 encoded JSON containing authentication data (optional)

### Authentication

The server supports two authentication methods:

1. **Environment Variable**: Set `SLACK_AUTH_TOKEN` with your bot token
2. **Request Header**: Send authentication via `x-auth-data` header containing base64-encoded JSON with `access_token` field

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
Search workspace messages.

**Parameters:**
- `query` (required): Search query (supports Slack search operators)
- `channel_ids` (optional): List of channel IDs to search within
- `sort` (optional): Sort by 'score' or 'timestamp' (default: score)
- `sort_dir` (optional): Sort direction 'asc' or 'desc' (default: desc)
- `count` (optional): Results per page (default: 20, max: 100)
- `cursor` (optional): Pagination cursor
- `highlight` (optional): Include match highlighting (default: true)

## Development

### Project Structure

```
slack_python/
├── server.py           # Main server implementation
├── tools/              # Tool modules
│   ├── __init__.py     # Module exports
│   ├── base.py         # Base client and authentication
│   ├── channels.py     # Channel-related tools
│   ├── messages.py     # Message-related tools
│   ├── users.py        # User-related tools
│   └── search.py       # Search functionality
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
