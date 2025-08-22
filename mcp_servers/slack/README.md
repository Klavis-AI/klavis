# Slack MCP Server (Python)

A Model Context Protocol (MCP) server implementation for Slack integration using Python. This server provides comprehensive tools for interacting with Slack workspaces using both bot and user tokens, enabling both general workspace operations and user-specific actions.

## Features

### User Tools (Using User Token)
These tools use the user token for user-specific operations:

#### Channel Management
- **List Channels**: List all channels the authenticated user has access to (public, private, DMs, multi-party DMs)
- **Get Channel History**: Retrieve recent messages from channels

#### Messaging
- **Post Message**: Send new messages to channels as a user
- **Reply to Thread**: Respond to existing message threads as a user
- **Add Reaction**: React to messages with emojis as a user

#### User Management
- **List Users**: Get workspace users with profile information
- **Get User Info**: Retrieve detailed information for specific users

#### Search
- **Search Messages**: Search messages with user permissions across all accessible channels

### Bot Tools (Using Bot Token)
These tools use the bot token for bot-specific operations:

#### Messaging
- **Post Message**: Send new messages to channels as a bot
- **Reply to Thread**: Respond to existing message threads as a bot
- **Add Reaction**: React to messages with emojis as a bot

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

Create a `.env` file in the slack directory with your Slack credentials:

```bash
# .env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_USER_TOKEN=xoxp-your-user-token
SLACK_MCP_SERVER_PORT=5000  # Optional, defaults to 5000
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

### User Tools (Require User Token)

### slack_user_list_channels
List all channels the authenticated user has access to.

**Parameters:**
- `limit` (optional): Maximum channels to return (default: 100, max: 200)
- `cursor` (optional): Pagination cursor for next page
- `types` (optional): Channel types (public_channel, private_channel, mpim, im)

### slack_get_channel_history
Get recent messages from a channel.

**Parameters:**
- `channel_id` (required): The channel ID
- `limit` (optional): Number of messages to retrieve (default: 10)

### slack_list_users
Lists all users in a Slack team.

**Parameters:**
- `cursor` (optional): Pagination cursor for getting more results
- `limit` (optional): Maximum number of users to return (default: 100, max: 200)
- `team_id` (optional): Team ID to list users from (for Enterprise Grid)
- `include_locale` (optional): Whether to include locale information for each user

### slack_user_get_info
Gets information about a specific user.

**Parameters:**
- `user_id` (required): The ID of the user to get information for
- `include_locale` (optional): Whether to include locale information for the user

### slack_user_search_messages
Searches for messages matching a query with user permissions.

**Parameters:**
- `query` (required): Search query (supports Slack search operators like 'in:#channel', 'from:@user', etc.)
- `channel_ids` (optional): List of channel IDs to search within
- `sort` (optional): Sort by 'score' or 'timestamp' (default: score)
- `sort_dir` (optional): Sort direction 'asc' or 'desc' (default: desc)
- `count` (optional): Results per page (default: 20, max: 100)
- `cursor` (optional): Pagination cursor
- `highlight` (optional): Include match highlighting (default: true)

### slack_user_post_message
Post a new message to a Slack channel as a user.

**Parameters:**
- `channel_id` (required): The channel ID
- `text` (required): Message text to post

### slack_user_reply_to_thread
Reply to a message thread as a user.

**Parameters:**
- `channel_id` (required): The channel ID
- `thread_ts` (required): Parent message timestamp
- `text` (required): Reply text

### slack_user_add_reaction
Add an emoji reaction to a message as a user.

**Parameters:**
- `channel_id` (required): The channel ID
- `timestamp` (required): Message timestamp
- `reaction` (required): Emoji name (without colons)

### Bot Tools (Require Bot Token)

### slack_bot_post_message
Post a new message to a Slack channel as a bot.

**Parameters:**
- `channel_id` (required): The channel ID
- `text` (required): Message text to post

### slack_bot_reply_to_thread
Reply to a message thread as a bot.

**Parameters:**
- `channel_id` (required): The channel ID
- `thread_ts` (required): Parent message timestamp
- `text` (required): Reply text

### slack_bot_add_reaction
Add an emoji reaction to a message as a bot.

**Parameters:**
- `channel_id` (required): The channel ID
- `timestamp` (required): Message timestamp
- `reaction` (required): Emoji name (without colons)

## Development

### Project Structure

```
slack/
├── server.py           # Main server implementation
├── bot_tools/          # Bot token operations
│   ├── __init__.py     # Module exports
│   ├── base.py         # Bot client and authentication
│   └── bot_messages.py # Bot messaging tools
├── user_tools/         # User token operations
│   ├── __init__.py     # Module exports
│   ├── base.py         # User client and authentication
│   ├── channels.py     # Channel-related tools
│   ├── user_messages.py # User messaging tools
│   ├── search.py       # User search functionality
│   └── users.py        # User information tools
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
└── README.md           # Documentation
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
