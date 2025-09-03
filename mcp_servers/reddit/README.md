# Reddit MCP Server

A Model Context Protocol (MCP) server for Reddit integration, enabling AI applications to interact with Reddit through standardized tools.

## Features

This server provides the following Reddit capabilities through MCP tools:

- **📱 Browse Subreddits**: Get posts from any subreddit with different sorting options (hot, new, top, rising)
- **🔍 Search Posts**: Search for posts across all of Reddit or within specific subreddits
- **💬 Get Comments**: Retrieve comments and replies for specific posts
- **👤 User Posts**: Get posts from specific Reddit users
- **ℹ️ Subreddit Info**: Get detailed information about subreddits including rules, description, and subscriber count
- **📝 Submit Posts**: Create new text or link posts (requires authentication)

## Prerequisites

Before using this server, you need:

1. **Reddit Account**: A valid Reddit account
2. **Reddit Application**: You need to create a Reddit application to get API credentials

### Getting Reddit API Credentials

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in the application details:
   - **Name**: Choose any name for your application
   - **App type**: Select "script"
   - **Description**: Optional description
   - **About URL**: Optional
   - **Redirect URI**: Use `http://localhost:8080` (required but not used for script apps)
4. Click "Create app"
5. Note down the **Client ID** (shown under the app name) and **Client Secret**

## Installation & Setup

### Method 1: Docker (Recommended)

This method encapsulates the server and its dependencies in a container.

#### 1. Build the Docker Image

Navigate to the root directory of the klavis project (the parent directory of `mcp_servers`) in your terminal and run:

```bash
docker build -t reddit-mcp -f mcp_servers/reddit/Dockerfile ./mcp_servers/reddit
```

#### 2. Run the Docker Container

Replace the placeholder values with your actual Reddit credentials:

```bash
docker run -d -p 5000:5000 \
  -e REDDIT_CLIENT_ID=your_client_id_here \
  -e REDDIT_CLIENT_SECRET=your_client_secret_here \
  -e REDDIT_USERNAME=your_username_here \
  -e REDDIT_PASSWORD=your_password_here \
  --name reddit-mcp-server \
  reddit-mcp
```

**Environment Variables Explanation:**
- `-d`: Runs the container in detached mode
- `-p 5000:5000`: Maps port 5000 on your host to port 5000 in the container
- `--name reddit-mcp-server`: Names the container for easy reference

#### 3. Verify the Server is Running

```bash
# Check if container is running
docker ps

# Check container logs
docker logs reddit-mcp-server

# Stop the container
docker stop reddit-mcp-server

# Remove the container
docker rm reddit-mcp-server
```

### Method 2: Local Python Environment

If you prefer to run the server directly with Python:

#### 1. Navigate to the Reddit Server Directory

```bash
cd mcp_servers/reddit
```

#### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
# You can use any text editor, for example:
nano .env
```

Fill in your Reddit API credentials in the `.env` file:

```bash
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username_here
REDDIT_PASSWORD=your_reddit_password_here
```

#### 5. Run the Server

```bash
python main.py
```

## Usage with Klavis AI

Once your Reddit MCP server is running, you can integrate it with the Klavis AI platform:

### Python Integration Example

```python
from klavis import Klavis
from klavis.types import McpServerName, ConnectionType

# Initialize Klavis client
klavis_client = Klavis(api_key="your-klavis-key")

# Create Reddit MCP server instance
reddit_server = klavis_client.mcp_server.create_server_instance(
    server_name="reddit",  # Custom server name
    user_id="user123",
    platform_name="MyApp",
    server_url="http://localhost:5000"  # Your running Reddit server
)

# Get available tools
tools = klavis_client.mcp_server.list_tools(
    server_url=reddit_server.server_url,
    format="openai"
)

print("Available Reddit tools:")
for tool in tools.tools:
    print(f"- {tool['function']['name']}: {tool['function']['description']}")
```

### Direct Tool Usage Examples

#### Browse Subreddit Posts

```python
# Get hot posts from r/python
result = klavis_client.mcp_server.call_tools(
    server_url=reddit_server.server_url,
    tool_name="get_subreddit_posts",
    tool_args={
        "subreddit": "python",
        "sort_by": "hot",
        "limit": 5
    }
)
print(result)
```

#### Search Reddit Posts

```python
# Search for AI-related posts
result = klavis_client.mcp_server.call_tools(
    server_url=reddit_server.server_url,
    tool_name="search_posts",
    tool_args={
        "query": "artificial intelligence",
        "subreddit": "technology",
        "limit": 10
    }
)
print(result)
```

#### Get Post Comments

```python
# Get comments for a specific post
result = klavis_client.mcp_server.call_tools(
    server_url=reddit_server.server_url,
    tool_name="get_post_comments",
    tool_args={
        "post_id": "abc123",  # Replace with actual post ID
        "limit": 20
    }
)
print(result)
```

## Available Tools

### 1. `get_subreddit_posts`
Retrieve posts from a specific subreddit.

**Parameters:**
- `subreddit` (required): Subreddit name without "r/" prefix
- `sort_by`: Sort order - "hot", "new", "top", or "rising" (default: "hot")
- `limit`: Number of posts to retrieve (1-100, default: 10)

**Example:**
```json
{
  "subreddit": "python",
  "sort_by": "top",
  "limit": 15
}
```

### 2. `search_posts`
Search for posts across Reddit or within a specific subreddit.

**Parameters:**
- `query` (required): Search terms
- `subreddit`: Limit search to specific subreddit (optional)
- `sort`: Sort results by "relevance", "hot", "top", "new", or "comments" (default: "relevance")
- `time_filter`: Time period - "all", "year", "month", "week", "day", "hour" (default: "all")
- `limit`: Number of results (1-100, default: 10)

**Example:**
```json
{
  "query": "machine learning",
  "subreddit": "MachineLearning",
  "sort": "top",
  "time_filter": "week",
  "limit": 20
}
```

### 3. `get_post_comments`
Get comments and replies for a specific Reddit post.

**Parameters:**
- `post_id` (required): Reddit post ID
- `limit`: Maximum top-level comments to retrieve (1-500, default: 50)

**Example:**
```json
{
  "post_id": "1a2b3c4",
  "limit": 100
}
```

### 4. `get_user_posts`
Retrieve posts from a specific Reddit user.

**Parameters:**
- `username` (required): Reddit username without "u/" prefix
- `sort`: Sort by "new", "hot", or "top" (default: "new")
- `limit`: Number of posts (1-100, default: 10)

**Example:**
```json
{
  "username": "example_user",
  "sort": "top",
  "limit": 25
}
```

### 5. `get_subreddit_info`
Get detailed information about a subreddit.

**Parameters:**
- `subreddit` (required): Subreddit name without "r/" prefix

**Example:**
```json
{
  "subreddit": "python"
}
```

### 6. `submit_post`
Submit a new post to a subreddit (requires authentication).

**Parameters:**
- `subreddit` (required): Target subreddit name
- `title` (required): Post title
- `content`: Post content for text posts (optional)
- `url`: URL for link posts (optional)

**Note:** Either `content` or `url` should be provided, not both.

**Example Text Post:**
```json
{
  "subreddit": "test",
  "title": "My Test Post",
  "content": "This is a test post created via the Reddit MCP server."
}
```

**Example Link Post:**
```json
{
  "subreddit": "technology",
  "title": "Interesting Article About AI",
  "url": "https://example.com/ai-article"
}
```

## Configuration Options

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `REDDIT_CLIENT_ID` | ✅ | Reddit application client ID | - |
| `REDDIT_CLIENT_SECRET` | ✅ | Reddit application client secret | - |
| `REDDIT_USER_AGENT` | ❌ | User agent string for API requests | "MCP-Reddit-Server/1.0" |
| `REDDIT_USERNAME` | ❌ | Reddit username (required for posting) | - |
| `REDDIT_PASSWORD` | ❌ | Reddit password (required for posting) | - |
| `REDDIT_MCP_SERVER_PORT` | ❌ | Server port number | 5000 |

### Authentication Levels

The server supports two authentication levels:

1. **Read-Only Access**: Only `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` required
   - Browse subreddits
   - Search posts
   - Get comments
   - Get user posts
   - Get subreddit info

2. **Full Access**: Requires all credentials including `REDDIT_USERNAME` and `REDDIT_PASSWORD`
   - All read-only features
   - Submit posts
   - Vote on posts/comments (if implemented)

## Troubleshooting

### Common Issues

#### 1. "Missing required Reddit credentials" Error

**Problem**: The server can't start because Reddit API credentials are missing.

**Solution**: 
- Ensure `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set in your environment or `.env` file
- Verify the credentials are correct by checking your Reddit app settings

#### 2. "403 Forbidden" or Authentication Errors

**Problem**: Reddit API rejects your requests.

**Solutions:**
- Check that your client ID and secret are correct
- Ensure your Reddit application is set to "script" type
- Verify your user agent string is descriptive and unique
- If posting, make sure username and password are correct

#### 3. Rate Limiting Issues

**Problem**: Reddit API returns rate limit errors.

**Solutions:**
- Reddit allows 60 requests per minute for authenticated requests
- Reduce the frequency of requests
- Consider implementing caching for frequently accessed data

#### 4. Docker Container Won't Start

**Problem**: Docker container exits immediately or fails to start.

**Solutions:**
```bash
# Check container logs for errors
docker logs reddit-mcp-server

# Run container interactively for debugging
docker run -it --rm reddit-mcp \
  -e REDDIT_CLIENT_ID=your_id \
  -e REDDIT_CLIENT_SECRET=your_secret \
  python main.py
```

### Testing the Server

You can test if your server is working correctly:

```bash
# Test with curl (if running locally)
curl -X POST http://localhost:5000 \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list", "params": {}}'

# Check server health
curl http://localhost:5000/health
```

## Development

### Project Structure

```
mcp_servers/reddit/
├── main.py              # Main server implementation
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container configuration
├── .env.example       # Environment variables template
└── README.md          # This documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Adding New Tools

To add new Reddit functionality:

1. Extend the `RedditClient` class with new methods
2. Add corresponding tool definitions in `handle_list_tools()`
3. Implement tool logic in `handle_call_tool()`
4. Update this README with documentation

## Security Considerations

- Store Reddit credentials securely and never commit them to version control
- Use environment variables or secure secret management systems
- Consider implementing rate limiting to prevent API abuse
- Run the server in a containerized environment when possible
- Regularly rotate Reddit application credentials

## License

This Reddit MCP server is part of the Klavis AI project and follows the same licensing terms.

## Support

For issues and questions:
- Check the [Klavis AI documentation](https://docs.klavis.ai)
- Open an issue on the [GitHub repository](https://github.com/Klavis-AI/klavis)
- Join the [Discord community](https://discord.gg/p7TuTEcssn)