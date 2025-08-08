# MCP Multi-Tool Server

**Author:** Prabhu Kiran Avula

## 📌 Purpose

This MCP (Model Context Protocol) server integrates **multiple AI-powered tools** into a single, easy-to-use API endpoint.  
It allows you to quickly perform **web searches**, **AI image generation**, **text-to-speech conversion**, and **research summarization** by connecting to multiple third-party APIs.

Currently, the server supports:

- **Replicate** – AI model inference for image generation and other tasks
- **ElevenLabs** – Natural-sounding text-to-speech conversion
- **SerpAPI** – Google Search API for structured search results
- **Tavily** – AI-powered web search and summarization

## 🛠️ Available Tools

This MCP server provides access to **40 total tools**:

- **35 Replicate AI Models** – Various AI models for image generation, text processing, and other AI tasks
- **5 Custom Tools** – Custom integrations for specific use cases

> **Note:** The code files contain many more tools, but due to Cursor's limit of 40 tools, only 5 custom tools could be implemented. The remaining tools are available in the codebase but not currently active in this deployment.

📄 **Project Documentation:** For detailed implementation report, output screenshots, and access to the official shared Google Drive folder with output files, see the [MCP Implementation Doc PDF](./MCP_Implementation_Doc.pdf).

---

## 🚀 Usage

This project provides MCP (Model Context Protocol) integrations for **Cursor** and **Claude Desktop**. The tools are designed to be used within these AI development environments.

### Available MCP Tools

**Replicate Integration (35 Tools):**
- Image generation with various AI models
- Model management and predictions
- Text-to-image and other AI tasks

**Focused Tools Server (5 Essential Tools):**
- **generate_voice**: Generate speech from text using ElevenLabs
- **search_web**: Search the web using SerpAPI  
- **search_tavily**: Advanced web search using Tavily
- **summarize_webpage**: Summarize webpages using Tavily
- **generate_image**: Generate images using Replicate

### Integration Setup

1. **For Cursor**: Configure the MCP server in your Cursor settings
2. **For Claude Desktop**: Add the MCP server to your Claude Desktop configuration
3. **Total Tools**: 40 tools (35 Replicate + 5 custom tools) optimized for performance

> **Note:** The `main.py` file contains setup information and print statements. All functionality is accessed through MCP tools within Cursor or Claude Desktop.

---

## 🔑 API Credentials Setup

This project requires API keys for each integrated service. Follow the links below to obtain your API keys:

### Required API Keys

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

> ⚠️ **Security Note:** Keep your `.env` file private and **never commit it** to version control.

---

## 🛠️ Detailed Setup Instructions

### Option 1: Direct Integration (Recommended)

**For Cursor:**
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

**For Claude Desktop:**
1. Open Claude Desktop settings
2. Go to "MCP Servers" section
3. Add server configuration pointing to `mcp_server_focused.py`
4. Configure environment variables in the settings

### Option 2: Personal Integration Tools

**Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 2: Configure Environment**
```bash
cp env_template.txt .env
# Edit .env with your API keys
```

**Step 3: Test Individual Tools**
```bash
python test_custom_tools.py
```

**Step 4: Integration Setup**

**For Cursor:**
1. Install the [MCP Extension](https://marketplace.visualstudio.com/items?itemName=modelcontextprotocol.mcp)
2. Configure in settings, mcp.json:
   ```json
   {
     "mcp.servers": {
       "replicate-mcp": {
         "command": "python",
         "args": ["mcp_server_focused.py"],
         "env": {
           "REPLICATE_API_TOKEN": "${env:REPLICATE_API_TOKEN}",
           "ELEVENLABS_API_KEY": "${env:ELEVENLABS_API_KEY}",
           "SERPAPI_API_KEY": "${env:SERPAPI_API_KEY}",
           "TAVILY_API_KEY": "${env:TAVILY_API_KEY}"
         }
       }
     }
   }
   ```

**For Claude Desktop:**
1. Download Claude Desktop from [Anthropic](https://claude.ai/download)
2. Open preferences and navigate to "MCP Servers"
3. Add server configuration with your API keys

### Verification Steps

1. **Test Replicate Integration:**
   - Try generating an image using the `generate_image` tool
   - Verify Replicate API connectivity

2. **Test Voice Generation:**
   - Use the `generate_voice` tool with sample text
   - Check ElevenLabs API connection

3. **Test Web Search:**
   - Try both `search_web` and `search_tavily` tools
   - Verify SerpAPI and Tavily connectivity

4. **Test Summarization:**
   - Use `summarize_webpage` with a test URL
   - Confirm Tavily summarization works

### Troubleshooting

**Common Issues:**
- **API Key Errors**: Verify all API keys are correctly set in `.env`
- **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Connection Issues**: Check internet connectivity and API service status
- **MCP Server Not Found**: Verify the server configuration in Cursor/Claude Desktop settings

**Useful Links:**
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Cursor MCP Extension](https://marketplace.visualstudio.com/items?itemName=modelcontextprotocol.mcp)
- [Claude Desktop Documentation](https://docs.anthropic.com/claude/docs/claude-desktop)
- [Replicate API Documentation](https://replicate.com/docs)
- [ElevenLabs API Documentation](https://elevenlabs.io/docs)
- [SerpAPI Documentation](https://serpapi.com/docs)
- [Tavily API Documentation](https://tavily.com/docs)

---

## 📂 Project Structure

```
├── main.py                  # Setup file with MCP tool information and print statements
├── mcp_server_focused.py    # MCP server implementation for focused tools
├── tools/                   # All MCP tools
│   ├── elevenlabs_voice.py  # ElevenLabs TTS integration
│   ├── generate_image.py    # Replicate AI image generation
│   ├── serpapi_search.py    # SerpAPI search integration
│   ├── tavily_search.py     # Tavily search integration
├── test_custom_tools.py     # Tool usage tests
├── requirements.txt         # Python dependencies
├── env_template.txt         # API key template
├── LICENSE.txt              # License (MIT)
├── MCP_Implementation_Doc.pdf # Project documentation with screenshots and output files
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.txt](./LICENSE.txt) file for details.

---

## 📄 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 Acknowledgments

- [Klavis AI](https://github.com/Klavis-AI/klavis) - Open source MCP integration platform
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Cursor](https://cursor.sh/)
- [Claude Desktop](https://claude.ai/download)
- [Replicate](https://replicate.com/)
- [ElevenLabs](https://elevenlabs.io/)
- [SerpAPI](https://serpapi.com/)
- [Tavily](https://tavily.com/)
