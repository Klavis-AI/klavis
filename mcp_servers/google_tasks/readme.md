# Google Tasks MCP Server

An **MCP (Model Context Protocol)** server that exposes **atomic tools** for Google Tasks.
It speaks MCP over **Streamable HTTP** (`/mcp/`) and supports **SSE** (`/sse`).
Designed to be consumed by AI agents (VS Code OpenAI Chat / Copilot Chat with MCP), or tested directly with `curl`.

---

## Features

* **Atomic tools** (one job each): list task lists, create task list, list tasks, create task, update task, delete task.
* **Rate limiting** (per tool, configurable).
* **Stateless** HTTP server; authenticates to Google via OAuth **refresh token**.
* **Dual transports**: SSE (`/sse`) and Streamable HTTP (`/mcp/`).

---

## Project Layout

```
.
├── server.py            # MCP server (single file)
├── requirements.txt     # Python deps (includes mcp, starlette, google client)
├── Dockerfile
├── .env.example         # sample env file
├── .vscode/mcp.json     # VS Code MCP client config (example)
└── proof/               # screenshots proving each tool works
    ├── gt_list_task_lists.png
    ├── gt_create_task_list.png
    ├── gt_list_tasks.png
    ├── gt_create_task.png
    ├── gt_update_task.png
    ├── gt_update_task_result.png
    ├── gt_delete_task.png
    └── gt_delete_task_result.png
```

---

## Requirements

* Python 3.11+ (or Docker)
* Google Cloud **OAuth Client (Desktop App)** with the **Tasks** scope granted.
* A refresh token for the scope: `https://www.googleapis.com/auth/tasks`

> **Tip**: Create an OAuth client in Google Cloud Console → OAuth consent (user type External is fine for testing) → Credentials → “Create credentials → OAuth client ID → Desktop”. Authorize once (via your own small script or OAuth Playground) to obtain a **refresh token**.

---

## Environment

Create `.env` (see `.env.example`):

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token

# Optional
GOOGLE_TASKS_MCP_SERVER_PORT=5000
GOOGLE_TASKS_RATE_MAX=60       # max calls
GOOGLE_TASKS_RATE_PERIOD=60    # in seconds
```

---

## Install & Run

### Option A: Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run
python server.py \
  --port 5000 \
  --log-level INFO \
  --rate-max 60 \
  --rate-period 60
```

You should see:

```
Server starting on port 5000 with dual transports:
  - SSE endpoint: http://localhost:5000/sse
  - StreamableHTTP endpoint: http://localhost:5000/mcp
Uvicorn running on http://0.0.0.0:5000
```

### Option B: Docker

```bash
docker build -t google-tasks-server .
docker run --rm -it --env-file .env -p 5000:5000 google-tasks-server
```

---

## MCP Tools

The server registers these tools:

| Tool name             | What it does                       | Required args             | Optional args                |
| --------------------- | ---------------------------------- | ------------------------- | ---------------------------- |
| `gt_list_task_lists`  | List all Google Task lists         | —                         | —                            |
| `gt_create_task_list` | Create a task list                 | `title`                   | —                            |
| `gt_list_tasks`       | List tasks in a task list          | `task_list_id`            | —                            |
| `gt_create_task`      | Create a task                      | `task_list_id`, `title`   | `notes`                      |
| `gt_update_task`      | Update a task (title/notes/status) | `task_list_id`, `task_id` | `title`, `notes`, `status`\* |
| `gt_delete_task`      | Delete a task                      | `task_list_id`, `task_id` | —                            |

\* `status` must be one of: `needsAction`, `completed`.

**Rate limiting:** Per tool; defaults to `60` calls per `60` seconds (tunable via env or CLI). When exceeded the server returns a JSON error like:

```json
{"error":"Rate limit exceeded for 'gt_create_task': 60 calls per 60s."}
```

---

## Testing with `curl`

> **Important**: Streamable HTTP requires the client to **accept both** `application/json` and `text/event-stream`.

### 1) List tools

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}' \
  http://localhost:5000/mcp/
```

### 2) Call a tool

**List Task Lists**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
        "jsonrpc":"2.0",
        "id":"2",
        "method":"tools/call",
        "params":{"name":"gt_list_task_lists","arguments":{}}
      }' \
  http://localhost:5000/mcp/
```

**Create Task List**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
        "jsonrpc":"2.0",
        "id":"3",
        "method":"tools/call",
        "params":{"name":"gt_create_task_list","arguments":{"title":"MCP Test"}}
      }' \
  http://localhost:5000/mcp/
```

**Create Task**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{
        \"jsonrpc\":\"2.0\",
        \"id\":\"4\",
        \"method\":\"tools/call\",
        \"params\":{\"name\":\"gt_create_task\",
          \"arguments\":{\"task_list_id\":\"<LIST_ID>\",\"title\":\"Write proof screenshots\",\"notes\":\"via MCP\"}
        }
      }" \
  http://localhost:5000/mcp/
```

**List Tasks**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{
        \"jsonrpc\":\"2.0\",
        \"id\":\"5\",
        \"method\":\"tools/call\",
        \"params\":{\"name\":\"gt_list_tasks\",\"arguments\":{\"task_list_id\":\"<LIST_ID>\"}}
      }" \
  http://localhost:5000/mcp/
```

**Update Task (mark completed)**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{
        \"jsonrpc\":\"2.0\",
        \"id\":\"6\",
        \"method\":\"tools/call\",
        \"params\":{\"name\":\"gt_update_task\",
          \"arguments\":{\"task_list_id\":\"<LIST_ID>\",\"task_id\":\"<TASK_ID>\",\"status\":\"completed\"}
        }
      }" \
  http://localhost:5000/mcp/
```

**Delete Task**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{
        \"jsonrpc\":\"2.0\",
        \"id\":\"7\",
        \"method\":\"tools/call\",
        \"params\":{\"name\":\"gt_delete_task\",
          \"arguments\":{\"task_list_id\":\"<LIST_ID>\",\"task_id\":\"<TASK_ID>\"}
        }
      }" \
  http://localhost:5000/mcp/
```

---

## Using in VS Code (MCP)

1. Ensure your server is running on port `5000`.

2. Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "googleTasks": {
      "type": "http",
      "url": "http://localhost:5000/mcp/"
    }
  }
}
```

3. Open **Chat**:

   * **OpenAI Chat extension** → set **Agent** to a GPT model (e.g., GPT-4o)
     or
   * **GitHub Copilot Chat** (with MCP support).

4. Click the **Tools** (beaker) icon → **enable** `googleTasks`.

5. Try natural prompts:

   * “**List my Google Task lists.**”
   * “**Create a task list called ‘MCP Test’.**”
   * “**Create a task ‘Write proof screenshots’ in list `<LIST_ID>`.**”
   * “**Show tasks in `<LIST_ID>`.**”
   * “**Mark task `<TASK_ID>` completed.**”
   * “**Delete task `<TASK_ID>` from `<LIST_ID>`.**”

> Some chat clients show a **Continue** confirmation before executing a tool. That’s expected. You can turn it off in the client settings if you prefer.

---

## Proof of Correctness

The `proof/` folder contains screenshots for each tool:

* `gt_list_task_lists.png`
* `gt_create_task_list.png`
* `gt_list_tasks.png`
* `gt_create_task.png`
* `gt_update_task.png` and `gt_update_task_result.png`
* `gt_delete_task.png` and `gt_delete_task_result.png`

Each shows a natural-language request, the server/tool invoked, and the result.

---

## Troubleshooting

* **406 / “Client must accept text/event-stream”**
  Include both types in `Accept` header:

  ```
  -H "Accept: application/json, text/event-stream"
  ```

* **307 redirect / 404**
  Use the **trailing slash** on `/mcp/` in both `curl` and `.vscode/mcp.json`.

* **Invalid request parameters**
  Use MCP methods **`tools/list`** and **`tools/call`** (not `list_tools` etc.).
  `tools/call` requires: `{"name": "...", "arguments": {...}}`.

* **Rate limit exceeded**
  Increase limits with `GOOGLE_TASKS_RATE_MAX` / `GOOGLE_TASKS_RATE_PERIOD`, or wait.

* **Google auth errors (403/401)**
  Verify `.env` values, refresh token validity, and that the **Tasks** scope was granted.

---

## Security Notes

* The server is **stateless** and relies on a **refresh token**. Keep `.env` private.
* Review rate limits before sharing access beyond local development.

---

## License

MIT (or your preferred license)