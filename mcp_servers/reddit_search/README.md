# Reddit Search MCP Server

A Model Context Protocol (MCP) server that enables AI clients to search, retrieve, and interact with Reddit content. Provides semantic search, post creation, comment management, and community discovery capabilities.

## Features

- **Semantic Search**: Find relevant subreddits and posts using natural language queries
- **Content Creation**: Create posts and comments programmatically
- **Community Discovery**: Discover relevant subreddits based on topics
- **Rate Limiting**: Built-in rate limiting and retry logic for Reddit API
- **Dual Transport**: Supports both SSE and StreamableHTTP protocols

## Tools Reference

| Tool | Description | Input Parameters | Output | Credentials Required |
|------|-------------|------------------|--------|---------------------|
| `reddit_find_subreddits` | Find relevant subreddits based on a query | `query` (string) | Array of subreddit objects with name, description, subscriber_count | Basic API credentials |
| `reddit_search_posts` | Search for posts in a specific subreddit | `subreddit` (string), `query` (string) | Array of post objects with title, score, url, comment_count | Basic API credentials |
| `reddit_get_post_comments` | Get top comments for a specific post | `post_id` (string), `subreddit` (string) | Array of comment objects with author, body, score | Basic API credentials |
| `reddit_find_similar_posts` | Find posts similar to a given post | `post_id` (string), `limit` (number, optional) | Array of similar post objects | Basic API credentials |
| `reddit_create_post` | Create a new text post in a subreddit | `subreddit` (string), `title` (string), `text` (string) | Post creation confirmation with post_id | Basic API credentials + Username/Password |
| `reddit_create_comment` | Create a comment on a post | `post_id` (string), `text` (string) | Comment creation confirmation with comment_id | Basic API credentials + Username/Password |
| `reddit_upvote` | Upvote a post | `post_id` (string) | Upvote confirmation | Basic API credentials + Username/Password |
| `reddit_get_user_posts` | Get recent posts by authenticated user | `limit` (number, optional) | Array of user's post objects | Basic API credentials + Username/Password |

## Prerequisites

### Reddit API Credentials

1. Visit https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" application type
4. Save the generated `client_id` and `client_secret`

**For Post Creation/Interaction**: You'll also need your Reddit username and password.

## Setup

### 1. Environment Configuration

Create `.env` file in `mcp_servers/reddit_search/`:

```bash
REDDIT_MCP_SERVER_PORT=5001
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=klavis-mcp/0.1 (+https://klavis.ai)

# For post creation (optional - only needed for reddit_create_post, reddit_create_comment, reddit_upvote)
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
```

### 2. Running the Server

#### Docker (Recommended)
```bash
# From repository root
docker build -t reddit-mcp-server -f mcp_servers/reddit_search/Dockerfile .
docker run -p 5001:5001 --env-file mcp_servers/reddit_search/.env reddit-mcp-server
```

#### Direct Python
```bash
cd mcp_servers/reddit_search
python server.py --port 5001
```

## Cursor IDE Integration

### 1. Configure MCP Server in Cursor

Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "reddit-search": {
      "url": "http://localhost:5001/sse"
    }
  }
}
```

### 2. Test in Cursor Chat

Try these example queries:

- "Use reddit_find_subreddits to find subreddits related to machine learning"
- "Use reddit_search_posts in subreddit 'programming' for query 'Python vs JavaScript'"
- "Use reddit_get_post_comments for post_id '1nqa311' in subreddit 'programming'"
- "Use reddit_find_similar_posts for post_id '1nqa311' with limit 5"
- "Use reddit_create_post in subreddit 'test' with title 'Test Post' and text 'This is a test'"

## API Endpoints

- **SSE**: `GET /sse` - Server-Sent Events endpoint for MCP communication
- **StreamableHTTP**: `POST /mcp` - StreamableHTTP endpoint for MCP communication

## Authentication

The server uses Reddit's OAuth2 client credentials flow. Access tokens are automatically obtained and cached for the duration of the server session.

## Rate Limiting

Built-in rate limiting and retry logic:
- Respects Reddit's rate limits (429 responses)
- Implements exponential backoff for failed requests
- Includes jitter to prevent thundering herd effects

## Dependencies

- mcp>=1.12.0
- pydantic
- typing-extensions
- httpx
- click
- python-dotenv
- starlette
- uvicorn[standard]
