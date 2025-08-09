# Klavis MCP Multi-Tool Server (Detailed Guide)

This MCP server provides a small, atomic toolset for AI agents:
- generate_image (Replicate)
- generate_voice (ElevenLabs)
- search_web (SerpAPI)
- search_tavily (Tavily)
- summarize_webpage (Tavily)

Tools are atomic, clearly named, and return structured results (success/error) per Klavis AI guidelines.

## Purpose
Enable fast integration of common AI actions (image generation, TTS, search, summarization) via a clean MCP interface suitable for Cursor, Claude Desktop, or direct JSON-RPC usage.

## Installation and Setup
1) Copy the env template and set credentials:
```bash
cp .env.example .env
```
2) Install dependencies:
```bash
pip install -r requirements.txt
```
3) Run locally (stdio / JSON-RPC):
```bash
python3 mcp_server_focused.py
```

## API credentials
Set the following in `.env` (this folder). The tools auto-load `.env`.
- `REPLICATE_API_TOKEN` – `https://replicate.com/account/api-tokens`
- `ELEVENLABS_API_KEY` – `https://elevenlabs.io/app/settings/api-keys`
- `SERPAPI_API_KEY` – `https://serpapi.com/manage-api-key`
- `TAVILY_API_KEY` – `https://app.tavily.com/sign-in`

Do not commit real secrets.

## Use with Cursor
Add an MCP server in Cursor settings:
```json
{
  "command": "python3",
  "args": ["mcp_server_focused.py"],
  "workingDirectory": "${workspaceRoot}"
}
```
- Start a new chat and use natural prompts; tools will be selected as needed.
- If tools don’t appear, verify Python deps and `.env`.

## Use with Claude Desktop
1) Preferences → MCP Servers → Add
- Command: `python3`
- Args: `mcp_server_focused.py`
- Working directory: this folder
2) Ensure `.env` is set; restart Claude Desktop if needed.

## Docker / Compose
```bash
# Docker
docker build -t klavis-mcp-replicate .
docker run --rm -it --env-file .env klavis-mcp-replicate

# Compose
docker compose up --build
```

## JSON-RPC examples
Initialize + list tools:
```bash
python3 mcp_server_focused.py << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
```
Call a tool:
```bash
python3 mcp_server_focused.py << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_image","arguments":{"prompt":"a scenic mountain at sunrise"}}}
EOF
```

## Makefile helpers
```bash
make run          # start server locally
make smoke        # initialize + list tools
make docker-build # build container
make docker-run   # run container with .env
make compose-up   # docker compose up --build
```

## Testing
- Smoke: `./smoke_test.sh` or `make smoke`
- Tool checks: `python3 test_custom_tools.py`

## Compliance (Klavis AI guidelines)
- Atomic tools, descriptive names, explicit inputs/outputs
- Clear, structured error returns (for self-correction)
- `.env.example` provided; `.env` auto-loaded; secrets ignored
- Dockerfile, .dockerignore, docker-compose for orchestration
- `tools/__init__.py` re-exports public API; stable imports
- README includes purpose, setup, credentials, run instructions, JSON-RPC, and testing
