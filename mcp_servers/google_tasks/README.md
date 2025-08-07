# Google Tasks MCP Server

This MCP server exposes Google Tasks as a set of atomic tools that AI agents can invoke through the [Model Context Protocol](https://modelcontextprotocol.io/).

## Features

| Tool | Purpose |
|------|---------|
| `google_list_tasklists` | List every tasklist the user owns |
| `google_get_tasklist` | Retrieve metadata about a single tasklist |
| `google_create_tasklist` | Create a new tasklist |
| `google_delete_tasklist` | Delete an entire tasklist |
| `google_list_tasks` | List tasks in a tasklist (optionally hide completed) |
| `google_get_task` | Retrieve a single task |
| `google_create_task` | Create a task (with optional notes, due, parent, position) |
| `google_update_task` | Update *any* mutable fields on a task |
| `google_move_task` | Move a task under a different parent / position |
| `google_clear_completed_tasks` | Bulk-delete all completed tasks in a tasklist |
| `google_delete_task` | Delete a task |

All responses are raw JSON straight from the Google Tasks API, making them easy for LLMs to inspect.

## Quick Start (Local)

1. **Create a Google OAuth client** (Desktop or Web), grab the Client ID & Client Secret, and generate a refresh token that has the `https://www.googleapis.com/auth/tasks` scope.

2. **Set environment variables** (either via `export` or a `.env` file):

   ```bash
   cp env.example .env  # or set vars manually
   export GOOGLE_CLIENT_ID=... \
          GOOGLE_CLIENT_SECRET=... \
          GOOGLE_REFRESH_TOKEN=...
   ```

3. **Install deps + run:**

   ```bash
   pip install -r requirements.txt
   python server.py --port 5000
   ```

   The server starts with dual transports:
   * SSE  → `http://localhost:5000/sse`
   * StreamableHTTP → `http://localhost:5000/mcp`

4. **Connect from a client** (Cursor, Claude Desktop, etc.) and trigger tools with natural language.

## Docker

```bash
docker build -t google-tasks-mcp -f mcp_servers/google_tasks/Dockerfile .

# Pass credentials at runtime
docker run -p 5000:5000 \
  -e GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID \
  -e GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET \
  -e GOOGLE_REFRESH_TOKEN=$GOOGLE_REFRESH_TOKEN \
  google-tasks-mcp
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth Client Secret |
| `GOOGLE_REFRESH_TOKEN` | OAuth Refresh Token (offline access) |
| `GOOGLE_TASKS_MCP_SERVER_PORT` | Optional; default `5000` |

These are loaded at runtime via [`python-dotenv`](https://pypi.org/project/python-dotenv/) so you can also put them in a `.env` file.

## Development Notes

* Code style: `ruff`, `black`, `mypy --strict`
* Tests live in `tests/` and use `pytest` + `responses`.
* Error handling currently passes through Google `HttpError` JSON; a centralized mapper is on the todo list.

---
**License:** MIT (see root LICENSE file)

