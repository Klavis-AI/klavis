# Reddit Search MCP Server

This Model Context Protocol (MCP) server enables AI clients (e.g., Cursor, Claude Desktop) to search and retrieve Reddit content. It exposes tools to discover relevant subreddits, search posts with semantic-style ranking, fetch post comments, and find similar posts. The server authenticates with Reddit via OAuth2 client credentials and includes resilient request handling.

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

## Acquire Reddit API Credentials

1. Visit `https://www.reddit.com/prefs/apps`
2. Click “Create App” (or “Create Another App”)
3. Choose application type: `script`
4. Save the generated `client_id` and `client_secret`

## Installation & Configuration

1) Create a `.env` file in `mcp_servers/reddit_search/` with:

```bash
REDDIT_MCP_SERVER_PORT=5001
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=klavis-mcp/0.1 (+https://klavis.ai)
```

2) Environment variables reference:

- `REDDIT_MCP_SERVER_PORT`: Port for the server (default: 5001)
- `REDDIT_CLIENT_ID`: Reddit app client ID
- `REDDIT_CLIENT_SECRET`: Reddit app client secret
- `REDDIT_USER_AGENT`: User agent string for Reddit API requests

## Running the Server

### Direct Python (uv)
From the repository root on Windows PowerShell:
```bash
cd mcp_servers/reddit_search; uv sync; uv run python main.py
```
Expected terminal output includes:
- "Starting Reddit MCP Server..."
- A log line indicating a Reddit token was obtained
- Tool invocation logs when tools are used, e.g.:
  - `Tool call: reddit_find_subreddits(query='...')`
  - `Tool call: reddit_search_posts(subreddit='...', query='...')`
  - `Tool call: reddit_get_post_comments(post_id='...', subreddit='...')`
  - `Tool call: reddit_find_similar_posts(post_id='...', limit=...)`

### Direct Python (standard)
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

2. **Test the Integration** (examples you can paste in chat):
   - "Use reddit_find_subreddits to find subreddits related to machine learning"
   - "Use reddit_search_posts in subreddit 'programming' for query 'Python vs JavaScript'"
   - "Use reddit_get_post_comments for post_id '<paste_id>' in subreddit 'programming'"
   - "Use reddit_find_similar_posts for post_id '<paste_id>' with limit 5"

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
