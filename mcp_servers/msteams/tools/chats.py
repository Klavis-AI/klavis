
from .base import make_graph_api_request

async def list_chats():
    """Lists all 1-on-1 and group chats the app has access to."""
    return await make_graph_api_request("GET", "/chats")

async def send_chat_message(chat_id: str, message: str):
    """Sends a message to a specific chat."""
    payload = {"body": {"content": message}}
    return await make_graph_api_request("POST", f"/chats/{chat_id}/messages", json_data=payload)
