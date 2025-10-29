import os, json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from src.zoom_client import ZoomClient, ZoomError

# Load environment variables from .env file 
load_dotenv()

# Initialize the MCP server with name
mcp = FastMCP("mcp-zoom")

# Cache for the ZoomClient instance
_zoom: ZoomClient | None = None

def zoom() -> ZoomClient:
    """Return a singleton ZoomClient instance."""
    global _zoom
    if _zoom is None:
        _zoom = ZoomClient()
    return _zoom

# Helpers for output formatting
def _ok(data: dict) -> str:
    """Wrap a successful result in JSON."""
    return json.dumps(data, ensure_ascii=False)

def _err(msg: str) -> str:
    """Wrap an error message in JSON."""
    return json.dumps({"error": msg}, ensure_ascii=False)


# MCP Tools

@mcp.tool()
def health_check() -> str:
    """
    Check if the server is running and if required Zoom credentials are set.
    Returns 'ok' if all required env vars exist, otherwise lists the missing ones.
    """
    missing = [k for k in ["ZOOM_ACCOUNT_ID", "ZOOM_CLIENT_ID", "ZOOM_CLIENT_SECRET"] if not os.getenv(k)]
    status = "ok" if not missing else f"missing env: {', '.join(missing)}"
    return _ok({"status": status})

@mcp.tool()
async def list_meetings(user_id_or_email: str, type: str = "upcoming", page_size: int = 10) -> str:
    """
    List Zoom meetings for a specific user (by email or user ID).
    Defaults to upcoming meetings, limited by page_size.
    """
    try:
        data = await zoom().list_meetings_for_user(user_id_or_email, page_size, type)
        meetings = [{
            "id": m["id"],
            "topic": m.get("topic", ""),
            "start_time": m.get("start_time"),
            "join_url": m.get("join_url"),
        } for m in data.get("meetings", [])]
        return _ok({"meetings": meetings, "next_page_token": data.get("next_page_token")})
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")

@mcp.tool()
async def create_meeting(
    user_id_or_email: str,
    topic: str,
    start_time_iso: str,
    duration_minutes: int = 30,
    timezone: str | None = None,
    settings: dict | None = None,
) -> str:
    """
    Create a scheduled Zoom meeting for a given user.
    Requires ISO 8601 start time format and supports custom settings.
    """
    try:
        res = await zoom().create_meeting(
            user_id_or_email=user_id_or_email,
            topic=topic,
            start_time_iso=start_time_iso,
            duration_minutes=duration_minutes,
            timezone=timezone,
            settings=settings,
        )
        out = {
            "meeting_id": res["id"],
            "join_url": res["join_url"],
            "start_url": res["start_url"],
            "password": res.get("password"),
        }
        return _ok(out)
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")

@mcp.tool()
async def get_meeting(meeting_id: str | int) -> str:
    """Fetch full details for a specific Zoom meeting."""
    try:
        res = await zoom().get_meeting(meeting_id)
        return _ok(res)
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")

@mcp.tool()
async def update_meeting(
    meeting_id: str | int | None = None,
    patch_fields: dict | None = None
) -> str:
    """
    Update selected fields for a meeting.
    Example patch_fields:
      {"topic":"New title","agenda":"Notes","settings":{"mute_upon_entry":true}}
    """
    if meeting_id in (None, ""):
        return _err("Missing required parameter: meeting_id")
    if not isinstance(patch_fields, dict) or not patch_fields:
        return _err("Missing or invalid parameter: patch_fields (expected a non-empty object)")

    try:
        res = await zoom().update_meeting(meeting_id, patch_fields)
        return _ok(res or {"updated": True, "meeting_id": meeting_id})
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")

@mcp.tool()
async def delete_meeting(meeting_id: str | int | None = None) -> str:
    """Delete/cancel a Zoom meeting."""
    if meeting_id in (None, ""):
        return _err("Missing required parameter: meeting_id")

    try:
        await zoom().delete_meeting(meeting_id)
        return _ok({"deleted": True, "meeting_id": meeting_id})
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")

@mcp.tool()
async def list_users(page_size: int = 30, status: str = "active") -> str:
    """
    List all users in the Zoom account.
    Useful for finding target user IDs or emails.
    """
    try:
        res = await zoom().list_users(page_size=page_size, status=status)
        users = [
            {
                "id": u["id"],
                "email": u.get("email"),
                "first_name": u.get("first_name"),
                "last_name": u.get("last_name")
            }
            for u in res.get("users", [])
        ]
        return _ok({"users": users, "next_page_token": res.get("next_page_token")})
    except ZoomError as ze:
        detail = (ze.payload or {}).get("message") or (ze.payload or {}).get("code") or (ze.payload or {}).get("text")
        return _err(f"Zoom error {ze.status}: {detail}")


# Start the MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")
