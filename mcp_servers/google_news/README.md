# Google News MCP Server

This is a Model Context Protocol (MCP) server for Google News using SerpApi. It provides tools to search news articles and get trending news from Google News.

## Features

- **News Search**: Search for news articles by query, topic, publication, or story
- **Trending News**: Get the most popular news articles
- **Localization**: Support for different countries and languages
- **Dual Transport**: Supports both SSE and StreamableHTTP protocols

## Tools

### google_news_search
Search Google News for articles using various parameters:
- `query` (optional): Search query for news articles
- `country` (optional): Two-letter country code (default: "us")
- `language` (optional): Two-letter language code (default: "en")  
- `topic_token` (optional): Token for specific news topic
- `publication_token` (optional): Token for specific publisher
- `story_token` (optional): Token for full coverage of specific story

### google_news_trending
Get trending Google News articles:
- `country` (optional): Two-letter country code (default: "us")
- `language` (optional): Two-letter language code (default: "en")

## Setup

### Prerequisites
- Python 3.11+
- SerpApi account and API key

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:

**Option 1: Using .env file (recommended)**
```bash
# Copy the example file and edit it
cp .env.example .env
# Edit .env with your actual values
```

**Option 2: Using export commands**
```bash
export SERPAPI_API_KEY="your_serpapi_key_here"
export GOOGLE_NEWS_MCP_SERVER_PORT="5000"  # Optional, defaults to 5000
```

3. Run the server:
```bash
python server.py
```

### Docker

Build and run with Docker:
```bash
# From the project root directory
docker build -f mcp_servers/google_news/Dockerfile -t google-news-mcp .
docker run -p 5000:5000 -e SERPAPI_API_KEY="your_key" google-news-mcp
```

## Configuration

The server supports configuration through environment variables:

- `SERPAPI_API_KEY`: Your SerpApi API key (required)
- `GOOGLE_NEWS_MCP_SERVER_PORT`: Port to run the server on (default: 5000)

## API Endpoints

- SSE: `http://localhost:5000/sse`
- StreamableHTTP: `http://localhost:5000/mcp`

## Authentication

You can provide the SerpApi key in two ways:
1. Environment variable: `SERPAPI_API_KEY`
2. Request header: `x-auth-token` (overrides environment variable)

## Usage Examples

### Search for specific news
```python
# Search for news about "climate change"
{
    "tool": "google_news_search",
    "arguments": {
        "query": "climate change",
        "country": "us",
        "language": "en"
    }
}
```

### Get trending news
```python
# Get trending news for UK in English
{
    "tool": "google_news_trending", 
    "arguments": {
        "country": "uk",
        "language": "en"
    }
}
```

### Search by topic token
```python
# Search using a specific topic token
{
    "tool": "google_news_search",
    "arguments": {
        "topic_token": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB"
    }
}
```

## Response Format

All responses are JSON formatted and include:
- `news_results`: Array of news articles
- `search_metadata`: Information about the search
- Each article includes title, source, link, thumbnail, date, and authors

## Error Handling

The server includes comprehensive error handling:
- Missing API key validation
- HTTP request error handling  
- Structured error responses
- Detailed logging for debugging

## Getting SerpApi Key

1. Sign up at [SerpApi](https://serpapi.com/)
2. Get your API key from the dashboard
3. Set it as an environment variable or pass it in headers