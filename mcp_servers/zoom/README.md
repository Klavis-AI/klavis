# MCP Zoom Server

A Model Context Protocol (MCP) server that exposes Zoom meeting, user, and recording functionality as tools. This allows MCP-compatible clients to interact with Zoom without manual API calls.

## Purpose

The server wraps common Zoom API actions (list, create, update, delete meetings; list users; retrieve recordings) into simple, atomic tools. Each tool returns structured JSON, making it easy for an AI client to chain calls or process the results.

---

## Installation & Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
install "mcp[cli]" httpx pydantic python-dotenv tenacity
install python-dotenv mcp fastmcp
4. Get Zoom API Credentials
Go to Zoom App Marketplace → Build App → choose Server-to-Server OAuth.

Fill in the required details.
Under Scopes, include at least:
Meetings: meeting:read:admin, meeting:write:admin
Users: user:read:admin, user:read:list_users:admin
Recordings: recording:read:admin

Activate the app and copy:
Account ID
Client ID
Client Secret

Environment Variables
Store credentials in a .env file in the project root:

ZOOM_ACCOUNT_ID=your_account_id
ZOOM_CLIENT_ID=your_client_id
ZOOM_CLIENT_SECRET=your_client_secret
Do not commit this file to source control.

5. Running the Server
python -m src.server


6. Available Tools
Tool	Description
health_check()	Checks server status and required environment variables
list_users()	Lists Zoom users in the account
list_meetings(user_id_or_email, type, page_size)	Lists meetings for a specific user
create_meeting(user_id_or_email, topic, start_time_iso, duration_minutes, timezone, settings)	Creates a scheduled meeting
get_meeting(meeting_id)	Retrieves meeting details
update_meeting(meeting_id, patch_fields)	Updates meeting properties
delete_meeting(meeting_id)	Deletes a meeting
list_recordings_for_meeting(meeting_id)	Lists recordings for a given meeting
list_recordings_for_user(user_id_or_email, from, to, page_size)	Lists recordings for a user in a date range

