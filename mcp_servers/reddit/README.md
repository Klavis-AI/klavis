# Reddit MCP Server for Klavis AI

A Model Context Protocol (MCP) server that provides atomic tools for interacting with the Reddit API.

## Features

- **6 Atomic Tools** - Each tool performs one specific, well-defined job
- **AI-Friendly Design** - Natural language queries work seamlessly
- **Robust Error Handling** - Graceful handling of API issues and network problems
- **Client Credentials Authentication** - Secure OAuth2 authentication
- **Comprehensive Logging** - Detailed logs with timestamps for debugging

## Available Tools

1. **search_reddit_posts** - Search for posts across Reddit using keywords
2. **get_subreddit_posts** - Get latest posts from specific subreddits
3. **get_trending_subreddits** - Get currently trending subreddits
4. **get_post_details** - Get detailed information about specific posts
5. **get_post_comments** - Get comments for specific Reddit posts
6. **get_user_profile** - Get information about Reddit users

## Prerequisites

- Python 3.8 or higher
- Reddit API credentials (Client ID and Client Secret)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd reddit-mcp-server
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Reddit API Setup

1. **Create a Reddit App**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Fill in the required fields:
     - **Name**: Your app name (e.g., "Reddit MCP Server")
     - **Description**: Brief description of your app
     - **About URL**: Can be left blank or your GitHub repo
     - **Redirect URI**: http://localhost:8080
   - Select "script" as the app type
   - Click "Create App"

2. **Get Your Credentials**
   - **Client ID**: The string under your app name (24 characters)
   - **Client Secret**: The "secret" field in your app settings

## Configuration

1. **Copy the environment template**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your credentials**
   ```bash
   # Reddit API Credentials (Client Credentials Authentication)
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USER_AGENT=klavis-reddit-mcp/1.0
   ```

## Usage

1. **Start the server**
   ```bash
   python server.py
   ```

2. **Configure MCP Client (e.g., Cursor)**
   ```json
   {
     "mcpServers": {
       "reddit": {
         "command": "python",
         "args": ["server.py"],
         "cwd": "/path/to/reddit-mcp-server"
       }
     }
   }
   ```

3. **Test with natural language queries**
   - "Search Reddit for posts about Python programming"
   - "Get the top 5 posts from r/programming"
   - "What subreddits are trending right now?"
   - "Get details about Reddit post 1m7b3v6"
   - "Show me comments for post 1m7b3v6"
   - "Get profile info for user Educational-Baby7421"

## Architecture

```
reddit-mcp-server/
├── server.py              # Main MCP server implementation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── Dockerfile            # Containerization support
├── README.md             # This documentation
└── tools/                # Modular tool implementations
    ├── __init__.py       # Package initializer
    ├── base.py           # Base Reddit API client
    ├── search.py         # Search tools
    ├── subreddits.py     # Subreddit tools
    ├── posts.py          # Post detail tools
    └── users.py          # User profile tools
```

## Error Handling

The server gracefully handles various error scenarios:

- **Authentication failures** - Clear error messages for invalid credentials
- **Rate limits** - Automatic retry with exponential backoff
- **Invalid inputs** - Validation and helpful error messages
- **Network issues** - Connection timeout handling
- **API errors** - Proper error propagation with context

## Development

To add new tools:

1. Create a new file in the `tools/` directory
2. Implement the tool logic following the existing pattern
3. Register the tool in `server.py`
4. Update this README with the new tool description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📹 Proof of Correctness

Video demonstration showing all 6 tools working with real-time logs:
**https://youtu.be/o1PJg6jgPmM**

---

**Last updated: August 5, 2025**