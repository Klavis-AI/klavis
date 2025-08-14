# Exa MCP Server

**AI-Powered Search Integration for Model Context Protocol**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

## 🎯 Purpose

The Exa MCP Server transforms how AI agents discover and access information by providing intelligent, semantic search capabilities through the Model Context Protocol. Unlike traditional keyword-based search, this server leverages Exa's neural search technology to understand context, meaning, and intent, enabling AI agents to find precisely relevant information across the web.

**Key Value Propositions:**
- **Semantic Understanding**: Goes beyond keywords to understand what users actually need
- **Specialized Search Types**: Academic papers, recent content, and similarity-based discovery
- **AI-Optimized Results**: Structured outputs designed for AI consumption and reasoning
- **Atomic Tool Design**: Five focused tools that can be combined for complex research workflows

## 🔧 Architecture & Tools

This server implements five atomic, specialized tools that follow MCP best practices:

### 🔍 `search_web`
**Purpose**: Perform neural semantic web search across the entire internet
- **When to use**: General information discovery, research, fact-finding
- **AI Advantage**: Understands context and intent, not just keywords
- **Output**: Ranked results with relevance scoring and rich metadata

### 🔗 `find_similar_content`
**Purpose**: Discover content semantically similar to a given URL
- **When to use**: Content discovery, competitive analysis, finding related sources
- **AI Advantage**: Uses embeddings to find conceptually related content
- **Output**: Similar pages with similarity scores and analysis

### 📅 `search_recent_content`
**Purpose**: Time-filtered search for fresh, up-to-date information
- **When to use**: News, current events, recent developments
- **AI Advantage**: Temporal relevance combined with semantic understanding
- **Output**: Recent content with publication dates and freshness indicators

### 🎓 `search_academic_content`
**Purpose**: Scholarly and research-focused content discovery
- **When to use**: Academic research, peer-reviewed sources, authoritative information
- **AI Advantage**: Filters for credible, scholarly sources automatically
- **Output**: Academic papers, research publications, and educational content

### 📄 `get_page_contents`
**Purpose**: Extract and analyze full content from search results
- **When to use**: Deep content analysis, full-text research, content summarization
- **AI Advantage**: Provides structured content with AI-generated summaries
- **Output**: Full text, key highlights, and intelligent summaries

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.8 or higher
- **Exa API Access**: Valid API key from [Exa](https://exa.ai/)
- **MCP Client**: Claude Desktop, Cursor, or any MCP-compatible client

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Klavis-AI/klavis.git
   cd klavis/servers/exa
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   ```bash
   # Create .env file or set environment variable
   export EXA_API_KEY="your-exa-api-key-here"
   ```

### API Key Configuration

#### Obtaining Your Exa API Key

1. **Visit** [Exa.ai](https://exa.ai/)
2. **Sign up** for an account or log in
3. **Navigate** to your dashboard
4. **Generate** a new API key
5. **Copy** the key securely

#### Setting the Environment Variable

**Option 1: Environment Variable (Recommended)**
```bash
# Windows (Command Prompt)
set EXA_API_KEY=your-exa-api-key-here

# Windows (PowerShell)
$env:EXA_API_KEY="your-exa-api-key-here"

# macOS/Linux
export EXA_API_KEY="your-exa-api-key-here"
```

**Option 2: .env File**
Create a `.env` file in the project root:
```
EXA_API_KEY=your-exa-api-key-here
```

**Option 3: MCP Client Configuration**
Add to your MCP client config (e.g., Claude Desktop):
```json
{
  "mcpServers": {
    "exa-search": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/exa-mcp-server",
      "env": {
        "EXA_API_KEY": "your-exa-api-key-here"
      }
    }
  }
}
```

## 🎮 Running the Server

### Standalone Mode (for testing)
```bash
python -m src.main
```

### With Claude Desktop

1. **Add to Claude Desktop Configuration**
   
   Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

   ```json
   {
     "mcpServers": {
       "exa-search": {
         "command": "python",
         "args": ["-m", "src.main"],
         "cwd": "/absolute/path/to/exa-mcp-server",
         "env": {
           "EXA_API_KEY": "your-exa-api-key-here"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Test the Connection**
   
   In Claude Desktop, try: *"Search for recent AI research papers on transformer architectures"*

### With Other MCP Clients

The server is compatible with any MCP client. Refer to your client's documentation for configuration steps.

## 💡 Usage Examples

### Basic Web Search
```
User: "Find information about quantum computing applications in cryptography"
AI: Uses search_web tool → Returns relevant articles and research
```

### Academic Research
```
User: "I need peer-reviewed papers on machine learning interpretability"
AI: Uses search_academic_content tool → Returns scholarly articles and publications
```

### Content Discovery
```
User: "Find articles similar to this Nature paper: https://nature.com/articles/..."
AI: Uses find_similar_content tool → Returns related research and articles
```

### Recent Developments
```
User: "What are the latest developments in autonomous vehicles this month?"
AI: Uses search_recent_content tool → Returns recent news and updates
```

### Deep Content Analysis
```
User: "Get the full content and summary from these search results: result_id_1, result_id_2"
AI: Uses get_page_contents tool → Returns full text with AI-generated summaries
```

## 🏗️ Development & Architecture

### Project Structure
```
exa-mcp-server/
├── examples/
│   ├── proof_of_correctness/
│   │   ├── 1 - Intro.mp4
│   │   ├── 2 - AI Web Search.mp4
│   │   ├── 3 - Find Similar Content.mp4
│   │   ├── 4 - Recent Content Search.mp4
│   │   ├── 5 - Academic Search.mp4
│   │   ├── 6 - Extract Content.mp4
│   │   └──
│   └── demo_queries.py
├── src/
│   ├── __pycache__/
│   ├── client/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── exa_client.py
│   ├── models/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── tools/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── content.py
│   │   ├── discovery.py
│   │   └── search.py
│   ├── utils/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── formatters.py
│   │   └── logging.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_integration.py
│   └── test_tools.py
├── .env.example
├── demo.html
├── direct_query_test.py
├── README.md
├── requirements.txt
├── run_server.py
├── setup.py
└── web_bridge.py
```

### Key Design Principles

1. **Atomic Tools**: Each tool performs one specific function exceptionally well
2. **Clear Interfaces**: Tool names and descriptions are optimized for AI understanding
3. **Robust Error Handling**: Graceful handling of API errors, rate limits, and edge cases
4. **Structured Responses**: All outputs are formatted for optimal AI consumption
5. **Extensible Architecture**: Easy to add new tools and capabilities

### Error Handling

The server implements comprehensive error handling:

- **API Rate Limits**: Automatic retry with exponential backoff
- **Invalid API Keys**: Clear error messages with troubleshooting guidance
- **Network Issues**: Graceful degradation and informative error responses
- **Malformed Requests**: Input validation with helpful correction suggestions

## 🧪 Running and Testing
### Using webpage UI and testing
```bash
# Set Exa API Key
$env:EXA_API_KEY="your-exa-api-key-here"

# Run the server and web bridge
python web_bridge.py

# Open localhost 8000
http://localhost:8000/
```

### Running Tests
```bash
# Run all tests
python direct_query_test.py

# Run Integration Test
python ./tests/test_integration.py
```

### Manual Testing
```bash
# Test server startup
python -m src.main

# Test individual tool (in another terminal)
echo '{"method":"tools/call","params":{"name":"search_web","arguments":{"query":"test"}}}' | python -m src.main
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `EXA_API_KEY` | Your Exa API key | Yes | - |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `MAX_RESULTS` | Default max results per search | No | `10` |
| `TIMEOUT` | API request timeout (seconds) | No | `30` |

### Advanced Configuration

Create a `config.yaml` file for advanced settings:

```yaml
exa:
  api_key: ${EXA_API_KEY}
  base_url: "https://api.exa.ai"
  timeout: 30
  max_retries: 3

server:
  name: "exa-mcp-server"
  version: "1.0.0"
  log_level: "INFO"

tools:
  search_web:
    default_num_results: 10
    max_num_results: 100
  search_academic_content:
    academic_domains: 
      - "arxiv.org"
      - "pubmed.ncbi.nlm.nih.gov"
      - "ieee.org"
```

## 🚨 Troubleshooting

### Common Issues

#### "No module named 'exa'"
```bash
pip install exa-py
```

#### "Authentication failed"
- Verify your Exa API key is correct
- Ensure the environment variable is set
- Check your Exa account has sufficient credits

#### "ModuleNotFoundError: No module named 'src'"
- Ensure you're running from the project root
- Verify all `__init__.py` files exist
- Check your Python path configuration

#### "Server disconnected" in Claude Desktop
- Verify the absolute path in your config
- Check the environment variable is set correctly
- Ensure Python is in your system PATH

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.main
```

### Getting Help

1. **Check the logs** for detailed error information
2. **Verify your API key** has sufficient credits and permissions
3. **Test the connection** manually using the provided test scripts
4. **Review the MCP protocol** documentation for client-specific issues

## 📊 Performance & Limits

### API Rate Limits
- Exa API: 1000 requests/month (free tier), check your plan for limits
- Server implements automatic retry with exponential backoff
- Rate limit errors are handled gracefully with informative messages

### Performance Characteristics
- **Typical Response Time**: 200-800ms per search
- **Concurrent Requests**: Handled asynchronously for better performance
- **Memory Usage**: ~50MB base + ~10MB per concurrent request
- **Caching**: Response caching available for repeated queries

### Scalability Considerations
- Stateless design allows horizontal scaling
- Database integration available for result caching
- Monitoring hooks for observability in production

## 🔒 Security & Privacy

### API Key Security
- API keys should never be committed to version control
- Use environment variables or secure configuration management
- Rotate API keys regularly following security best practices

### Data Privacy
- No user data is stored by the server
- All requests are proxied directly to Exa's API
- Server logs can be configured to exclude sensitive information

### Network Security
- All API communications use HTTPS/TLS encryption
- Input validation prevents injection attacks
- Rate limiting protects against abuse

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Follow the coding standards** established in the project
4. **Update documentation** for any API changes
5. **Submit a pull request** with a clear description


## 🙏 Acknowledgments

- **Exa Team** for providing the powerful neural search API
- **Anthropic** for developing the Model Context Protocol
- **Klavis AI** for the opportunity to contribute to the ecosystem

## 📞 Support

For questions, issues, or contributions:
- **GitHub Issues**: [Create an issue](https://github.com/Klavis-AI/klavis/issues)
- **Documentation**: [MCP Protocol Docs](https://modelcontextprotocol.io/)
- **Exa API Docs**: [Exa Documentation](https://docs.exa.ai/)

---

**Built with ❤️ for the AI community**