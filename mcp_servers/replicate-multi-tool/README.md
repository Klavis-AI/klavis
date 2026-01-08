# Replicate Multi‑Tool MCP Server

This server exposes a comprehensive set of MCP tools that combine Replicate models and curated integrations (web search, summarization, TTS) behind a single MCP endpoint, with dual transports (SSE and Streamable HTTP).

## Purpose
Provide AI agents with a unified, atomic toolset for:
- Image generation and upscaling (Replicate)
- Web search and webpage summarization (SerpAPI, Tavily)
- Text‑to‑speech voice synthesis (ElevenLabs)
- A catalog of additional MCP tools (text, audio, video, code, analysis) for expansion and prototyping

Tools are explicitly named, have clear JSON schemas, and return structured results.

## Tool catalog (server.py)
- Custom tools
  - `generate_voice_from_text`
  - `search_web_query`
  - `search_with_tavily`
  - `summarize_webpage`
  - `generate_image`
  - `image_upscale`
- Text generation
  - `llama_3_70b_instruct`, `gpt_4`, `claude_3_opus`, `claude_3_sonnet`
- Image generation
  - `sdxl`, `midjourney`
- Audio generation
  - `musicgen`
- Video generation
  - `video_generation`
- Code generation
  - `code_generation`
- Translation and summarization
  - `translation`, `text_summarization`
- NLP utilities
  - `sentiment_analysis`, `question_answering`, `language_detection`, `entity_recognition`, `text_classification`, `content_moderation`, `keyword_extraction`, `text_similarity`, `creative_writing`
- Code quality and docs
  - `code_review`, `api_documentation`, `test_generation`, `performance_analysis`, `security_analysis`, `dependency_analysis`, `code_formatting`, `error_handling`, `documentation_generation`

Note: Many catalog tools are wired with safe placeholder implementations intended for extension; the custom tools listed first are fully implemented today.

## Requirements
- Python 3.10+
- `pip` and virtualenv recommended

## Installation
```bash
cd mcp_servers/replicate-multi-tool
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Credentials and environment
Copy the provided example and fill in your keys. The tools auto‑load this file.

```bash
cp .env.example .env
```

Required variables and where to obtain them (also listed in `.env.example`):
- `REPLICATE_API_TOKEN` – get from `https://replicate.com/account/api-tokens`
- `ELEVENLABS_API_KEY` – get from `https://elevenlabs.io/app/settings/api-keys`
- `SERPAPI_API_KEY` – get from `https://serpapi.com/manage-api-key`
- `TAVILY_API_KEY` – get from `https://app.tavily.com/sign-in`
Do not commit real secrets to version control.

## How to run
Local (auto‑runs with Uvicorn if available):
```bash
python3 server.py
# Server will bind on 0.0.0.0:8000
```

Run with Uvicorn directly (optional):
```bash
uvicorn server:create_app --factory --host 0.0.0.0 --port 8000
```

Docker:
```bash
docker build -t klavis-mcp-replicate .
docker run --rm -it -p 8000:8000 --env-file .env klavis-mcp-replicate
```

## Transports and endpoints
- SSE transport: `GET /sse` and `POST /messages/` (MCP SSE protocol)
- Streamable HTTP transport: `POST /mcp` (MCP Streamable HTTP protocol)

Use an MCP‑compatible client to connect over either transport. For examples, see the `mcp-clients/` folder in this repository.

## Quick sanity checks (implemented tools)
- Voice synthesis
  - Ensure `ELEVENLABS_API_KEY` is set
  - Call MCP tool `generate_voice_from_text` with `{ text: "Hello world" }`
- Web search and summarize
  - Ensure `SERPAPI_API_KEY` and/or `TAVILY_API_KEY` are set
  - Call `search_web_query` or `search_with_tavily` / `summarize_webpage`
- Image generation
  - Ensure `REPLICATE_API_TOKEN` is set
  - Call `generate_image` with a descriptive prompt

## Proof of comprehensive testing (images)
Add screenshots are in the doc link below:

[Mandatory Proof of Correctness](https://docs.google.com/document/d/1cn-lpog6vaGT4M-Hnz4gW1BYM000Nu2F8K3vYmJ-VGU/edit?usp=sharing)
[Outputs Drive Folder](https://drive.google.com/drive/folders/11hVXcgoV0TOJJDfq9Fbab39IOWwtvCDz?usp=sharing)

These images should demonstrate successful calls and responses for each implemented tool and a full tools catalog listing.

## Notes
- The `.env` is loaded from the server root so tools work regardless of current working directory.
- Many catalog tools are scaffolded for rapid iteration; extend the placeholder wrappers in `server.py` or add concrete implementations in `tools/` as needed.

### Troubleshooting
- Tools do not appear in client
  - Ensure the server is running on port 8000 and reachable; check logs for initialization and tool registration.
  - Call the tools list endpoint via your MCP client to confirm registration.
- 401/403 or quota errors
  - Verify API keys: `REPLICATE_API_TOKEN`, `ELEVENLABS_API_KEY`, `SERPAPI_API_KEY`, `TAVILY_API_KEY` are set and valid.
  - Check provider dashboards for active subscriptions and rate limits.
- .env not loaded
  - The server loads `.env` from this folder; ensure it exists and has no extra file extensions.
  - Re‑start the server after changing environment variables.
- Replicate issues
  - Confirm `REPLICATE_API_TOKEN` and model availability; some models change slugs or require access.
- ElevenLabs issues
  - Confirm `ELEVENLABS_API_KEY` and `voice_id` validity; check /tmp write permissions for audio output.
- SerpAPI/Tavily issues
  - Validate key usage and result limits; for Tavily, `search_depth` must be `basic` or `advanced`.
- Port already in use
  - Choose a different port when launching with Uvicorn (e.g., `--port 8010`) or stop the conflicting process.
- Tool "not found"
  - Ensure the tool name matches exactly what `tools/list` returns and that the server has been restarted after edits.

### Helpful links
- Model Context Protocol overview: [modelcontextprotocol.dev](https://modelcontextprotocol.dev)
- MCP servers documentation (in this repo): [`docs/documentation/mcp-server/`](../../docs/documentation/mcp-server/)
- MCP clients documentation (in this repo): [`docs/documentation/mcp-client/`](../../docs/documentation/mcp-client/)
- Klavis SDK docs (in this repo): [`docs/documentation/sdk/`](../../docs/documentation/sdk/)
- AI platform integration guides (in this repo): [`docs/documentation/ai-platform-integration/`](../../docs/documentation/ai-platform-integration/)
- Cursor MCP setup: refer to Cursor documentation (search for "Cursor MCP")
- Claude Desktop MCP setup: refer to Claude Desktop documentation (search for "Claude Desktop MCP")
