from typing import Optional
from .base import get_trello_client

async def get_list_cards(list_id: str):
    """Fetches all cards in a specific list."""
    client = get_trello_client()
    return await client.make_request("GET", f"/lists/{list_id}/cards")

async def create_card(idList: str, name: str, desc: Optional[str] = None):
    """Creates a new card in a specific list."""
    client = get_trello_client()
    json_data = {
        "idList": idList,
        "name": name,
    }
    if desc:
        json_data["desc"] = desc
    return await client.make_request("POST", "/cards", json=json_data)

async def update_card(card_id: str, name: Optional[str] = None, desc: Optional[str] = None, idList: Optional[str] = None):
    """Updates a card in Trello."""
    client = get_trello_client()
    json_data = {}
    if name:
        json_data["name"] = name
    if desc:
        json_data["desc"] = desc
    if idList:
        json_data["idList"] = idList
    return await client.make_request("PUT", f"/cards/{card_id}", json=json_data)

async def delete_card(card_id: str):
    """Deletes a card in Trello."""
    client = get_trello_client()
    return await client.make_request("DELETE", f"/cards/{card_id}")
