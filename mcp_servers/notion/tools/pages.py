from typing import Dict, Any, Optional, List
from .base import get_notion_client, handle_notion_error, clean_notion_response


async def create_page(
    parent: Dict[str, Any],
    properties: Dict[str, Any],
    children: Optional[List[Dict[str, Any]]] = None,
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new page in Notion."""
    try:
        notion = get_notion_client()
        
        page_data = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            page_data["children"] = children
        if icon:
            page_data["icon"] = icon
        if cover:
            page_data["cover"] = cover
        
        response = notion.pages.create(**page_data)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def get_page(
    page_id: str,
    filter_properties: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Retrieve a page from Notion."""
    try:
        notion = get_notion_client()
        
        params = {}
        if filter_properties:
            params["filter_properties"] = filter_properties
        
        response = notion.pages.retrieve(page_id, **params)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def retrieve_page_property(
    page_id: str,
    property_id: str,
    start_cursor: Optional[str] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """Retrieve a specific property from a page."""
    try:
        notion = get_notion_client()
        
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = notion.pages.properties.retrieve(page_id, property_id, **params)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def update_page_properties(
    page_id: str,
    properties: Dict[str, Any],
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
    in_trash: Optional[bool] = None
) -> Dict[str, Any]:
    """Update properties of a page."""
    try:
        notion = get_notion_client()
        
        update_data = {"properties": properties}
        
        if icon is not None:
            update_data["icon"] = icon
        if cover is not None:
            update_data["cover"] = cover
        if archived is not None:
            update_data["archived"] = archived
        if in_trash is not None:
            update_data["in_trash"] = in_trash
        
        response = notion.pages.update(page_id, **update_data)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e) 