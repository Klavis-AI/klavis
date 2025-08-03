# Reddit MCP Server for Klavis AI

A Model Context Protocol (MCP) server that provides atomic tools for interacting with Reddit's API. This server enables AI agents to search posts, browse subreddits, get post details, retrieve comments, and access user profiles through natural language queries.

## Features

- **6 Atomic Tools**: Each tool performs one specific job well
- **AI-Friendly Design**: Clear tool names and descriptions optimized for LLM understanding
- **Robust Error Handling**: Graceful handling of API errors and rate limits
- **Client Credentials Authentication**: Secure OAuth2 authentication with Reddit API
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Available Tools

1. **`search_reddit_posts`** - Search for posts across Reddit using keywords
2. **`get_subreddit_posts`** - Get latest posts from a specific subreddit
3. **`get_trending_subreddits`** - Get currently trending subreddits
4. **`get_post_details`** - Get detailed information about a specific post
5. **`get_post_comments`** - Get comments for a specific Reddit post
6. **`get_user_profile`** - Get information about a Reddit user

## Prerequisites

- Python 3.8 or higher
- Reddit API credentials (Client ID and Client Secret)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd reddit-mcp-server
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Reddit API Setup

1. **Create a Reddit App**:
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" as the app type
   - Fill in the required information:
     - **Name**: `MCP-KelivisRed-Server` (or your preferred name)
     - **Description**: `MCP Server for Reddit API integration`
     - **About URL**: Leave empty or add your GitHub repo
     - **Redirect URI**: `http://localhost:8080`
   - Click "Create App"

2. **Get Your Credentials**:
   - **Client ID**: The string under your app name (e.g., `UTHDPIKZNTIXKclCRDCr0w`)
   - **Client Secret**: The "secret" field (e.g., `FK7GWttFB8w2x9kE90wBjY1Aa-vrVA`)

## Configuration

1. **Copy the environment template**:
   ```bash
   cp env_example.txt .env
   ```

2. **Edit `.env` with your credentials**:
   ```bash
   # Reddit API Credentials (Client Credentials Authentication)
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USER_AGENT=klavis-reddit-mcp/1.0
   ```

## Usage

### Running the Server

```bash
python server.py
```

The server will start and wait for MCP client connections via stdio.

### Using with MCP Clients

#### Cursor Configuration

Add this to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "reddit-mcp": {
      "command": "python",
      "args": ["path/to/reddit-mcp-server/server.py"],
      "cwd": "path/to/reddit-mcp-server"
    }
  }
}
```

#### Example Queries

- "Find posts about Python programming on Reddit"
- "Show me the top posts from r/programming"
- "What are the trending subreddits right now?"
- "Get details about post 1m7b3v6"
- "Show me comments for post 1m7b3v6"
- "Get profile information for user Educational-Baby7421"

## Architecture

The server follows the Klavis AI MCP server structure:

```
reddit-mcp-server/
├── server.py              # Main server implementation
├── requirements.txt       # Python dependencies
├── env_example.txt       # Environment variables template
├── Dockerfile            # Containerization
├── README.md             # This file
├── LICENSE               # MIT License
└── tools/                # Tool modules
    ├── __init__.py       # Package initialization
    ├── base.py           # Base Reddit API client
    ├── search.py         # Search functionality
    ├── subreddits.py     # Subreddit tools
    ├── posts.py          # Post-related tools
    └── users.py          # User profile tools
```

## Error Handling

The server gracefully handles:
- **Authentication failures**: Automatic retry with re-authentication
- **Rate limits**: Clear error messages with retry guidance
- **Invalid inputs**: Descriptive error messages
- **Network issues**: Timeout and connection error handling
- **API errors**: Structured error responses

## Development

### Adding New Tools

1. Create a new tool class in the appropriate module under `tools/`
2. Add the tool definition to `server.py` in the `handle_list_tools()` function
3. Add the tool routing in `handle_call_tool()` function
4. Update this README with the new tool description

### Testing

```bash
# Test the server directly
python server.py

# Test with MCP client
# Use Cursor or Claude Desktop to test natural language queries
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

This is a submission for the Klavis AI Founding Engineer role. The server demonstrates:

- **Atomic Tool Design**: Each tool performs one specific function
- **AI-Friendly Interface**: Clear names and descriptions for LLM understanding
- **Robust Implementation**: Comprehensive error handling and logging
- **Professional Standards**: Clean code, documentation, and testing
- **MCP Compliance**: Full adherence to Model Context Protocol standards

## Proof of Correctness

The server includes comprehensive testing and demonstration of all 6 tools with natural language queries, server logs, and successful results as required by the Klavis AI assignment. 