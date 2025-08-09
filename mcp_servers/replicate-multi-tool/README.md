# Replicate Multi-Tool MCP Server

**Author:** Prabhu Kiran Avula  
**Interview Submission for Klavis AI**

## 🎯 Overview

This MCP (Model Context Protocol) server integrates **multiple AI-powered tools** into a single, easy-to-use API endpoint. It allows you to quickly perform **web searches**, **AI image generation**, **text-to-speech conversion**, and **research summarization** by connecting to multiple third-party APIs.

## 🛠️ Available Tools

This MCP server provides access to **40 total tools**:

- **35 Replicate AI Models** – Various AI models for image generation, text processing, and other AI tasks
- **5 Custom Tools** – Custom integrations for specific use cases

### Custom Tools:
- **generate_voice**: Generate speech from text using ElevenLabs
- **search_web**: Search the web using SerpAPI  
- **search_tavily**: Advanced web search using Tavily
- **summarize_webpage**: Summarize webpages using Tavily
- **generate_image**: Generate images using Replicate

## 🔑 API Credentials Setup

This project requires API keys for each integrated service:

| Service | API Key Link | Description |
|---------|-------------|-------------|
| **Replicate** | [Get API Token](https://replicate.com/account/api-tokens) | AI model inference for image generation and other tasks |
| **ElevenLabs** | [Get API Key](https://elevenlabs.io/app/settings/api-keys) | Natural-sounding text-to-speech conversion |
| **SerpAPI** | [Get API Key](https://serpapi.com/manage-api-key) | Google Search API for structured search results |
| **Tavily** | [Get API Key](https://app.tavily.com/sign-in) | AI-powered web search and summarization |

### Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp env_template.txt .env
   ```

2. **Edit `.env`** and fill in your API keys:
   ```env
   REPLICATE_API_TOKEN=your_replicate_token_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here
   SERPAPI_API_KEY=your_serpapi_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

## 🚀 Usage

### For Cursor:
1. Open Cursor settings (`Cmd/Ctrl + ,`)
2. Navigate to "Extensions" → "MCP"
3. Add new MCP server configuration:
   ```json
   {
     "command": "python",
     "args": ["-m", "mcp_server_focused"],
     "env": {
       "REPLICATE_API_TOKEN": "your_token",
       "ELEVENLABS_API_KEY": "your_key",
       "SERPAPI_API_KEY": "your_key",
       "TAVILY_API_KEY": "your_key"
     }
   }
   ```

### For Claude Desktop:
1. Open Claude Desktop settings
2. Go to "MCP Servers" section
3. Add server configuration pointing to `mcp_server_focused.py`
4. Configure environment variables in the settings

## 📂 Project Structure

```
mcp_servers/replicate-multi-tool/
├── mcp_server_focused.py    # MCP server implementation
├── tools/                   # All MCP tools
│   ├── elevenlabs_voice.py  # ElevenLabs TTS integration
│   ├── generate_image.py    # Replicate AI image generation
│   ├── serpapi_search.py    # SerpAPI search integration
│   ├── tavily_search.py     # Tavily search integration
├── test_custom_tools.py     # Tool usage tests
├── requirements.txt         # Python dependencies
├── env_template.txt         # API key template
└── README.md               # This documentation
```

## 🧪 Testing

Run the test suite to verify all tools are working:

```bash
python test_custom_tools.py
```

## 📄 License

This project is licensed under the MIT License.

## 🎯 Interview Submission Details

This implementation demonstrates:
- **MCP Protocol Compliance**: Full Model Context Protocol implementation
- **Multi-API Integration**: Seamless integration of 4 different APIs
- **Modular Architecture**: Clean separation of concerns
- **Production Ready**: Error handling, environment configuration, and testing
- **Comprehensive Documentation**: Professional-grade setup instructions

**Total Tools Implemented**: 40 (35 Replicate + 5 custom tools)

---

**Ready for review! 🚀**
