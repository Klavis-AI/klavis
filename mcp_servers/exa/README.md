# 🔍 Exa AI-Powered Search MCP Server

An advanced Model Context Protocol (MCP) server that provides AI-powered web search capabilities through Exa's sophisticated search engine. This server exposes Exa's full suite of search tools, enabling AI agents to perform semantic search, content retrieval, similarity finding, direct question answering, and comprehensive research.

## 🌟 Features

### Core Search Capabilities
- **Neural Search**: AI-powered semantic search that understands meaning and context
- **Keyword Search**: Traditional keyword-based search for precise term matching
- **Content Retrieval**: Clean, parsed HTML content from search results
- **Similarity Finding**: Discover pages similar in meaning to a given URL
- **Direct Answers**: Get AI-generated answers with source citations
- **Research Mode**: Comprehensive research with structured results

### Advanced Filtering
- **Domain Control**: Include or exclude specific domains
- **Date Filtering**: Filter by crawl date or published date
- **Content Filtering**: Include or exclude specific text patterns
- **Category Filtering**: Focus on specific content categories
- **Autoprompt**: Automatic query optimization

---

## 🛠️ Available Tools

### `exa_search`
**AI Prompt Words**: "search for", "find information about", "look up"

Performs an Exa search query using neural embeddings or keyword search.

**Parameters:**
- `query` (str, required): The search query to find relevant web content
- `num_results` (int): Number of results to return (max 1000, default 10)
- `include_domains` (array): List of domains to include in search results
- `exclude_domains` (array): List of domains to exclude from search results
- `start_crawl_date` (str): Start date for crawl date filter (YYYY-MM-DD)
- `end_crawl_date` (str): End date for crawl date filter (YYYY-MM-DD)
- `start_published_date` (str): Start date for published date filter (YYYY-MM-DD)
- `end_published_date` (str): End date for published date filter (YYYY-MM-DD)
- `use_autoprompt` (bool): Whether to use Exa's autoprompt feature (default true)
- `type` (str): Search type - 'neural' or 'keyword' (default 'neural')
- `category` (str): Category filter for results
- `include_text` (array): Text patterns that must be included in results
- `exclude_text` (array): Text patterns to exclude from results

**Example Usage:**
```javascript
{
  "query": "latest developments in quantum computing",
  "num_results": 15,
  "type": "neural",
  "include_domains": ["arxiv.org", "nature.com"],
  "start_published_date": "2024-01-01"
}
```

---

### `exa_get_contents`
**AI Prompt Words**: "get content", "read full text", "retrieve page content"

Retrieves clean, parsed HTML content for specific Exa search result IDs.

**Parameters:**
- `ids` (array, required): List of Exa result IDs to get contents for
- `text` (bool): Whether to include text content (default true)
- `highlights` (object): Highlighting options with query and num_sentences
- `summary` (object): Summary options with query for generating summaries

**Example Usage:**
```javascript
{
  "ids": ["result_id_1", "result_id_2"],
  "text": true,
  "highlights": {
    "query": "quantum computing",
    "num_sentences": 3
  }
}
```

---

### `exa_find_similar`
**AI Prompt Words**: "find similar pages", "discover related content", "what's similar to"

Finds web pages that are similar in meaning to a given URL.

**Parameters:**
- `url` (str, required): The URL to find similar pages for
- `num_results` (int): Number of similar results to return (max 1000, default 10)
- `exclude_source_domain` (bool): Whether to exclude the source domain (default true)
- Additional filtering parameters same as exa_search

**Example Usage:**
```javascript
{
  "url": "https://example.com/article-about-ai",
  "num_results": 10,
  "exclude_source_domain": true,
  "include_domains": ["research.org", "university.edu"]
}
```

---

### `exa_answer`
**AI Prompt Words**: "answer the question", "what is", "explain", "define"

Gets a direct, AI-generated answer to a specific question using Exa's Answer API.

**Parameters:**
- `query` (str, required): The question to get a direct answer for
- All filtering parameters from exa_search apply

**Example Usage:**
```javascript
{
  "query": "What are the main applications of quantum computing?",
  "include_domains": ["scholar.google.com", "arxiv.org"],
  "type": "neural"
}
```

---

### `exa_research`
**AI Prompt Words**: "research", "comprehensive analysis", "in-depth study", "investigate"

Conducts comprehensive, in-depth web research on a topic with structured results and citations.

**Parameters:**
- `query` (str, required): The research topic or question to investigate comprehensively
- All parameters from exa_search apply

**Example Usage:**
```javascript
{
  "query": "Impact of artificial intelligence on healthcare diagnostics",
  "num_results": 20,
  "include_domains": ["pubmed.ncbi.nlm.nih.gov", "nature.com", "nejm.org"],
  "start_published_date": "2023-01-01"
}
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Exa API key (get one at [exa.ai](https://exa.ai))

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
export EXA_API_KEY="your_exa_api_key_here"
export EXA_MCP_SERVER_PORT=5001  # Optional, defaults to 5001
```

3. **Run the server:**
```bash
python server.py
```

### Docker Setup

1. **Build the container:**
```bash
docker build -t exa-mcp-server .
```

2. **Run with environment variables:**
```bash
docker run -p 5001:5001 -e EXA_API_KEY="your_api_key" exa-mcp-server
```

---

## 🔧 Configuration

### Environment Variables
- `EXA_API_KEY`: Your Exa API key (required)
- `EXA_MCP_SERVER_PORT`: Server port (default: 5001)
- Authentication can also be passed via `x-auth-token` header

### Server Endpoints
- **SSE**: `http://localhost:5001/sse`
- **StreamableHTTP**: `http://localhost:5001/mcp`

---

## 💡 Use Cases

### Content Discovery
Perfect for finding relevant articles, research papers, and web content based on semantic meaning rather than just keywords.

### Research & Analysis
Conduct comprehensive research on any topic with automatic source gathering and citation.

### Content Recommendation
Find similar content to existing articles or web pages for content curation and recommendation systems.

### Q&A Systems
Get direct answers to questions with proper source attribution for chatbots and knowledge systems.

### Competitive Intelligence
Research competitors, market trends, and industry developments with advanced filtering capabilities.

---

## 🔍 API Capabilities

The Exa API excels at:
- **Semantic Understanding**: Finds content by meaning, not just keywords
- **High-Quality Sources**: Filters for authoritative and relevant content  
- **Real-Time Data**: Access to recently crawled web content
- **Flexible Filtering**: Comprehensive options for domain, date, and content filtering
- **Content Analysis**: Automatic summarization and highlighting capabilities

---

## 🧪 Testing

Test the server with any MCP-compatible client:

### Claude Desktop
Configure in your Claude Desktop settings to connect to the local server.

### Cursor IDE
Add as a remote MCP server in your Cursor configuration.

### Custom Testing
Use the streamable HTTP client for direct API testing:
```bash
python -m mcp_clients.streamable_http_client http://localhost:5001/mcp
```

---

## 📚 Example Queries

**Research Query:**
> "Research the latest developments in renewable energy storage technologies"

**Semantic Search:**
> "Find articles about machine learning applications in medical diagnosis"

**Similarity Finding:**
> "Find content similar to this Nature article about climate change"

**Direct Answer:**
> "What are the key benefits of edge computing over cloud computing?"

---

## 🤝 Contributing

When contributing to this MCP server:

1. Ensure tool descriptions are clear and AI-friendly
2. Test with multiple AI clients
3. Document new features thoroughly
4. Follow the atomic tool design principle
5. Include proper error handling

---

## 📄 License

This project follows the Klavis AI open-source licensing terms.
