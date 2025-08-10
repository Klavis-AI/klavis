# Klavis Tavily MCP Server

A Model Context Protocol (MCP) server for the Tavily AI Search API.

It exposes two atomic tools:

1. `tavily_search` — Perform a web search and return structured results (optionally with an answer).
2. `tavily_extract` — Extract the main content from one or more URLs (markdown or text).

---

## Requirements

- Python 3.10+ (3.12+ works)
- Tavily API key: `TAVILY_API_KEY`
- Optional: MCP Inspector for testing the server locally

---

## Quick Start (macOS and Windows)

### 1) Clone and create a virtual environment

**macOS / Linux (bash):**

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv .venv
source .venv/bin/activate
Windows (PowerShell):

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv .venv
.venv\Scripts\Activate.ps1

2) Install the package (editable)
pip install -U pip
pip install -e .

3) Provide your API key
macOS / Linux (bash):
export TAVILY_API_KEY=your_api_key_here

Windows (PowerShell):
$env:TAVILY_API_KEY="your_api_key_here"
Tip: For local convenience you can create a .env file with TAVILY_API_KEY=... (do not commit it). An .env.example is provided as a template.

4) Run the server
Always run as a module (recommended with a src/ layout):
python -m klavis_tavily_mcp.server
The server starts in stdio mode and waits for an MCP client (e.g., MCP Inspector, Claude Desktop).

Testing with MCP Inspector
Install and launch Inspector
macOS (Homebrew):
brew install mcp-inspector
mcp-inspector
macOS or Windows (Node.js via npx):
npx @modelcontextprotocol/inspector
This opens a browser at http://localhost:6274.

Connect Inspector to this server
In the Inspector UI:

Transport: STDIO

Command: path to your venv Python

macOS: /full/path/to/project/.venv/bin/python

Windows: C:\full\path\to\project\.venv\Scripts\python.exe

Arguments: -m klavis_tavily_mcp.server

Environment Variables: TAVILY_API_KEY=your_api_key_here

Click Connect.

Go to Tools → you should see tavily_search and tavily_extract.

Run tavily_search first, then copy a URL and run tavily_extract.

Tools
tavily_search
Inputs

query (str) — search query

max_results (int, default 5, 1–20)

search_depth (basic | advanced, default advanced)

include_answer (bool, default true)

include_raw_content (bool, default false)

Output shape (example)

json
Copy
Edit
{
  "ok": true,
  "data": {
    "query": "your query",
    "answer": "optional synthesis",
    "results": [
      {"title": "...", "url": "...", "score": 0.83, "content": "..."}
    ]
  }
}
tavily_extract
Inputs

urls (list[str]) — absolute URLs

extract_depth (basic | advanced, default basic)

format (markdown | text, default markdown)

include_images (bool, default false)

include_favicon (bool, default false)

Output shape (example)

json
Copy
Edit
{
  "ok": true,
  "data": {
    "results": [
      {"url": "https://...", "raw_content": "markdown or text"}
    ]
  }
}
Run from Visual Studio Code (macOS and Windows)
Open the project folder in VS Code.

Select the Python interpreter:

Command Palette → “Python: Select Interpreter” → choose the one inside .venv.

Create .vscode/launch.json with this content:

json
Copy
Edit
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "MCP: klavis-tavily (stdio)",
      "type": "python",
      "request": "launch",
      "module": "klavis_tavily_mcp.server",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "TAVILY_API_KEY": "${env:TAVILY_API_KEY}"
      }
    }
  ]
}
Press “Run and Debug” and choose MCP: klavis-tavily (stdio).

Start MCP Inspector and connect as described above.

Project Hygiene
Do not commit secrets:

Keep .env out of Git. Use .env.example for placeholders.

Suggested .gitignore:

bash
Copy
Edit
.venv/
venv/
.env
__pycache__/
*.pyc
When using a src/ layout, prefer python -m klavis_tavily_mcp.server over running a file path.

```
