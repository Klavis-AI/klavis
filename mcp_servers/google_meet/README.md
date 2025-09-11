# Google Meet MCP Server

Lightweight MCP server for Google Meet (Google Calendar) events: create, list (upcoming & past), update, delete, fetch details + past attendees. Sends invites / update emails when you want.

## Tools

create: google_meet_create_meet  (notify_attendees default true)

list upcoming: google_meet_list_meetings

list past: google_meet_list_past_meetings

details: google_meet_get_meeting_details

update: google_meet_update_meeting (change detection + optional notify)

delete: google_meet_delete_meeting

past attendees: google_meet_get_past_meeting_attendees

## Quick Start

```bash
uv venv
./.venv/Scripts/Activate.ps1   # (PowerShell)  |  source .venv/bin/activate (bash)
uv pip install -r requirements.txt
set GOOGLE_MEET_MCP_SERVER_PORT=5000
set AUTH_DATA={"access_token":"ya29.your_token"}
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

Scopes: needs calendar events write (e.g. <https://www.googleapis.com/auth/calendar>).

## Create Example

```json
{
  "name": "google_meet_create_meet",
  "arguments": {
    "summary": "Team Sync",
    "start_time": "2025-09-05T10:00:00Z",
    "end_time": "2025-09-05T10:30:00Z",
    "attendees": ["a@example.com","b@example.com"],
    "description": "Daily standup",
    "notify_attendees": true
  }
}
```

## Past Meetings

```json
{
  "name": "google_meet_list_past_meetings",
  "arguments": {"max_results": 5}
}
```

## Update Meeting (resend notifications)

```json
{
  "name": "google_meet_update_meeting",
  "arguments": {
    "event_id": "abc123",
    "start_time": "2025-09-05T11:00:00Z",
    "end_time": "2025-09-05T11:30:00Z",
    "notify_attendees": true
  }
}
```

## Behavior Notes

- Invitations: create/update uses sendUpdates=all when notify_attendees true.
- Change detection: update skips API call + emails if nothing changed.
- Meet detection: conferenceData.entryPoints OR hangoutLink.
- Past list: excludes all‑day events; 30‑day default lookback.
- Attendees fetch: only allowed for ended events.

## Package Layout

```text
server.py      # tooling + transports
tools/
  base.py      # core logic
  utils.py     # validation + shaping
```
## License

MIT
