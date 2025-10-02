from .base import get_trello_client

async def get_board_lists(board_id: str):
    """Fetches all lists in a specific board."""
    client = get_trello_client()
    return await client.make_request("GET", f"/boards/{board_id}/lists")
