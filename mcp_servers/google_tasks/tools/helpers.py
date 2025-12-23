import os
import logging
import asyncio
from typing import Any, Dict
from dotenv import load_dotenv

# Google Tasks
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =========================
# Environment / Logging
# =========================
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-tasks-mcp-server")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN):
    raise ValueError(
        "Missing Google OAuth env vars. Required: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN."
    )

MCP_PORT = int(os.getenv("GOOGLE_TASKS_MCP_SERVER_PORT", "5000"))

# Default rate limits (can override via CLI or env)
DEFAULT_RATE_MAX = int(os.getenv("GOOGLE_TASKS_RATE_MAX", "60"))       # calls
DEFAULT_RATE_PERIOD = int(os.getenv("GOOGLE_TASKS_RATE_PERIOD", "60")) # seconds


def _get_service():
    """Build a Google Tasks API service using refresh token flow."""
    creds = Credentials(
        None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    return build("tasks", "v1", credentials=creds)

def _error_from_http(e: HttpError, default_msg: str) -> Dict[str, Any]:
    """Normalize Google API errors."""
    status = getattr(e, "resp", None).status if getattr(e, "resp", None) else None
    try:
        body = e.error_details if hasattr(e, "error_details") else None
    except Exception:
        body = None
    if status in (403, 429):
        return {"error": "Rate limit exceeded or unauthorized.", "status": status}
    return {"error": f"{default_msg} (HTTP {status})", "status": status, "details": str(e)}

async def _run_sync(fn, *args, **kwargs):
    """Run blocking Google client calls in a thread."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))