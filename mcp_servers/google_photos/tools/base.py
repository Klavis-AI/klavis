import os
from dotenv import load_dotenv
import logging
from contextvars import ContextVar
from typing import Any, Dict

try:
    from google_photos.utils import get_picker_service, format_picker_media_item as _format_picker_media_item
except Exception:
    try:
        from ..utils import get_picker_service, format_picker_media_item as _format_picker_media_item
    except Exception:
        from utils import get_picker_service, format_picker_media_item as _format_picker_media_item

logger = logging.getLogger(__name__)

auth_token_context: ContextVar[str] = ContextVar('auth_token')


class ToolExecutionError(Exception):
    pass


def get_auth_token() -> str:
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")


env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


def get_picker_service_with_credentials(access_token: str):
    """Create a Picker API service client using environment-configured OAuth credentials.

    This mirrors the helper used in other MCP servers: callers provide the access_token
    and the helper wires in client/refresh/token_uri values from environment.
    """
    return get_picker_service(
        access_token,
        GOOGLE_REFRESH_TOKEN,
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        GOOGLE_TOKEN_URI,
    )


# Re-export the canonical formatter from `utils.py` so the implementation lives
# in a single place and other modules can import it from `tools.base`.
format_picker_media_item = _format_picker_media_item
