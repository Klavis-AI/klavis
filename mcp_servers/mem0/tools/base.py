import json
import logging
import os
from contextvars import ContextVar
from typing import Any, Dict, Optional

from mem0 import MemoryClient
try:
    # Official mem0-mcp uses this import path.
    from mem0.exceptions import MemoryError  # type: ignore
except Exception:  # pragma: no cover
    MemoryError = Exception  # type: ignore[misc,assignment]

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False

logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_MCP_USER_ID = "user" # "user" is default user id for mem0 that can see from the dashboard

ENABLE_GRAPH_DEFAULT = (
    os.getenv("MEM0_ENABLE_GRAPH_DEFAULT", "false").lower() in {"1", "true", "yes"}
)

mem0_api_key_context: ContextVar[str] = ContextVar('mem0_api_key')
mem0_user_id_context: ContextVar[Optional[str]] = ContextVar('mem0_user_id', default=None)

def get_mem0_api_key() -> str:
    """Get the mem0 API key from context or environment."""
    try:
        return mem0_api_key_context.get()
    except LookupError:
        api_key = os.getenv("MEM0_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            raise RuntimeError("mem0 API key not found in request context or environment")
        return api_key

def get_mem0_user_id() -> Optional[str]:
    """Get the mem0 user ID from context or environment."""
    try:
        return mem0_user_id_context.get()
    except LookupError:
        return os.getenv("MEM0_DEFAULT_USER_ID", DEFAULT_MCP_USER_ID)

def default_enable_graph(enable_graph: Optional[bool]) -> bool:
    """Use caller override when provided, else use server default."""
    if enable_graph is None:
        return ENABLE_GRAPH_DEFAULT
    return bool(enable_graph)

def with_default_filters(
    filters: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normalize filter shape:
    - Ensure there is a boolean root (AND/OR/NOT); wrap plain dict into AND
    - If user_id is provided and not present in filters, inject it.
    """
    if not filters:
        if user_id:
            return {"AND": [{"user_id": user_id}]}
        return {}

    if not any(key in filters for key in ("AND", "OR", "NOT")):
        filters = {"AND": [filters]}
    
    if user_id:
        # Check if user_id is already in the filters
        has_user = json.dumps(filters, sort_keys=True).find('"user_id"') != -1
        if not has_user:
            and_list = filters.setdefault("AND", [])
            if not isinstance(and_list, list):
                # Should not happen if we respect the structure, but safe guard
                # If AND is not a list, we can't easily append. 
                # Fallback: wrap the whole thing? 
                # For now assume standard usage.
                logger.warning("filters['AND'] is not a list, skipping user_id injection")
            else:
                and_list.insert(0, {"user_id": user_id})

    return filters

def mem0_call(func, *args, **kwargs) -> Dict[str, Any]:
    """Call Mem0 client methods and surface structured errors (official-style)."""
    try:
        result = func(*args, **kwargs)
        return {"success": True, "result": result}
    except MemoryError as exc:
        logger.error("Mem0 call failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "status": getattr(exc, "status", None),
            "payload": getattr(exc, "payload", None),
        }
    except Exception as exc:
        logger.exception("Unexpected Mem0 call error: %s", exc)
        return {"success": False, "error": str(exc)}

def get_mem0_client() -> MemoryClient:
    """Get a configured mem0 client with current API key from context."""
    try:
        api_key = get_mem0_api_key()
        client = MemoryClient(api_key=api_key)
        logger.debug("mem0 client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize mem0 client: {e}")
        raise
