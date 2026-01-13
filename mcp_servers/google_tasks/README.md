# Google Tasks MCP Server

Lightweight MCP server for Google Tasks: create, list, update, delete, move tasks and task lists. Full CRUD operations with pagination, filtering, and comprehensive task management.

## Tools

**Task Lists:**
- create: `google_tasks_create_task_list`
- list: `google_tasks_list_task_lists` (with pagination)
- get: `google_tasks_get_task_list`
- update: `google_tasks_update_task_list`
- delete: `google_tasks_delete_task_list`

**Tasks:**
- create: `google_tasks_create_task` (with status, completion, due dates)
- list: `google_tasks_list_tasks` (with pagination, filtering, date ranges)
- get: `google_tasks_get_task`
- update: `google_tasks_update_task` (comprehensive task updates)
- delete: `google_tasks_delete_task`
- move: `google_tasks_move_task` (reorder, move between lists)
- clear: `google_tasks_clear_completed_tasks`

## Quick Start

```bash
uv venv
./.venv/Scripts/Activate.ps1   # (PowerShell)  |  source .venv/bin/activate (bash)
uv pip install -r requirements.txt
set GOOGLE_TASKS_MCP_SERVER_PORT=5000
set AUTH_DATA={"access_token":"xxxx.your_token"}
uv run server.py --stdio  # stdio mode (Claude Desktop)
# OR HTTP/SSE
uv run server.py --port 5000 --log-level INFO
```

HTTP endpoints:

SSE: <http://localhost:5000/sse>

StreamableHTTP: <http://localhost:5000/mcp>

## Auth

Two ways:

1. Stdio: AUTH_DATA env JSON {"access_token":"..."}
2. HTTP/SSE: header x-auth-data = base64(JSON with access_token)

Scopes: needs tasks read/write (e.g. <https://www.googleapis.com/auth/tasks>).

## Create Task List Example

```json
{
  "name": "google_tasks_create_task_list",
  "arguments": {
    "title": "My Project Tasks"
  }
}
```

## List Tasks with Filtering

```json
{
  "name": "google_tasks_list_tasks",
  "arguments": {
    "task_list_id": "MDg4NTgzNTA4ODY2ODMxMjUzNTc6MDow",
    "completed_max": "2025-10-10T23:59:59Z",
    "completed_min": "2025-10-01T00:00:00Z",
    "show_completed": true
  }
}
```

## Update Task Example

```json
{
  "name": "google_tasks_update_task",
  "arguments": {
    "task_list_id": "MTIzNDU2Nzg5MA",
    "task_id": "dGFza18xMjM0NTY3ODkw",
    "status": "completed",
  }
}
```

## Move Task Example

```json
{
  "name": "google_tasks_move_task",
  "arguments": {
    "task_list_id": "MTIzNDU2Nzg5MA",
    "task_id": "dGFza18xMjM0NTY3ODkw",
    "previous": "dGFza19wcmV2aW91czEyMzQ",
  }
}
```

## Delete Task

```json
{
  "name": "google_tasks_delete_task",
  "arguments": {
    "task_id": "V3VvNy01MFEzSFJnUXVrdg",
    "task_list_id": "MDg4NTgzNTA4ODY2ODMxMjUzNTc6MDow"
  }
}
```

## Behavior Notes

- **Date Filtering**: Use RFC 3339 timestamps for `completed_min/max`, `due_min/max`
- **Task Status**: `needsAction` or `completed`
- **Task Hierarchy**: Use `parent` and `previous` for subtasks and ordering
- **Cross-List Moves**: Use `destination_tasklist` to move tasks between lists

## Advanced Features

**Date Range Filtering:**
- Filter tasks by completion date range
- Filter tasks by due date range
- Combine multiple filters for precise results

**Task Management:**
- Create subtasks with parent relationships
- Reorder tasks with previous sibling references
- Move tasks between different task lists
- Bulk clear completed tasks

## Package Layout

```text
server.py      # tooling + transports
tools/
  base.py      # core logic
  utils.py     # validation + shaping
  __init__.py  # module exports
```

## License

MIT
