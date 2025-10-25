from .base import make_graph_api_request

async def create_online_meeting(user_id: str, subject: str, start_datetime: str, end_datetime: str):
    """Schedules a new online meeting for a specific user."""
    payload = {
        "subject": subject,
        "startDateTime": start_datetime,
        "endDateTime": end_datetime
    }
    return await make_graph_api_request("POST", f"/users/{user_id}/onlineMeetings", json_data=payload)

async def list_online_meetings(user_id: str):
    """Lists all online meetings for a specific user."""
    return await make_graph_api_request("GET", f"/users/{user_id}/onlineMeetings")