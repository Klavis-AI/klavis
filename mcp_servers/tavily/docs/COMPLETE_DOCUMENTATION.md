# Tavily MCP Server - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Documentation](#api-documentation)
4. [Security & Compliance](#security--compliance)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Error Handling](#error-handling)
8. [Performance & Caching](#performance--caching)
9. [Troubleshooting](#troubleshooting)
10. [Integration Guide](#integration-guide)

---

## Overview

The Tavily MCP Server is a Model Context Protocol (MCP) server that provides web search, content extraction, and web crawling capabilities using the Tavily API. It's designed to integrate seamlessly with Klavis AI as a custom MCP server.

### Key Features
- **Web Search**: Basic and advanced search with filtering options
- **Content Extraction**: Extract content from single or multiple URLs
- **Web Crawling**: Configurable website crawling with depth and breadth control
- **Async Operations**: All tools implemented as async functions
- **Comprehensive Error Handling**: Standardized error messages
- **Intelligent Caching**: Performance optimization with configurable TTL
- **Rate Limiting**: Built-in throttling to respect API limits

---

## Architecture

### Project Structure
```
tavily/
├── app.py                 # FastMCP application setup
├── server.py             # Server entry point
├── pyproject.toml        # Dependencies and configuration
├── tools/                # Core functionality
│   ├── client.py         # HTTP client configuration
│   ├── search.py         # Web search implementation
│   ├── extract.py        # Content extraction
│   ├── crawl.py          # Web crawling
│   ├── types.py          # Pydantic data models
│   └── errors.py         # Error handling
└── docs/                 # Documentation
```

### Core Components

#### 1. FastMCP Application (`app.py`)
```python
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("Tavily")
```

#### 2. Server Entry Point (`server.py`)
```python
from app import mcp

# Importing registers the tools with FastMCP
import tools.search   # noqa: F401
import tools.extract  # noqa: F401
import tools.crawl    # noqa: F401

if __name__ == "__main__":
    print("Starting MCP server 'Tavily' on stdio…")
    mcp.run()
```

#### 3. HTTP Client (`tools/client.py`)
```python
def auth_headers() -> dict:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("Missing TAVILY_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "KlavisMCP-Tavily/0.1",
        "X-Request-Id": str(uuid.uuid4()),
    }

def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE,
        timeout=httpx.Timeout(REQUEST_TIMEOUT_S, connect=CONNECT_TIMEOUT_S),
        headers=auth_headers(),
    )
```

#### 4. Data Models (`tools/types.py`)
```python
class SearchResponse(BaseModel):
    query: Optional[str] = None
    answer: Optional[str] = None
    results: List[Result] = Field(default_factory=list)
    response_time: Optional[Union[str, float]] = None
    auto_parameters: Optional[Dict[str, Any]] = None

class ExtractResponse(BaseModel):
    results: List[ExtractItem] = Field(default_factory=list)

class CrawlResponse(BaseModel):
    pages: List[CrawlPage] = Field(default_factory=list)
```

---

## API Documentation

### 1. tavily_search

**Purpose**: Search the web for current information and reputable sources.

**Tool Name**: `tavily_search`

**Description**: 
```
Search the web for a query and return summarized results. 
Use when you need current information or reputable sources. 
Returns an optional synthesized answer plus result items.
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | - | Non-empty search text |
| `search_depth` | `Literal["basic", "advanced"]` | No | `"basic"` | Search depth level |
| `max_results` | `int` | No | `5` | Number of results (1-10) |
| `include_answer` | `bool` | No | `True` | Include synthesized answer |
| `include_raw_content` | `bool` | No | `False` | Include raw content snippets |
| `days` | `Optional[int]` | No | `None` | Freshness filter (0-365 days) |
| `topic` | `Optional[str]` | No | `None` | Topic focus string |

#### Implementation Details

```python
@mcp.tool(
    name="tavily_search",
    description=(
        "Search the web for a query and return summarized results. "
        "Use when you need current information or reputable sources. "
        "Returns an optional synthesized answer plus result items."
    ),
)
async def tavily_search(
    query: str,
    search_depth: Literal["basic", "advanced"] = "basic",
    max_results: int = 5,
    include_answer: bool = True,
    include_raw_content: bool = False,
    days: Optional[int] = None,
    topic: Optional[str] = None,
) -> SearchResponse:
```

#### Example Request
```python
{
    "query": "latest AI developments",
    "search_depth": "basic",
    "max_results": 5,
    "include_answer": True
}
```

#### Example Response
```json
{
    "query": "latest AI developments",
    "answer": "Recent AI developments include breakthroughs in large language models...",
    "results": [
        {
            "url": "https://example.com/ai-news",
            "title": "Latest AI Breakthroughs in 2024",
            "content": "Researchers have made significant progress...",
            "score": 0.95,
            "favicon": "https://example.com/favicon.ico"
        }
    ],
    "response_time": "1.2",
    "auto_parameters": {
        "search_depth": "basic",
        "max_results": 5
    }
}
```

### 2. tavily_extract

**Purpose**: Extract primary content from one or more URLs.

**Tool Name**: `tavily_extract`

**Description**:
```
Extract the primary content from one or more URLs. 
Use when you already know the URL(s) and need cleaned text and optional images.
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | `Union[str, List[str]]` | Yes | - | URL(s) to extract from |
| `include_images` | `bool` | No | `False` | Include images in results |

#### Implementation Details

```python
@mcp.tool(
    name="tavily_extract",
    description=(
        "Extract the primary content from one or more URLs. "
        "Use when you already know the URL(s) and need cleaned text and optional images."
    ),
)
async def tavily_extract(urls: Union[str, List[str]], include_images: bool = False) -> ExtractResponse:
```

#### Example Request
```python
{
    "urls": [
        "https://example.com/article1",
        "https://example.com/article2"
    ],
    "include_images": True
}
```

#### Example Response
```json
{
    "results": [
        {
            "url": "https://example.com/article",
            "title": "Article Title",
            "content": "Extracted article content...",
            "images": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg"
            ]
        }
    ]
}
```

### 3. tavily_crawl

**Purpose**: Crawl websites with configurable depth and breadth.

**Tool Name**: `tavily_crawl`

**Description**:
```
Crawl from a single start URL up to max_depth/max_breadth/limit, returning extracted pages. 
Use for site exploration and content collection when you need multiple pages, not just one.
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `str` | Yes | - | Root URL to begin crawl |
| `max_depth` | `int` | No | `1` | Crawl depth (1-3) |
| `max_breadth` | `int` | No | `20` | Links per level (≥1) |
| `limit` | `int` | No | `50` | Maximum pages (1-500) |
| `instructions` | `Optional[str]` | No | `None` | Natural language guidance |
| `select_paths` | `Optional[List[str]]` | No | `None` | Include path patterns |
| `select_domains` | `Optional[List[str]]` | No | `None` | Include domain patterns |
| `exclude_paths` | `Optional[List[str]]` | No | `None` | Exclude path patterns |
| `exclude_domains` | `Optional[List[str]]` | No | `None` | Exclude domain patterns |
| `allow_external` | `bool` | No | `True` | Include external domains |
| `include_images` | `bool` | No | `False` | Include images in results |
| `categories` | `Optional[List[str]]` | No | `None` | Content categories |
| `extract_depth` | `Literal["basic", "advanced"]` | No | `"basic"` | Extraction depth |
| `format` | `Literal["markdown", "text"]` | No | `"markdown"` | Output format |
| `include_favicon` | `bool` | No | `False` | Include favicon URLs |

#### Implementation Details

```python
@mcp.tool(
    name="tavily_crawl",
    description=(
        "Crawl from a single start URL up to max_depth/max_breadth/limit, returning extracted pages. "
        "Use for site exploration and content collection when you need multiple pages, not just one."
    ),
)
async def tavily_crawl(
    url: str,
    max_depth: int = 1,
    max_breadth: int = 20,
    limit: int = MAX_PAGES_DEFAULT,
    instructions: Optional[str] = None,
    select_paths: Optional[List[str]] = None,
    select_domains: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    allow_external: bool = True,
    include_images: bool = False,
    categories: Optional[List[str]] = None,
    extract_depth: Literal["basic", "advanced"] = "basic",
    format: Literal["markdown", "text"] = "markdown",
    include_favicon: bool = False,
) -> CrawlResponse:
```

#### Example Request
```python
{
    "url": "https://docs.example.com",
    "max_depth": 3,
    "max_breadth": 15,
    "limit": 100,
    "instructions": "Focus on API documentation and tutorials",
    "select_paths": ["/api/", "/docs/"],
    "exclude_paths": ["/blog/", "/news/"],
    "format": "markdown",
    "include_images": True
}
```

#### Example Response
```json
{
    "pages": [
        {
            "url": "https://example.com",
            "title": "Example Website",
            "content": "# Welcome to Example\n\nThis is the main page...",
            "images": ["https://example.com/logo.png"],
            "depth": 0,
            "parent": null
        },
        {
            "url": "https://example.com/docs",
            "title": "Documentation",
            "content": "## Documentation\n\nHere you can find...",
            "images": [],
            "depth": 1,
            "parent": "https://example.com"
        }
    ]
}
```

---

## Security & Compliance

### API Key Management

#### Implementation
```python
def auth_headers() -> dict:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("Missing TAVILY_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "KlavisMCP-Tavily/0.1",
        "X-Request-Id": str(uuid.uuid4()),
    }
```

#### Security Features
- **Environment Variable Storage**: API keys stored in environment variables
- **Runtime Validation**: Missing API keys trigger immediate error
- **Bearer Token Authentication**: Secure token-based authentication
- **Request ID Tracking**: Unique UUID for audit trails

### Rate Limiting & Throttling

#### Implementation
```python
SEMAPHORE_MAX = int(os.getenv("TAVILY_CONCURRENCY", "8"))
_SEM = asyncio.Semaphore(SEMAPHORE_MAX)

async def tavily_search(...):
    async with _SEM:  # Limits concurrent requests
        r = await _post_with_retry("/search", payload)
```

#### Features
- **Concurrent Request Limiting**: Maximum 8 concurrent requests (configurable)
- **Semaphore-based Throttling**: Prevents overwhelming the API
- **Automatic Retry Logic**: Exponential backoff for failed requests
- **Configurable Limits**: All limits adjustable via environment variables

### Input Validation & Sanitization

#### Query Sanitization
```python
def _clean_query(q: str, max_len: int = 500) -> str:
    q = "".join(ch for ch in q if ch.isprintable())
    q = q.strip()
    return q[:max_len]
```

#### Parameter Validation
```python
def _validate_params(query: str, search_depth: str, max_results: int, days: Optional[int]) -> None:
    if not isinstance(query, str) or not query.strip():
        raise RuntimeError("query must be a non-empty string")
    if search_depth not in ALLOWED_DEPTH:
        raise RuntimeError("search_depth must be 'basic' or 'advanced'")
    if not isinstance(max_results, int) or not 1 <= max_results <= MAX_RESULTS_CAP:
        raise RuntimeError(f"max_results must be 1..{MAX_RESULTS_CAP}")
    if days is not None and not (0 <= days <= 365):
        raise RuntimeError("days must be between 0 and 365")
```

### Error Handling & Security

#### Standardized Error Messages
```python
ERROR_HINTS = {
    401: "ERR_UNAUTHORIZED: check TAVILY_API_KEY.",
    429: "ERR_RATE_LIMIT: Tavily rate limited the request. Retry later or reduce load.",
    402: "ERR_PAYMENT_REQUIRED: billing or quota issue.",
    400: "ERR_BAD_REQUEST: invalid parameters for Tavily. Check your inputs.",
    408: "ERR_TIMEOUT: Tavily took too long to respond.",
    500: "ERR_UPSTREAM_500: Tavily internal error.",
    502: "ERR_UPSTREAM_502: bad gateway from Tavily.",
    503: "ERR_UPSTREAM_503: Tavily service unavailable.",
    504: "ERR_UPSTREAM_504: Tavily gateway timeout.",
}
```

#### Security Benefits
- **No sensitive data exposure** in error messages
- **Consistent error format** for automated handling
- **Actionable error hints** for resolution
- **Upstream response sanitization** to prevent information leakage

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TAVILY_API_KEY` | **Required** | Your Tavily API key |
| `TAVILY_BASE_URL` | `https://api.tavily.com` | Tavily API base URL |
| `TAVILY_TIMEOUT_S` | `20` | Request timeout in seconds |
| `TAVILY_CONNECT_TIMEOUT_S` | `5` | Connection timeout in seconds |
| `TAVILY_MAX_RETRIES` | `2-3` | Maximum retry attempts |
| `TAVILY_CONCURRENCY` | `8` | Maximum concurrent requests |
| `TAVILY_CACHE_TTL_S` | `120` | Cache TTL in seconds |
| `TAVILY_MAX_RESULTS_CAP` | `10` | Maximum search results |
| `TAVILY_CRAWL_MAX_PAGES` | `50` | Maximum pages for crawling |
| `LOG_LEVEL` | `INFO` | Logging level |

### Dependencies

```toml
[project]
dependencies = [
  "mcp[cli]>=1.2.0",        # MCP Python SDK + CLI runner
  "httpx>=0.27.0",          # HTTP client
  "pydantic>=2.6.0",        # request/response schemas
  "python-dotenv>=1.0.1",   # load .env
  "tenacity>=8.2.3",        # retries with backoff
  "typing-extensions>=4.12.2"
]
```

---

## Usage Examples

### Basic Web Search
```python
# Search for recent AI news
result = await tavily_search(
    query="latest artificial intelligence developments",
    search_depth="basic",
    max_results=5,
    days=30
)
```

### Content Extraction
```python
# Extract content from multiple URLs
result = await tavily_extract(
    urls=[
        "https://example.com/article1",
        "https://example.com/article2"
    ],
    include_images=True
)
```

### Website Crawling
```python
# Crawl a documentation site
result = await tavily_crawl(
    url="https://docs.example.com",
    max_depth=2,
    max_breadth=10,
    limit=25,
    instructions="Focus on API documentation",
    select_paths=["/api/", "/docs/"],
    format="markdown"
)
```

### Advanced Search with Filters
```python
# Advanced search with topic focus
result = await tavily_search(
    query="machine learning trends",
    search_depth="advanced",
    max_results=10,
    days=90,
    topic="technology",
    include_raw_content=True
)
```

---

## Error Handling

### Error Types

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `ERR_UNAUTHORIZED` | Missing or invalid API key | Check TAVILY_API_KEY environment variable |
| `ERR_RATE_LIMIT` | Rate limit exceeded | Retry later or reduce request frequency |
| `ERR_BAD_REQUEST` | Invalid parameters | Check parameter types and values |
| `ERR_PAYMENT_REQUIRED` | Billing or quota issue | Check Tavily account status |
| `ERR_UPSTREAM_<status>` | Upstream API error | Check Tavily service status |

### Error Response Format
```json
{
    "error": "ERR_RATE_LIMIT: Tavily rate limited the request. Retry later or reduce load. Upstream says: Rate limit exceeded"
}
```

### Retry Logic Implementation
```python
async def _post_with_retry(path: str, payload: dict) -> httpx.Response:
    retry_statuses = {429, 502, 503, 504}
    attempt = 0
    while attempt <= MAX_RETRIES:
        try:
            r = await http.post(f"{BASE}{path}", json=payload)
            if r.status_code in retry_statuses:
                sleep_s = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(min(sleep_s, 8))
                attempt += 1
                continue
            return r
        except httpx.RequestError as e:
            await asyncio.sleep(min(2 ** attempt, 8))
            attempt += 1
```

---

## Performance & Caching

### Caching Implementation
```python
def _cache_key(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)

def _cache_get(key: str):
    ent = _CACHE.get(key)
    if not ent:
        return None
    if time.time() > ent["exp"]:
        _CACHE.pop(key, None)
        return None
    return ent["data"]

def _cache_set(key: str, data: Dict[str, Any]):
    _CACHE[key] = {"data": data, "exp": time.time() + CACHE_TTL_S}
```

### Caching Features
- **Search Results**: Cached for 120 seconds (configurable)
- **Extract Results**: Cached for 120 seconds
- **Crawl Results**: Cached for 120 seconds
- **Cache Key**: Deterministic based on request parameters
- **Time-based Expiration**: Automatic cleanup of expired entries

### Performance Optimizations
- **Async Operations**: All tools are async for better concurrency
- **Connection Pooling**: HTTP client reuses connections
- **Semaphore Limiting**: Prevents overwhelming the API
- **Response Shaping**: Optimized data transformation
- **Deterministic Cache Keys**: Prevents cache poisoning

---

## Troubleshooting

### Common Issues

#### 1. Missing API Key
**Error**: `ERR_UNAUTHORIZED: check TAVILY_API_KEY.`
**Solution**: Set the `TAVILY_API_KEY` environment variable

#### 2. Rate Limiting
**Error**: `ERR_RATE_LIMIT: Tavily rate limited the request.`
**Solution**: 
- Reduce concurrent requests by setting `TAVILY_CONCURRENCY` to a lower value
- Implement exponential backoff in your application
- Check your Tavily account usage limits

#### 3. Invalid Parameters
**Error**: `ERR_BAD_REQUEST: invalid parameters for Tavily.`
**Solution**: 
- Check parameter types and values
- Ensure query is not empty
- Verify search_depth is "basic" or "advanced"
- Check max_results is between 1 and 10

#### 4. Network Timeouts
**Error**: `ERR_TIMEOUT: Tavily took too long to respond.`
**Solution**:
- Increase `TAVILY_TIMEOUT_S` if needed
- Check network connectivity
- Verify Tavily service status

#### 5. Billing Issues
**Error**: `ERR_PAYMENT_REQUIRED: billing or quota issue.`
**Solution**:
- Check your Tavily account billing status
- Verify API quota limits
- Contact Tavily support if needed

### Debugging Tips

#### 1. Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
mcp dev server.py
```

#### 2. Check Request IDs
Each request includes a unique UUID for tracking:
```python
"X-Request-Id": str(uuid.uuid4())
```

#### 3. Monitor Performance
Logs include performance metrics:
```
tavily_search ok depth=basic max=5 ms=1200.5 results=5
```

#### 4. Validate Environment
```python
import os
print(f"API Key present: {bool(os.getenv('TAVILY_API_KEY'))}")
print(f"Base URL: {os.getenv('TAVILY_BASE_URL', 'https://api.tavily.com')}")
```

---

## Integration Guide

### MCP Client Configuration

#### Basic Configuration
```json
{
  "mcpServers": {
    "tavily": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "TAVILY_API_KEY": "your_tavily_api_key_here"
      }
    }
  }
}
```

#### Using MCP Dev Command
```bash
# Set environment variable
export TAVILY_API_KEY=your_key_here

# Run server
mcp dev server.py
```

### Klavis AI Integration

#### 1. Install Dependencies
```bash
pip install -e .
```

#### 2. Set Environment Variables
```bash
export TAVILY_API_KEY=your_tavily_api_key_here
```

#### 3. Start Server
```bash
mcp dev server.py
```

#### 4. Configure Klavis AI
Add the Tavily MCP server to your Klavis AI configuration to enable web search, content extraction, and crawling capabilities.

### Environment Setup Examples

#### Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment
echo "TAVILY_API_KEY=your_key_here" > .env

# Run server
mcp dev server.py
```

#### Production Environment
```bash
# Install dependencies
pip install -e .

# Set environment variables
export TAVILY_API_KEY=your_production_key
export TAVILY_CONCURRENCY=4
export TAVILY_CACHE_TTL_S=300

# Run server
mcp dev server.py
```

### Testing Integration

#### 1. Test Basic Search
```python
# Test search functionality
result = await tavily_search(
    query="test query",
    max_results=1
)
print(f"Found {len(result.results)} results")
```

#### 2. Test Content Extraction
```python
# Test extraction functionality
result = await tavily_extract(
    urls="https://example.com",
    include_images=False
)
print(f"Extracted content from {len(result.results)} URLs")
```

#### 3. Test Crawling
```python
# Test crawling functionality
result = await tavily_crawl(
    url="https://example.com",
    max_depth=1,
    limit=5
)
print(f"Crawled {len(result.pages)} pages")
```

---

## Conclusion

The Tavily MCP Server provides a robust, secure, and performant interface to Tavily's web search, content extraction, and crawling capabilities. With comprehensive error handling, intelligent caching, and rate limiting, it's designed for production use in MCP environments.

Key strengths:
- **Security**: Secure API key management and input validation
- **Performance**: Async operations with intelligent caching
- **Reliability**: Comprehensive error handling and retry logic
- **Flexibility**: Configurable parameters for various use cases
- **Compliance**: MCP protocol compliance with standardized responses

For support or questions, refer to the troubleshooting section or contact the development team.
