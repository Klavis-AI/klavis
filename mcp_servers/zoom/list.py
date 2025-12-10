import mcp.types as types


def get_tool_list() -> list[types.Tool]:
    """Get the list of available tools with their schemas."""
    return [
        types.Tool(
            name="zoom_create_meeting",
            description=(
                "Create a new Zoom meeting with customizable settings like topic, time, duration, "
                "and video/audio preferences.\n"
                "Prompt hints: 'schedule a meeting', 'create zoom call', 'set up team standup'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "required": ["topic"],
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"},
                    "topic": {"type": "string", "description": "Meeting topic/title"},
                    "type": {"type": "integer", "description": "Meeting type: 1=instant, 2=scheduled, 3=recurring", "default": 2},
                    "start_time": {"type": "string", "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)"},
                    "duration": {"type": "integer", "description": "Meeting duration in minutes", "default": 60},
                    "timezone": {"type": "string", "description": "Timezone (e.g., 'America/New_York')", "default": "UTC"},
                    "password": {"type": "string", "description": "Meeting password"},
                    "host_video": {"type": "boolean", "description": "Host video on/off", "default": True},
                    "participant_video": {"type": "boolean", "description": "Participant video on/off", "default": True},
                    "join_before_host": {"type": "boolean", "description": "Allow joining before host", "default": False},
                    "mute_upon_entry": {"type": "boolean", "description": "Mute participants on entry", "default": False},
                    "watermark": {"type": "boolean", "description": "Add watermark", "default": False},
                    "use_pmi": {"type": "boolean", "description": "Use Personal Meeting ID", "default": False},
                    "approval_type": {"type": "integer", "description": "Approval type: 0=automatically, 1=manually, 2=no registration", "default": 0},
                    "audio": {"type": "string", "description": "Audio options: 'both', 'telephony', 'computer_audio'", "default": "both"},
                    "auto_recording": {"type": "string", "description": "Auto recording: 'none', 'local', 'cloud'", "default": "none"}
                }
            }
        ),
        types.Tool(
            name="zoom_get_meeting",
            description=(
                "Retrieve detailed information about a specific Zoom meeting including settings, "
                "participants, and meeting status.\n"
                "Prompt hints: 'get meeting details', 'show meeting info', 'check meeting settings'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "required": ["meeting_id"],
                "properties": {
                    "meeting_id": {"type": "string", "description": "Zoom meeting ID"}
                }
            }
        ),
        types.Tool(
            name="zoom_update_meeting",
            description=(
                "Update meeting details like topic, time, duration, and settings for an existing Zoom meeting.\n"
                "Prompt hints: 'change meeting time', 'update meeting topic', 'modify meeting settings'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "required": ["meeting_id"],
                "properties": {
                    "meeting_id": {"type": "string", "description": "Zoom meeting ID"},
                    "topic": {"type": "string", "description": "New meeting topic/title"},
                    "type": {"type": "integer", "description": "Meeting type: 1=instant, 2=scheduled, 3=recurring"},
                    "start_time": {"type": "string", "description": "New start time in ISO format"},
                    "duration": {"type": "integer", "description": "New meeting duration in minutes"},
                    "timezone": {"type": "string", "description": "New timezone"},
                    "password": {"type": "string", "description": "New meeting password"},
                    "settings": {"type": "object", "description": "Meeting settings to update"}
                }
            }
        ),
        types.Tool(
            name="zoom_delete_meeting",
            description=(
                "Delete a Zoom meeting permanently. This action cannot be undone.\n"
                "Prompt hints: 'cancel meeting', 'delete zoom call', 'remove meeting'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "required": ["meeting_id"],
                "properties": {
                    "meeting_id": {"type": "string", "description": "Zoom meeting ID to delete"}
                }
            }
        ),
        types.Tool(
            name="zoom_list_meetings",
            description=(
                "List all meetings for a specific user with pagination support and filtering options.\n"
                "Prompt hints: 'show my meetings', 'list all meetings', 'get meeting history'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"},
                    "type": {"type": "string", "description": "Meeting type filter: 'scheduled', 'live', 'upcoming'"},
                    "page_size": {"type": "integer", "description": "Number of meetings per page", "default": 30},
                    "page_number": {"type": "integer", "description": "Page number for pagination", "default": 1},
                    "next_page_token": {"type": "string", "description": "Token for next page"}
                }
            }
        ),
        types.Tool(
            name="zoom_get_meeting_participants",
            description=(
                "Get the list of participants for a specific meeting including join/leave times and duration.\n"
                "Prompt hints: 'who joined the meeting', 'get participant list', 'show meeting attendees'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "required": ["meeting_id"],
                "properties": {
                    "meeting_id": {"type": "string", "description": "Zoom meeting ID"}
                }
            }
        ),
        types.Tool(
            name="zoom_get_user",
            description=(
                "Get detailed information about a specific Zoom user including account type, "
                "settings, and permissions.\n"
                "Prompt hints: 'get user info', 'show user details', 'check user account'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID or 'me' for current user", "default": "me"}
                }
            }
        ),
        types.Tool(
            name="zoom_list_users",
            description=(
                "List all users in the Zoom account with pagination and filtering options.\n"
                "Prompt hints: 'show all users', 'list team members', 'get user directory'\n"
                "⚠️ REQUIRES OAUTH: This tool requires a valid Zoom OAuth access token. "
                "If you don't have one, please ask the user to provide their Zoom OAuth access token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "User status filter: 'active', 'inactive', 'pending'"},
                    "role_id": {"type": "string", "description": "Role ID filter"},
                    "page_size": {"type": "integer", "description": "Number of users per page", "default": 30},
                    "page_number": {"type": "integer", "description": "Page number for pagination", "default": 1},
                    "next_page_token": {"type": "string", "description": "Token for next page"}
                }
            }
        ),
    ]
