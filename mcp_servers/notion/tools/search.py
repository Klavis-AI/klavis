from typing import Dict, Any, Optional
from .base import get_notion_client, handle_notion_error, clean_notion_response


async def search_notion(
    query: Optional[str] = None,
    sort: Optional[Dict[str, Any]] = None,
    filter_conditions: Optional[Dict[str, Any]] = None,
    start_cursor: Optional[str] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """Search for pages and databases in Notion."""
    try:
        notion = get_notion_client()
        
        search_params = {}
        if query:
            search_params["query"] = query
        if sort:
            search_params["sort"] = sort
        if filter_conditions:
            search_params["filter"] = filter_conditions
        if start_cursor:
            search_params["start_cursor"] = start_cursor
        if page_size:
            search_params["page_size"] = page_size
        
        response = notion.search(**search_params)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e) 