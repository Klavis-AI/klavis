import json
import logging
from typing import Any, Dict, Callable, Awaitable

import mcp.types as types

from tools.meetings import (
    zoom_create_meeting,
    zoom_get_meeting,
    zoom_update_meeting,
    zoom_delete_meeting,
    zoom_list_meetings,
    zoom_get_meeting_participants,
)
from tools.users import zoom_get_user, zoom_list_users

logger = logging.getLogger("zoom-mcp-server")

TOOL_REGISTRY = {
    "zoom_create_meeting": zoom_create_meeting,
    "zoom_get_meeting": zoom_get_meeting,
    "zoom_update_meeting": zoom_update_meeting,
    "zoom_delete_meeting": zoom_delete_meeting,
    "zoom_list_meetings": zoom_list_meetings,
    "zoom_get_meeting_participants": zoom_get_meeting_participants,
    "zoom_get_user": zoom_get_user,
    "zoom_list_users": zoom_list_users,
}

async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Execute a tool by name with the given arguments."""
    logger.info(f"call_tool: {name}")
    logger.debug(f"raw arguments: {json.dumps(arguments, indent=2)}")

    try:
        if name in TOOL_REGISTRY:
            handler = TOOL_REGISTRY[name]
            result = await handler(arguments)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
