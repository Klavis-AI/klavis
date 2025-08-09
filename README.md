# Klavis MCP Multi-Tool (Overview)

This repo contains a focused Model Context Protocol (MCP) server that exposes a small, reliable set of tools for AI agents:
- generate_image (Replicate)
- generate_voice (ElevenLabs)
- search_web (SerpAPI)
- search_tavily (Tavily)
- summarize_webpage (Tavily)

The canonical implementation lives in `mcp_servers/replicate-multi-tool/`.

## Quick start
- Go to the server folder:
  ```bash
  cd mcp_servers/replicate-multi-tool
  ```
- Copy env template and add your keys:
  ```bash
  cp .env.example .env
  ```
- Install deps and run locally:
  ```bash
  pip install -r requirements.txt
  python3 mcp_server_focused.py
  ```

## Use in IDEs
- Cursor: Add an MCP server with `command: python3`, `args: ["mcp_server_focused.py"]`, `workingDirectory: server folder`.
- Claude Desktop: Add a server with the same command/args; ensure `.env` is set in the server folder.

## Docker / Compose (optional)
From `mcp_servers/replicate-multi-tool`:
```bash
# Docker
docker build -t klavis-mcp-replicate .
docker run --rm -it --env-file .env klavis-mcp-replicate

# Compose
docker compose up --build
```

## API keys
- Replicate: `https://replicate.com/account/api-tokens`
- ElevenLabs: `https://elevenlabs.io/app/settings/api-keys`
- SerpAPI: `https://serpapi.com/manage-api-key`
- Tavily: `https://app.tavily.com/sign-in`

## Project structure
```
.
└── mcp_servers/
    └── replicate-multi-tool/
        ├── mcp_server_focused.py
        ├── tools/
        ├── requirements.txt
        ├── .env.example
        ├── Dockerfile
        ├── .dockerignore
        ├── docker-compose.yml
        ├── Makefile
        ├── smoke_test.sh
        └── README.md
```

For the full, detailed guide (installation, configuration, IDE setup, JSON-RPC examples, testing, and troubleshooting), see:
- `mcp_servers/replicate-multi-tool/README.md`
