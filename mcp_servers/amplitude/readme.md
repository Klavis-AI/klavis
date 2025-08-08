# Amplitude MCP Server (Short)

Atomic MCP tools for Amplitude that work on any project:

- **track_event** — send one event via HTTP V2
- **identify_user** — set user properties / link user_id or device_id

Optional (plan-gated, not enabled by default):
- **list_event_categories** — Amplitude Taxonomy (Enterprise)
- **get_user_profile** — User Profile API (Activation, US-only)

---

## Requirements
- Python 3.10+
- `requests`, `python-dotenv`, `pytest`
- Choose ONE runtime:
  - **Standard MCP**: `pip install "mcp[cli]"` and import from `mcp.server.fastmcp`
  - **Klavis runtime**: keep `from klavis import MCPServer`

## Setup
```bash
cd servers/amplitude_mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env:
# AMPLITUDE_API_KEY=...
```
## Mock Test
```bash
pytest
```
## Smoke tests (live)

1) track_event (HTTP V2, JSON body)
```bash
US endpoint (default):
curl -sS -X POST "https://api2.amplitude.com/2/httpapi" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key":"YOUR_API_KEY",
    "events":[{
      "event_type":"mcp_smoke_test",
      "user_id":"mcp_user_12345",
      "event_properties":{"source":"mcp","purpose":"smoke_test"}
    }]
  }'
```
```bash
2) identify_user (form-encoded, NOT JSON)
curl --location --request POST "https://api2.amplitude.com/identify" \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "api_key=YOUR_API_KEY" \
  --data-urlencode 'identification=[{"user_id":"mcp_user_12345","user_properties":{"plan":"free","source":"mcp"}}]'
```
Expected: success

Common pitfall: sending JSON here → 400 missing_event.
EU projects: https://api.eu.amplitude.com/identify.