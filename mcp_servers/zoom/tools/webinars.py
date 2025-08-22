import json
from typing import Dict, Any
from .auth import get_zoom_client

async def zoom_create_webinar(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Zoom webinar."""
    try:
        client = get_zoom_client()
        
        # Extract required and optional parameters
        user_id = arguments.get("user_id", "me")  # Default to current user
        topic = arguments.get("topic", "New Webinar")
        webinar_type = arguments.get("type", 5)  # 5 = scheduled webinar
        
        # Build webinar data
        webinar_data = {
            "topic": topic,
            "type": webinar_type,
            "start_time": arguments.get("start_time"),
            "duration": arguments.get("duration", 60),
            "timezone": arguments.get("timezone", "UTC"),
            "password": arguments.get("password"),
            "settings": {
                "host_video": arguments.get("host_video", True),
                "panelists_video": arguments.get("panelists_video", True),
                "practice_session": arguments.get("practice_session", False),
                "hd_video": arguments.get("hd_video", True),
                "audio": arguments.get("audio", "both"),
                "auto_recording": arguments.get("auto_recording", "none"),
                "alternative_hosts": arguments.get("alternative_hosts"),
                "close_registration": arguments.get("close_registration", False),
                "show_share_button": arguments.get("show_share_button", True),
                "allow_multiple_devices": arguments.get("allow_multiple_devices", False),
                "on_demand": arguments.get("on_demand", False),
                "global_dial_in_countries": arguments.get("global_dial_in_countries", []),
                "contact_name": arguments.get("contact_name"),
                "contact_email": arguments.get("contact_email"),
                "registrants_restrict_number": arguments.get("registrants_restrict_number", False),
                "registrants_email_notification": arguments.get("registrants_email_notification", True)
            }
        }
        
        # Remove None values
        webinar_data = {k: v for k, v in webinar_data.items() if v is not None}
        if "settings" in webinar_data:
            webinar_data["settings"] = {k: v for k, v in webinar_data["settings"].items() if v is not None}
        
        endpoint = f"/users/{user_id}/webinars"
        result = await client.post(endpoint, webinar_data)
        
        return {
            "success": True,
            "webinar": result,
            "message": f"Webinar '{topic}' created successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create webinar"
        }
