from typing import Optional
from .base import get_trello_client

async def get_my_boards():
    """Fetches all boards that the user is a member of."""
    client = get_trello_client()
    return await client.make_request("GET", "/members/me/boards")

async def create_board(name: str, desc: Optional[str] = None):
    """Creates a new board in Trello."""
    client = get_trello_client()
    json_data = {"name": name}
    if desc:
        json_data["desc"] = desc
    return await client.make_request("POST", "/boards", json=json_data)
