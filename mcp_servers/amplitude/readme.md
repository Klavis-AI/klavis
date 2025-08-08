# Amplitude MCP Serve

An MCP (Model Context Protocol) server exposing atomic Amplitude tools for AI agents. Built with the standard MCP Python SDK (FastMCP). 

- **track_event** — send one event via HTTP V2
- **identify_user** — set user properties / link user_id or device_id
- **list_event_categories** — Amplitude Taxonomy (Enterprise)
- **get_user_profile** — User Profile API (Activation, US-only)

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
python -m pytest
```

## Tools (function docs for AI clients)

1) track_event
	- •	Title: Track a single event (HTTP V2)
	- •	AI Prompt Words: track event, log event, record event
	- •	Parameters:
	- •	event_type (str, required) — event name
	- •	user_id (str, optional) — user identifier (≥5 chars)
	- •	device_id (str, optional) — alternative to user_id (≥5 chars)
	- •	event_properties (dict or JSON string, optional) — custom props
	- •	time (int ms or seconds, optional) — timestamp; seconds auto-converted to ms

Example:

“Track an Amplitude event named test for user username with properties {source:mcp, purpose:test}.”

2) identify_user
	- •	Title: Identify user / set user properties (Identify API)
	- •	AI Prompt Words: identify user, set user properties, update user profile
	- •	Parameters:
	- •	user_id (str, optional)
	- •	device_id (str, optional)
	- •	user_properties (dict, optional) — plain props to $set
	- •	operations (dict, optional) — advanced ops like $set, $add; overrides user_properties if provided

On success returns the string success.

Natural prompt example:

“Identify username and set {plan:free, source:test}.”

3) get_user_profile (visible; may be plan-gated)
	- •	Title: Get user profile (Profile API)
	- •	AI Prompt Words: get user profile, fetch user properties, show profile data
	- •	Parameters:
	- •	user_id (str, required)
	- •	get_amp_props, get_cohort_ids, get_recs, get_computations (bool, optional)


Natural prompt example:

“Get user profile for username including get_amp_props=true.”

4) list_event_categories (visible; may be plan-gated)
	- •	Title: List event categories (Taxonomy)
	- •	AI Prompt Words: list categories, show taxonomy categories
	- •	Parameters: (none)

Natural prompt example:

“List Amplitude event categories.”
