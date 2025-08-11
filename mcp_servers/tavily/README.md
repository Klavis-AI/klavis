# Tavily MCP Server

A Model Context Protocol (MCP) server that provides access to Tavily's AI-powered search engine. Tavily is specifically optimized for LLM use cases, delivering high-quality, relevant search results with built-in content extraction and filtering.

## 🚀 Features

- **AI-Optimized Search**: Results filtered and ranked specifically for AI agents and LLMs
- **Content Extraction**: Clean content extraction from URLs with noise filtering
- **Direct Answers**: Question-answering search with synthesized responses
- **News Search**: Specialized news search with recency filtering
- **Contextual Search**: Enhanced search using additional context
- **Domain Control**: Include/exclude specific domains from search results
- **Structured Responses**: Pydantic models for type-safe, structured data

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install Dependencies

```bash
# Using uv (recommended)
uv pip install "mcp[cli]" tavily-python python-dotenv

# Or using pip
pip install "mcp[cli]" tavily-python python-dotenv
```

### Get Tavily API Key

1. Visit [Tavily](https://app.tavily.com) and create an account
2. Get your free API key (1,000 requests/month on free tier)
3. Set the environment variable:

```bash
export TAVILY_API_KEY="tvly-YOUR_API_KEY"
```

Or create a `.env` file in the project root:
```env
TAVILY_API_KEY=tvly-YOUR_API_KEY
```

## 📁 Project Structure

```
tavily_mcp_server/
├── __init__.py
├── main.py                 # Entry point and server setup
├── config.py              # Configuration and environment management
├── models.py              # Pydantic models for structured responses
├── client.py              # Tavily client wrapper with error handling
├── utils.py               # Utility functions
├── tools/                 # Tool implementations
│   ├── __init__.py
│   ├── search.py         # General search tools
│   ├── extract.py        # Content extraction tool
│   ├── news.py           # News search tool
│   └── context.py        # Context search tool
├── resources.py           # MCP resources
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <your-repo>
   ```

2. **Set API Key**:
   ```bash
   export TAVILY_API_KEY="tvly-YOUR_API_KEY"
   ```

3. **Run the Server**:
   ```bash
   uv run mcp dev main.py
   ```

4. **Configure Claude Desktop**:
   Add to your Claude Desktop configuration file:

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "tavily-search": {
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/tavily_mcp_server",
           "run",
           "mcp",
           "dev",
           "main.py"
         ],
         "env": {
           "TAVILY_API_KEY": "tvly-YOUR_API_KEY"
         }
       }
     }
   }
   ```

## 🔧 Available Tools

### 1. **tavily_search** - General AI-Optimized Search
Perform comprehensive web searches optimized for AI consumption.

```python
tavily_search(
    query="artificial intelligence trends 2024",
    search_depth="basic",  # "basic" or "advanced"
    max_results=5,
    include_images=False,
    include_answer=True
)
```

### 2. **tavily_extract** - Content Extraction
Extract clean, readable content from specific URLs.

```python
tavily_extract(url="https://example.com/article")
```

### 3. **tavily_qna** - Question Answering
Get direct answers to specific questions with supporting sources.

```python
tavily_qna(
    query="What is the capital of France?",
    search_depth="advanced",
    max_results=3
)
```

### 4. **tavily_news_search** - News Search
Search for recent news articles with time filtering.

```python
tavily_news_search(
    query="climate change",
    days=7,  # Last 7 days
    max_results=10,
    include_images=True
)
```

### 5. **tavily_search_context** - Contextual Search
Enhanced search using additional context for better relevance.

```python
tavily_search_context(
    query="machine learning",
    context="I want to understand the basics for beginners",
    max_results=5
)
```

## 📊 Response Format

All search tools return structured responses:

```json
{
  "query": "search query",
  "answer": "Direct answer when available",
  "results": [
    {
      "title": "Result title",
      "url": "https://example.com",
      "content": "Content summary",
      "score": 0.95,
      "raw_content": "Full content if requested"
    }
  ],
  "images": ["https://image1.jpg"],
  "response_time": "1.23",
  "follow_up_questions": ["Related question 1", "Related question 2"]
}
```

## ⚙️ Configuration

### Environment Variables
- `TAVILY_API_KEY` - Your Tavily API key (required)

### Default Settings
- `MAX_RESULTS_LIMIT`: 20 (API limit)
- `DEFAULT_MAX_RESULTS`: 5
- `DEFAULT_SEARCH_DEPTH`: "basic"
- `DEFAULT_TOPIC`: "general"

### Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | - | Search query (required) |
| `search_depth` | string | "basic" | "basic" or "advanced" |
| `topic` | string | "general" | "general" or "news" |
| `max_results` | int | 5 | Max results (1-20) |
| `include_images` | bool | false | Include image URLs |
| `include_answer` | bool | true | Include direct answer |
| `include_raw_content` | bool | false | Include full content |
| `include_domains` | list | null | Specific domains to search |
| `exclude_domains` | list | null | Domains to exclude |

## 🔍 Usage Examples

### Basic Web Search
```python
# Search for AI trends with basic depth
result = tavily_search("artificial intelligence trends 2024")
print(f"Answer: {result.answer}")
for r in result.results:
    print(f"- {r.title}: {r.url}")
```

### News Search with Time Filter
```python
# Get recent climate news from last week
news = tavily_news_search(
    query="climate change",
    days=7,
    max_results=5,
    include_images=True
)
```

### Content Extraction
```python
# Extract content from a specific URL
content = tavily_extract("https://example.com/article")
print(content.raw_content)
```

### Domain-Specific Search
```python
# Search only academic sources
academic_results = tavily_search(
    query="quantum computing research",
    include_domains=["arxiv.org", "nature.com", "science.org"],
    search_depth="advanced"
)
```

## 🚨 Error Handling

The server includes comprehensive error handling:

- **API Errors**: Gracefully handled with informative error messages
- **Network Issues**: Automatic retries and fallback responses
- **Invalid Parameters**: Validation with helpful error descriptions
- **Rate Limits**: Proper error reporting for quota exceeded

## 📈 Rate Limits

**Free Tier**: 1,000 requests/month
**Paid Tiers**: Higher limits available

Monitor your usage at [Tavily Dashboard](https://app.tavily.com)

## 🧪 Testing

```bash
# Test the server
python -c "
from tools.search import tavily_search
result = tavily_search('test query')
print(f'Success: {len(result.results)} results')
"
```