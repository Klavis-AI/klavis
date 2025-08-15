import json
import logging
import mcp.types as types
from tools import (
    create_meeting,
    get_meeting_details,
    get_past_meetings,
    get_past_meeting_details,
    get_past_meeting_participants,
)

logger = logging.getLogger(__name__)


async def list_tools() -> list[types.Tool]:
    """Define all the tools available in this server. Each tool has a name, description, and input schema for validation."""
    return [
        types.Tool(
            name="create_meeting",
            description="Create a new meeting",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_meeting_details",
            description="Get details of a meeting",
            inputSchema={
                "type": "object",
                "required": ["space_id"],
                "properties": {
                    "space_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^spaces/[a-zA-Z0-9\\-_]+$",
                        "description": "Meeting space ID (spaces/{space-id})"
                    }
                }
            },
        ),
        types.Tool(
            name="get_past_meetings",
            description="Get details for completed meetings",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of records to return"},
                    "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                    "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                }
            },
        ),
        types.Tool(
            name="get_past_meeting_details",
            description="Get details of a specific meeting",
            inputSchema={
                "type": "object",
                "required": ["conference_record_id"],
                "properties": {
                    "conference_record_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                        "description": "Conference record ID (conferenceRecords/{record-id})"
                    }
                }
            },
        ),
        types.Tool(
            name="get_past_meeting_participants",
            description="Get a list of participants from a past meeting",
            inputSchema={
                "type": "object",
                "required": ["conference_record_id"],
                "properties": {
                    "conference_record_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1000,
                        "pattern": "^conferenceRecords/[a-zA-Z0-9\\-_]+$",
                        "description": "Conference record ID (conferenceRecords/{record-id})"
                    },
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10, "description": "Maximum number of participants to return"},
                    "page_token": {"type": "string", "maxLength": 5000, "description": "Token for pagination"},
                    "filter": {"type": "string", "maxLength": 2000, "description": "Filter expression"}
                }
            },
        ),
    ]


async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """This is where we route the tool calls. Based on the name, we call the right function and return the result as text."""
    try:
        if name == "create_meeting":
            result = await create_meeting(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_meeting_details":
            result = await get_meeting_details(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meetings":
            result = await get_past_meetings(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meeting_details":
            result = await get_past_meeting_details(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        elif name == "get_past_meeting_participants":
            result = await get_past_meeting_participants(arguments)
            return [types.TextContent(type="text", text=json.dumps(result))]
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
