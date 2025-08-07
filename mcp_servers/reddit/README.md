# Reddit MCP Server

A Model Context Protocol (MCP) server that provides atomic tools for interacting with Reddit's API. This server enables AI agents to search, read, and analyze Reddit content through natural language commands.

## Features

- **Search Reddit posts** by keywords, subreddits, and time periods
- **Get post details** including comments, scores, and metadata
- **List subreddits** with trending topics and community information
- **Get user profiles** and their recent activity
- **Search comments** across Reddit
- **Get trending posts** from specific subreddits

## Installation

### Prerequisites

- Python 3.8 or higher
- Reddit API credentials (Client ID and Client Secret)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Reddit API Credentials**
   
   To use this MCP server, you need to create a Reddit application:
   
   1. Go to https://www.reddit.com/prefs/apps
   2. Click "Create App" or "Create Another App"
   3. Select "script" as the application type
   4. Fill in the required fields:
      - **Name**: Your app name (e.g., "MCP Reddit Server")
      - **Description**: Brief description
      - **About URL**: Can be left blank
      - **Redirect URI**: Use `http://localhost:8080` (not actually used for script apps)
   5. Click "Create App"
   6. Note down your **Client ID** (the string under your app name) and **Client Secret**

4. **Configure Environment Variables**
   
   Create a `.env` file in the project root or set these environment variables:
   ```bash
   export REDDIT_CLIENT_ID="your_client_id_here"
   export REDDIT_CLIENT_SECRET="your_client_secret_here"
   export REDDIT_USER_AGENT="MCP_Reddit_Server/1.0 (by /u/your_username)"
   ```

## Usage

### Running the Server

```bash
python reddit_mcp_server.py
```

The server will start on `localhost:8080` by default.

### Connecting to an MCP Client

Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "reddit": {
      "command": "python",
      "args": ["/path/to/reddit_mcp_server.py"],
      "env": {
        "REDDIT_CLIENT_ID": "your_client_id",
        "REDDIT_CLIENT_SECRET": "your_client_secret",
        "REDDIT_USER_AGENT": "MCP_Reddit_Server/1.0"
      }
    }
  }
}
```

## Available Tools

### `search_reddit_posts`
Search for posts across Reddit or within specific subreddits.

**Parameters:**
- `query` (string, required): Search terms
- `subreddit` (string, optional): Limit search to specific subreddit
- `limit` (integer, optional): Number of results (default: 10, max: 100)
- `time_filter` (string, optional): Time period (hour, day, week, month, year, all)

**Example Usage:**
- "Search for posts about Python programming"
- "Find recent posts about machine learning in r/MachineLearning"
- "Get the top 20 posts about AI from the past week"

### `get_post_details`
Get detailed information about a specific Reddit post.

**Parameters:**
- `post_id` (string, required): Reddit post ID or full URL

**Example Usage:**
- "Get details for post t3_abc123"
- "Show me the full post and comments for https://reddit.com/r/Python/comments/abc123"

### `list_subreddits`
Get information about subreddits, including trending topics.

**Parameters:**
- `query` (string, optional): Search for specific subreddits
- `limit` (integer, optional): Number of results (default: 10)

**Example Usage:**
- "List popular programming subreddits"
- "Find subreddits about data science"

### `get_user_profile`
Get information about a Reddit user and their recent activity.

**Parameters:**
- `username` (string, required): Reddit username

**Example Usage:**
- "Get profile for user u/spez"
- "Show me the recent posts by u/username"

### `search_comments`
Search for comments across Reddit.

**Parameters:**
- `query` (string, required): Search terms
- `subreddit` (string, optional): Limit search to specific subreddit
- `limit` (integer, optional): Number of results (default: 10)

**Example Usage:**
- "Search for comments about React hooks"
- "Find comments about Docker in r/docker"

### `get_trending_posts`
Get trending posts from a specific subreddit.

**Parameters:**
- `subreddit` (string, required): Subreddit name (without r/)
- `limit` (integer, optional): Number of results (default: 10)
- `time_filter` (string, optional): Time period (hour, day, week, month, year, all)

**Example Usage:**
- "Get trending posts from r/Python"
- "Show me the top posts from r/technology this week"

## Error Handling

The server includes robust error handling for:
- Invalid API credentials
- Rate limiting (Reddit API has rate limits)
- Network connectivity issues
- Invalid parameters
- Missing or malformed responses

All errors are returned with clear, actionable messages that help the AI understand what went wrong and potentially self-correct.

## Rate Limiting

Reddit's API has rate limits:
- 60 requests per minute for authenticated requests
- The server automatically handles rate limiting and will retry requests when possible

## Security Notes

- Never commit your Reddit API credentials to version control
- Use environment variables for all sensitive configuration
- The server only makes read-only requests to Reddit's API
- No user authentication is required for public data access

## Contributing

This MCP server follows the Klavis AI development guidelines:
- Atomic, single-purpose tools
- Clear, descriptive tool names and descriptions
- Comprehensive error handling
- User-centric design for AI agents

## License

This project is part of the Klavis AI MCP server collection. 