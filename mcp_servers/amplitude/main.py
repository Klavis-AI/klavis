
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("amplitude")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amplitude")

from tools.track_events import track_event as _track_event
from tools.identify_user import identify_user as _identify_user
from tools.get_user_profile import get_user_profile as _get_user_profile
from tools.list_event_categories import list_event_categories as _list_event_categories


@mcp.tool()
def track_event(
    event_type: str,
    user_id: str | None = None,
    device_id: str | None = None,
    event_properties: dict | None = None,
    time: int | float | None = None,
) -> dict:
    """Record a single Amplitude event via HTTP V2."""
    logger.info("TOOL_CALL track_event", extra={"event_type": event_type, "user_id": user_id, "device_id": device_id})
    return _track_event(event_type, user_id, device_id, event_properties, time)


@mcp.tool()
def identify_user(
    user_id: str | None = None,
    device_id: str | None = None,
    user_properties: dict | None = None,
    operations: dict | None = None,
) -> dict:
    """Set user properties via Identify API (form-encoded)."""
    logger.info("TOOL_CALL identify_user", extra={"user_id": user_id, "device_id": device_id})
    return _identify_user(user_id, device_id, user_properties, operations)


@mcp.tool()
def get_user_profile(
    user_id: str,
    get_amp_props: bool = False,
    get_cohort_ids: bool = False,
    get_recs: bool = False,
    get_computations: bool = False,
) -> dict:
    """Fetch user profile (may require Activation plan; returns a friendly error if unavailable)."""
    logger.info("TOOL_CALL get_user_profile", extra={"user_id": user_id})
    try:
        return _get_user_profile(user_id, get_amp_props, get_cohort_ids, get_recs, get_computations)
    except Exception as e:
        return {"error": "profile_api_unavailable_or_unauthorized", "detail": str(e)}

@mcp.tool()
def list_event_categories() -> dict:
    """List all event categories in Amplitude"""
    logger.info("TOOL_CALL list_event_categories")
    return _list_event_categories()


if __name__ == "__main__":
    print("[amplitude-mcp] started. Waiting for an MCP client...")
    mcp.run()