import json
from typing import Dict, Any
from .auth import get_zoom_client

async def zoom_create_meeting(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Zoom meeting."""
    try:
        client = get_zoom_client()
        
        # Extract required and optional parameters
        user_id = arguments.get("user_id", "me")  # Default to current user
        topic = arguments.get("topic", "New Meeting")
        meeting_type = arguments.get("type", 2)  # 2 = scheduled meeting
        
        # Build meeting data
        meeting_data = {
            "topic": topic,
            "type": meeting_type,
            "start_time": arguments.get("start_time"),
            "duration": arguments.get("duration", 60),
            "timezone": arguments.get("timezone", "UTC"),
            "password": arguments.get("password"),
            "settings": {
                "host_video": arguments.get("host_video", True),
                "participant_video": arguments.get("participant_video", True),
                "join_before_host": arguments.get("join_before_host", False),
                "mute_upon_entry": arguments.get("mute_upon_entry", False),
                "watermark": arguments.get("watermark", False),
                "use_pmi": arguments.get("use_pmi", False),
                "approval_type": arguments.get("approval_type", 0),
                "audio": arguments.get("audio", "both"),
                "auto_recording": arguments.get("auto_recording", "none")
            }
        }
        
        # Remove None values
        meeting_data = {k: v for k, v in meeting_data.items() if v is not None}
        if "settings" in meeting_data:
            meeting_data["settings"] = {k: v for k, v in meeting_data["settings"].items() if v is not None}
        
        endpoint = f"/users/{user_id}/meetings"
        result = await client.post(endpoint, meeting_data)
        
        return {
            "success": True,
            "meeting": result,
            "message": f"Meeting '{topic}' created successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create meeting"
        }

async def zoom_get_meeting(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get meeting details by ID."""
    try:
        client = get_zoom_client()
        meeting_id = arguments.get("meeting_id")
        
        if not meeting_id:
            return {
                "success": False,
                "error": "meeting_id is required",
                "message": "Please provide a meeting ID"
            }
        
        endpoint = f"/meetings/{meeting_id}"
        result = await client.get(endpoint)
        
        return {
            "success": True,
            "meeting": result,
            "message": "Meeting details retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get meeting details"
        }

async def zoom_update_meeting(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Update meeting details."""
    try:
        client = get_zoom_client()
        meeting_id = arguments.get("meeting_id")
        
        if not meeting_id:
            return {
                "success": False,
                "error": "meeting_id is required",
                "message": "Please provide a meeting ID"
            }
        
        # Build update data
        update_data = {}
        for key in ["topic", "type", "start_time", "duration", "timezone", "password"]:
            if key in arguments:
                update_data[key] = arguments[key]
        
        if "settings" in arguments:
            update_data["settings"] = arguments["settings"]
        
        if not update_data:
            return {
                "success": False,
                "error": "No update data provided",
                "message": "Please provide at least one field to update"
            }
        
        endpoint = f"/meetings/{meeting_id}"
        await client.put(endpoint, update_data)
        
        return {
            "success": True,
            "message": f"Meeting {meeting_id} updated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update meeting"
        }

async def zoom_delete_meeting(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a meeting."""
    try:
        client = get_zoom_client()
        meeting_id = arguments.get("meeting_id")
        
        if not meeting_id:
            return {
                "success": False,
                "error": "meeting_id is required",
                "message": "Please provide a meeting ID"
            }
        
        endpoint = f"/meetings/{meeting_id}"
        await client.delete(endpoint)
        
        return {
            "success": True,
            "message": f"Meeting {meeting_id} deleted successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete meeting"
        }

async def zoom_list_meetings(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List meetings for a user."""
    try:
        client = get_zoom_client()
        user_id = arguments.get("user_id", "me")
        
        # Build query parameters
        params = {}
        for key in ["type", "page_size", "page_number", "next_page_token"]:
            if key in arguments:
                params[key] = arguments[key]
        
        endpoint = f"/users/{user_id}/meetings"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        result = await client.get(endpoint)
        
        return {
            "success": True,
            "meetings": result.get("meetings", []),
            "total_records": result.get("total_records", 0),
            "page_count": result.get("page_count", 0),
            "message": "Meetings retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list meetings"
        }

async def zoom_get_meeting_participants(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get meeting participant list."""
    try:
        client = get_zoom_client()
        meeting_id = arguments.get("meeting_id")
        
        if not meeting_id:
            return {
                "success": False,
                "error": "meeting_id is required",
                "message": "Please provide a meeting ID"
            }
        
        endpoint = f"/meetings/{meeting_id}/participants"
        result = await client.get(endpoint)
        
        return {
            "success": True,
            "participants": result.get("participants", []),
            "total_records": result.get("total_records", 0),
            "message": "Meeting participants retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get meeting participants"
        }
