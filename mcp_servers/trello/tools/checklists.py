from .base import get_trello_client

async def create_checklist(idCard: str, name: str):
    """Creates a new checklist on a specific card."""
    client = get_trello_client()
    return await client.make_request("POST", f"/cards/{idCard}/checklists", params={"name": name})

async def add_item_to_checklist(idChecklist: str, name: str, checked: bool = False):
    """Adds a new item to a specific checklist."""
    client = get_trello_client()
    params = {"name": name, "checked": checked}
    return await client.make_request("POST", f"/checklists/{idChecklist}/checkItems", params=params)

async def update_checklist_item_state(idCard: str, idCheckItem: str, state: str):
    """Updates the state of an item on a checklist (e.g., 'complete' or 'incomplete')."""
    client = get_trello_client()
    # Note: The endpoint for updating a checkitem is unusual and requires the card ID.
    # It's PUT /1/cards/{idCard}/checkItem/{idCheckItem}
    return await client.make_request("PUT", f"/cards/{idCard}/checkItem/{idCheckItem}", params={"state": state})
