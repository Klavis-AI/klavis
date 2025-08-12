# Exa AI-Powered Search MCP Server

A high-quality Model Context Protocol (MCP) server that provides AI-powered web search capabilities through Exa's sophisticated search engine. This server exposes Exa's full suite of search tools, enabling AI agents to perform semantic search, content retrieval, similarity finding, direct question answering, and comprehensive research.

## Purpose

This MCP server acts as an intelligent bridge between AI agents and Exa's advanced web search capabilities. It transforms natural language queries into powerful search operations, making web research and content discovery seamless for AI assistants.

## Key Features

- **AI-Powered Semantic Search**: Neural search that understands meaning and context
- **Content Retrieval**: Clean, parsed HTML content from search results  
- **Similarity Discovery**: Find pages similar to a given URL
- **Direct Q&A**: Get focused answers with source citations
- **Comprehensive Research**: Structured multi-source analysis
- **Advanced Filtering**: Domain, date, and content-based filtering

---

## Installation and Setup

### Prerequisites

- **Python 3.11 or higher**
- **Exa API Key**: Sign up at [exa.ai](https://exa.ai) to get your API key

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Acquire and Configure API Credentials

1. **Get Your Exa API Key**:
   - Visit [exa.ai](https://exa.ai)
   - Sign up for an account
   - Navigate to your API settings
   - Copy your API key

2. **Configure Environment Variables**:

   **Option A: Environment Variables (Recommended)**
```bash
export EXA_API_KEY="your_exa_api_key_here"
export EXA_MCP_SERVER_PORT=5001  # Optional, defaults to 5001
```

   **Option B: .env File**
   Create a `.env` file in the project root:
   ```
   EXA_API_KEY=your_exa_api_key_here
   EXA_MCP_SERVER_PORT=5001
   ```

   **Option C: Runtime Authentication**
   You can also pass the API key via the `x-auth-token` header when making requests.

### Step 3: Run the Server

```bash
python server.py
```

The server will start on port 5001 (or your configured port) with dual transport support:
- **SSE Endpoint**: `http://localhost:5001/sse`
- **StreamableHTTP Endpoint**: `http://localhost:5001/mcp`

### Docker Setup (Alternative)

1. **Build the container**:
```bash
docker build -t exa-mcp-server .
```

2. **Run with environment variables**:
```bash
docker run -p 5001:5001 -e EXA_API_KEY="your_api_key" exa-mcp-server
```

---

## Available Tools

### `exa_search` - Web Search
Search the web for content using AI-powered semantic search or traditional keyword search.

**When to use**: Finding web pages, articles, or content related to a topic
**Returns**: Search results with URLs, titles, scores, and optional content text

**Required Parameters**:
- `query` (string): The search query

**Optional Parameters**:
- `num_results` (integer): Number of results (max 1000, default 10)
- `type` (string): "neural" (default) or "keyword" search
- `include_domains` (array): Domains to include
- `exclude_domains` (array): Domains to exclude
- `start_crawl_date` (string): Start date filter (YYYY-MM-DD)
- `end_crawl_date` (string): End date filter (YYYY-MM-DD)
- `start_published_date` (string): Published start date (YYYY-MM-DD)
- `end_published_date` (string): Published end date (YYYY-MM-DD)
- `use_autoprompt` (boolean): Use query optimization (default true)
- `category` (string): Category filter
- `include_text` (array): Required text patterns
- `exclude_text` (array): Excluded text patterns

### `exa_get_contents` - Content Retrieval
Get the full text content of web pages using their Exa search result IDs.

**When to use**: After performing a search to read full content of specific results
**Returns**: Clean, parsed content with optional highlighting and summarization

**Required Parameters**:
- `ids` (array): List of Exa result IDs

**Optional Parameters**:
- `text` (boolean): Include text content (default true)
- `highlights` (object): Highlighting options with query and num_sentences
- `summary` (object): Summary options with query

### `exa_find_similar` - Similarity Discovery
Discover web pages similar in meaning and content to a given URL.

**When to use**: Finding related articles or expanding research around a specific source
**Returns**: Semantically similar pages with relevance scores

**Required Parameters**:
- `url` (string): The URL to find similar pages for

**Optional Parameters**:
- Same filtering options as `exa_search`
- `exclude_source_domain` (boolean): Exclude source domain (default true)

### `exa_answer` - Direct Q&A
Get a direct answer to a specific question by searching and analyzing web sources.

**When to use**: Need focused answers to specific questions rather than general search results
**Returns**: Structured response with answer and source citations

**Required Parameters**:
- `query` (string): The question to answer

**Optional Parameters**:
- Same filtering options as `exa_search`

### `exa_research` - Comprehensive Research
Conduct comprehensive research on a topic with multiple sources and structured analysis.

**When to use**: In-depth research projects requiring multiple high-quality sources
**Returns**: Structured results with detailed content, citations, and analysis

**Required Parameters**:
- `query` (string): The research topic

**Optional Parameters**:
- Same parameters as `exa_search`

---

## Integration with MCP Clients

### Claude Desktop / Cursor IDE

Add this configuration to your Claude Desktop/ Cursor settings:

```json
{
  "mcpServers": {
    "exa-search": {
      "command": "python",
      "args": ["path/to/exa/server.py"],
      "env": {
        "EXA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Other MCP Clients

The server supports both SSE and StreamableHTTP transports, making it compatible with any MCP client. Use the appropriate endpoint based on your client's capabilities.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EXA_API_KEY` | Yes | None | Your Exa API key from exa.ai |
| `EXA_MCP_SERVER_PORT` | No | 5001 | Port for the MCP server |

---

## Error Handling

The server provides robust error handling with clear, actionable error messages:

- **Authentication Errors**: Clear guidance when API keys are missing or invalid
- **API Limit Errors**: Informative messages about rate limiting
- **Network Errors**: Helpful context for connectivity issues
- **Validation Errors**: Specific feedback on parameter issues

All errors are logged and returned in a format that AI agents can understand and potentially act upon.

---

## Testing and Validation

### Basic Connectivity Test

```bash
# Test server is running
curl http://localhost:5001/mcp

# Test with SSE
curl http://localhost:5001/sse
```

### Tool Testing with Natural Language

The server has been tested with these natural language queries to validate tool triggering:

**For exa_search**:
- "Search for recent developments in quantum computing"
- "Find articles about sustainable energy solutions"
- "Look up information on machine learning trends"

**For exa_get_contents**:
- "Get the full content of these search results"
- "Read the complete text from this article"
- "Retrieve the content from these URLs"

**For exa_find_similar**:
- "Find pages similar to this research article"
- "Discover related content to this blog post"
- "What other articles are like this one?"

**For exa_answer**:
- "What are the main benefits of renewable energy?"
- "How does machine learning improve healthcare?"
- "Explain the impact of climate change on agriculture"

**For exa_research**:
- "Research the current state of artificial intelligence in education"
- "Conduct comprehensive analysis on cryptocurrency adoption"
- "Investigate trends in remote work technologies"

---

## Contributing

When contributing to this MCP server:

1. **Follow Atomic Design**: Each tool should perform one specific job
2. **Clear Descriptions**: Tool descriptions must be AI-friendly and unambiguous
3. **Robust Error Handling**: Provide clear, actionable error messages
4. **Test Thoroughly**: Validate with multiple AI clients and natural language queries
5. **Document Changes**: Update README and maintain comprehensive documentation

---

## Security Notes

- API keys are handled securely through environment variables
- The server supports both environment-based and header-based authentication
- No sensitive information is logged in production mode
- All network requests use secure HTTPS connections to Exa's API

---

## Troubleshooting

**Server won't start**:
- Verify Python 3.11+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure port 5001 is available

**Authentication errors**:
- Verify your Exa API key is correct and active
- Check environment variable spelling: `EXA_API_KEY`
- Confirm your Exa account has sufficient API credits

**No search results**:
- Try different search queries
- Check domain filters aren't too restrictive
- Verify date filters are reasonable

**Connection issues**:
- Confirm firewall settings allow the configured port
- Test with curl commands above
- Check server logs for detailed error information

---

## License

This project follows the Klavis AI open-source licensing terms.
