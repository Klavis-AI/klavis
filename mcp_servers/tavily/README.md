# Tavily MCP Server for Klavis AI

A Model Context Protocol (MCP) server that provides web search, content extraction, and web crawling capabilities using the Tavily API. This server is designed to integrate seamlessly with Klavis AI as a custom MCP server.

## Features

### 🔍 Web Search (`tavily_search`)
Search the web for current information and reputable sources with configurable depth and filtering options.

**Capabilities:**
- Basic and advanced search depth
- Configurable result limits 
- Optional synthesized answers
- Freshness filtering 
- Topic-based filtering
- Intelligent caching for performance
- Retry logic with exponential backoff

### 📄 Content Extraction (`tavily_extract`)
Extract primary content from one or more URLs with optional image extraction.

**Capabilities:**
- Extract content from multiple URLs simultaneously
- Optional image extraction
- Response normalization and caching
- Robust error handling

### 🕷️ Web Crawling (`tavily_crawl`)
Crawl websites with configurable depth and breadth for comprehensive content collection.

**Capabilities:**
- Graph-based traversal from a single start URL
- Configurable depth (1-3 levels) and breadth limits
- Domain-aware crawling with external link control
- Path and domain filtering (include/exclude)
- Natural language instructions for guided crawling
- Multiple output formats (markdown/text)
- Category-based filtering

## Installation

### Prerequisites
- Python 3.10 or higher
- Tavily API key

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd tavily
   ```

2. **Install dependencies:**

   **Option A: Using pip with editable install (recommended):**
   ```bash
   pip install -e .
   ```

   **Option B: Using uv (modern Python package manager):**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

## Configuration

The server uses environment variables for configuration:

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

## Usage

### Running the Server

Start the MCP server using the MCP dev command:
```bash
mcp dev server.py
```

The server runs on stdio and is compatible with MCP clients.

### Tool Descriptions

#### `tavily_search`
Search the web for a query and return summarized results. Use when you need current information or reputable sources.

**Parameters:**
- `query` (str): Search query text
- `search_depth` (str): "basic" or "advanced"
- `max_results` (int): 1-10 results
- `include_answer` (bool): Include synthesized answer
- `include_raw_content` (bool): Include raw content snippets
- `days` (int, optional): Freshness filter (0-365)
- `topic` (str, optional): Topic focus

**Returns:** SearchResponse with answer, results, response time, and auto parameters.

#### `tavily_extract`
Extract the primary content from one or more URLs. Use when you already know the URL(s) and need cleaned text and optional images.

**Parameters:**
- `urls` (str or List[str]): URL(s) to extract from
- `include_images` (bool): Include images in results

**Returns:** ExtractResponse with extracted content and optional images.

#### `tavily_crawl`
Crawl from a single start URL up to max_depth/max_breadth/limit, returning extracted pages. Use for site exploration and content collection.

**Parameters:**
- `url` (str): Root URL to begin crawl
- `max_depth` (int): Crawl depth (1-3)
- `max_breadth` (int): Links per level (≥1)
- `limit` (int): Maximum pages (1-500)
- `instructions` (str, optional): Natural language guidance
- `select_paths` (List[str], optional): Include path patterns
- `select_domains` (List[str], optional): Include domain patterns
- `exclude_paths` (List[str], optional): Exclude path patterns
- `exclude_domains` (List[str], optional): Exclude domain patterns
- `allow_external` (bool): Include external domains
- `include_images` (bool): Include images in results
- `categories` (List[str], optional): Content categories
- `extract_depth` (str): "basic" or "advanced"
- `format` (str): "markdown" or "text"
- `include_favicon` (bool): Include favicon URLs

**Returns:** CrawlResponse with crawled pages and metadata.

## Error Handling

The server provides standardized error messages for different scenarios:

- `ERR_UNAUTHORIZED`: Check TAVILY_API_KEY
- `ERR_RATE_LIMIT`: Rate limited, retry later
- `ERR_UPSTREAM_<status>`: Upstream API errors with context
- `ERR_BAD_REQUEST`: Invalid parameters
- `ERR_PAYMENT_REQUIRED`: Billing or quota issues

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
└── mcp_venv/             # Virtual environment
```

### Key Components

#### HTTP Client (`tools/client.py`)
- Centralized client factory with consistent configuration
- Authentication via TAVILY_API_KEY
- Configurable timeouts and retry logic
- Request ID tracking for debugging

#### Data Models (`tools/types.py`)
- Pydantic models for type safety
- Flexible field mapping for API compatibility
- Response validation and normalization

#### Error Handling (`tools/errors.py`)
- Standardized error messages for HTTP status codes
- AI-friendly error hints for debugging
- Response body snippets for context

## Dependencies

- `mcp[cli]>=1.2.0`: MCP Python SDK
- `httpx>=0.27.0`: HTTP client
- `pydantic>=2.6.0`: Data validation
- `python-dotenv>=1.0.1`: Environment variable loading
- `tenacity>=8.2.3`: Retry logic

## Development

### Running Tests
```bash
pytest
```

### Code Quality
The project follows Python best practices with:
- Type hints throughout
- Comprehensive error handling
- Logging for debugging
- Caching for performance
- Rate limiting and concurrency control

## License

This project is part of the Klavis AI ecosystem and follows the same licensing terms.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues related to:
- **Tavily API**: Contact Tavily support
- **MCP Integration**: Check MCP documentation
- **Klavis AI**: Contact Klavis AI support
- **This Project**: Open an issue on GitHub

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
