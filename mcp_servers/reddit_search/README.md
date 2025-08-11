# Reddit Search MCP Server

A Model Context Protocol (MCP) server for searching and retrieving Reddit content. This server provides AI assistants with the ability to find relevant subreddits, search for posts, retrieve comments, and discover similar content across Reddit.

## Features

- **Subreddit Discovery**: Find relevant subreddits based on search queries
- **Post Search**: Search for posts within specific subreddits with semantic ranking
- **Comment Retrieval**: Get top comments for specific posts
- **Similar Post Discovery**: Find posts similar to a given post using semantic matching
- **Advanced Querying**: Supports comparison queries (e.g., "X vs Y") with specialized ranking
- **Rate Limiting**: Built-in rate limiting and retry logic for Reddit API
- **Dual Transport**: Supports both SSE and StreamableHTTP protocols

## Available Tools

### Subreddit Operations
- `reddit_find_subreddits`: Find relevant subreddits based on a query

### Post Operations
- `reddit_search_posts`: Search for posts in a specific subreddit
- `reddit_get_post_comments`: Get top comments for a specific post
- `reddit_find_similar_posts`: Find posts similar to a given post using semantic matching

## Prerequisites

To use this server, you need Reddit API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" application type
4. Note down your `client_id` and `client_secret`

## Configuration

Create a `.env` file in the `mcp_servers/reddit_search/` directory with the following content:

```bash
REDDIT_MCP_SERVER_PORT=5001
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=klavis-mcp/0.1 (+https://klavis.ai)
```

Set the following environment variables:

- `REDDIT_MCP_SERVER_PORT`: Port for the server (default: 5001)
- `REDDIT_CLIENT_ID`: Reddit app client ID
- `REDDIT_CLIENT_SECRET`: Reddit app client secret
- `REDDIT_USER_AGENT`: User agent string for Reddit API requests

## Running the Server

### Direct Python
```bash
python main.py --port 5001 --json-response
```

### Docker
From the root of the repository:
```bash
docker build -t reddit-mcp-server -f mcp_servers/reddit_search/Dockerfile .
docker run -p 5001:5001 --env-file mcp_servers/reddit_search/.env reddit-mcp-server
```

### Command Line Options
- `--port`: Port to listen on (default: 5001)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--json-response`: Enable JSON responses for StreamableHTTP instead of SSE streams

## API Endpoints

- **SSE**: `GET /sse` - Server-Sent Events endpoint for MCP communication
- **StreamableHTTP**: `POST /mcp` - StreamableHTTP endpoint for MCP communication

## Integration with Cursor IDE

To integrate this MCP server with Cursor IDE:

1. **Configure MCP Server in Cursor**:
   - Open Cursor IDE
   - Go to Settings > Features > MCP Servers
   - Add a new MCP server with the following configuration:

```json
{
  "mcpServers": {
    "reddit-search": {
      "command": "python",
      "args": ["mcp_servers/reddit_search/main.py", "--port", "5001"],
      "env": {
        "REDDIT_CLIENT_ID": "your_client_id",
        "REDDIT_CLIENT_SECRET": "your_client_secret",
        "REDDIT_USER_AGENT": "klavis-mcp/0.1 (+https://klavis.ai)"
      }
    }
  }
}
```

2. **Test the Integration**:
   - Ask Cursor to search for relevant subreddits
   - Search for posts within specific communities
   - Retrieve detailed post information with comments

## Example Usage

Once integrated with Cursor, you can use natural language queries like:

- "Find subreddits related to machine learning"
- "Search for posts about Python vs JavaScript in the programming subreddit"
- "Get the comments for this Reddit post: [post_id]"
- "Find posts similar to this one about AI development"

## API Rate Limiting

The server includes built-in rate limiting and retry logic:
- Respects Reddit's rate limits (429 responses)
- Implements exponential backoff for failed requests
- Includes jitter to prevent thundering herd effects

## Authentication

The server uses Reddit's OAuth2 client credentials flow for authentication. Access tokens are automatically obtained and cached for the duration of the server session.

## Dependencies

- mcp>=1.12.0
- pydantic
- typing-extensions
- requests
- click
- python-dotenv
- starlette
- uvicorn[standard]

## Error Handling

The server includes comprehensive error handling for:
- Invalid Reddit API credentials
- Network connectivity issues
- Rate limiting (automatic retry with backoff)
- Malformed API responses
- Missing or invalid post/subreddit IDs

## Semantic Search Features

The server implements advanced semantic search capabilities:
- **Token-based matching**: Analyzes text content for relevant keywords
- **Comparison query detection**: Special handling for "X vs Y" style queries
- **Semantic scoring**: Ranks results based on relevance, not just Reddit scores
- **Fallback strategies**: Multiple search approaches to ensure comprehensive results
