# Spotify MCP Server 🎵

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for controlling and querying Spotify via Claude or other MCP-compatible clients.  
This server exposes tools for **searching, playing, pausing, queueing, and fetching Spotify content** over HTTP.

---

## Features
-  **Search Spotify** (tracks, albums, artists, playlists)
-  **Play songs** by URI or resume playback
-  **Pause** current playback
-  **Skip** tracks
-  **Manage queue** (view / add tracks)
-  **Get detailed item info** (track, album, artist, playlist)
-  **Manage playlists** (get, add, remove, update details)
-  **HTTP MCP Orchestration** — fully compatible with Claude’s MCP client

---

## Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd mcp_servers/spotify
```

2. **Create a virtual environment (optional but recommended)**
```bash
uv venv
```

3. **Install dependencies**
```bash
uv pip install -e .
```

---

## Configuration

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_ACCESS_TOKEN=your_valid_access_token
```

> ⚠️ Never commit `.env` to version control.  
> For getting a Spotify access token, see [Spotify Developer Console](https://developer.spotify.com/console/).

---

## Running the Server

### Option 1 — Directly with `uv`
```bash
uv run spotify-mcp --port 5001
```

### Option 2 — Module Execution
```bash
python -m src.spotify_mcp.server --port 5001
```

When running, you’ll see:
```
[INFO] Starting Spotify MCP server on port 5001
[INFO]   - SSE endpoint: http://localhost:5001/sse
[INFO]   - StreamableHTTP endpoint: http://localhost:5001/mcp
```

---

## Claude / MCP Client Integration

Add to your Claude MCP config (usually `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\ABSOLUTE\PATH\TO\mcp_servers\spotify",
        "run",
        "spotify-mcp",
        "--port",
        "5001"
      ]
    }
  }
}
```

Restart Claude Desktop, and you can run commands like:
- “Search Spotify for the track ‘Blinding Lights’ and return the top 3 results.”
- “Play ‘Shape of You’ on Spotify.”
- “Pause the current playback.”

---

## Testing via Postman

The MCP server speaks **JSON-RPC over HTTP**.

**Example: List all tools**
```http
POST http://localhost:5001/mcp
Content-Type: application/json
Accept: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list"
}
```

**Example: Search a song**
```http
POST http://localhost:5001/mcp
Content-Type: application/json
Accept: application/json

{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/call",
  "params": {
    "name": "SpotifySearch",
    "arguments": {
      "query": "Blinding Lights",
      "limit": 3
    }
  }
}
```

---

## Available Tools

| Tool Name         | Description |
|-------------------|-------------|
| **SpotifyPlayback** | Manage playback: get info, start, pause, skip |
| **SpotifySearch**   | Search for tracks, albums, artists, playlists |
| **SpotifyQueue**    | View or add to playback queue |
| **SpotifyGetInfo**  | Get details about a track, album, artist, playlist |
| **SpotifyPlaylist** | Manage playlists: get, add tracks, remove tracks, edit details |

---

## Error Handling
- If the access token is **missing** → returns `"Missing Spotify access token"`
- If the access token is **invalid/expired** → returns `"Invalid access token"` or `"401 Unauthorized"`
- All errors are sent as JSON-RPC `error` objects for consistency.

---

## Development
- Code is formatted with `ruff` / `black`
- Python ≥ 3.12 required
- Dependencies are managed with [uv](https://github.com/astral-sh/uv)

---
