This document shows end-to-end evidence that the server works as specified.  
All screenshots are located under `docs/screenshots/`.

---

## 1) Tools are registered

**Action:** Connect MCP Inspector and list tools.  
**Expectation:** `tavily_search` and `tavily_extract` appear with clear descriptions and schemas.

- `docs/screenshots/step1_list_tools.png`
- `docs/screenshots/step-2_tools_list.png`

---

## 2) Search works

**Action:** Call `tavily_search` with query:  
“latest AI regulation updates in the European Union”, `max_results=3`, `search_depth=advanced`, `include_answer=true`.

**Expectation:** `ok: true` with structured results including URLs and optional synthesized answer.

- Request: `docs/screenshots/step-3_search_request.png`
- Response: `docs/screenshots/step-4_search_response.png`

---

## 3) Extraction works

**Action:** Take one URL from search results and call `tavily_extract` with:  
`extract_depth="basic"`, `format="markdown"`, `include_images=false`, `include_favicon=false`.

**Expectation:** `ok: true` with `results[0].raw_content` containing readable page content.

- Request: `docs/screenshots/step-5_extract_request.png`
- Response: `docs/screenshots/step-6_extract_response.png`

---

## 4) Server runtime evidence

**Action:** Run the server in Visual Studio Code integrated terminal and send requests from Inspector.

**Expectation:** Logs show stdio startup and tool calls being received.

- Terminal log: `docs/screenshots/terminal_Result_1.png`
- Terminal log: `docs/screenshots/terminal_Result_2.png`

---

## Reproducing the Results

### macOS / Linux (bash)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
export TAVILY_API_KEY=your_api_key_here
python -m klavis_tavily_mcp.server
In MCP Inspector:

Transport: STDIO

Command: .venv/bin/python

Arguments: -m klavis_tavily_mcp.server

Env: TAVILY_API_KEY=your_api_key_here

Connect → Run tavily_search → copy a result URL → run tavily_extract.

Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
$env:TAVILY_API_KEY="your_api_key_here"
python -m klavis_tavily_mcp.server
In MCP Inspector:

Transport: STDIO

Command: .venv\Scripts\python.exe

Arguments: -m klavis_tavily_mcp.server

Env: TAVILY_API_KEY=your_api_key_here

Connect → Run tavily_search → copy a result URL → run tavily_extract.

Expected outcome: You should observe ok: true responses matching the screenshots above.


```
