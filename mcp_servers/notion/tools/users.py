from typing import Dict, Any, Optional
from .base import get_notion_client, handle_notion_error, clean_notion_response


async def get_user(user_id: str) -> Dict[str, Any]:
    """Retrieve a user from Notion."""
    try:
        notion = get_notion_client()
        response = notion.users.retrieve(user_id)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def get_me() -> Dict[str, Any]:
    """Retrieve your token's bot user information."""
    try:
        notion = get_notion_client()
        response = notion.users.me()
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def list_users(
    start_cursor: Optional[str] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """List all users in the workspace."""
    try:
        notion = get_notion_client()
        
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = notion.users.list(**params)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


 