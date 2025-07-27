from typing import Dict, Any, Optional, List
from .base import get_notion_client, handle_notion_error, clean_notion_response


async def retrieve_block(block_id: str) -> Dict[str, Any]:
    """Retrieve a block from Notion."""
    try:
        notion = get_notion_client()
        response = notion.blocks.retrieve(block_id)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def update_block(
    block_id: str,
    block_type: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None
) -> Dict[str, Any]:
    """Update a block in Notion."""
    try:
        notion = get_notion_client()
        
        update_data = {}
        if block_type is not None:
            # The block_type should contain the specific block type and its properties
            update_data.update(block_type)
        if archived is not None:
            update_data["archived"] = archived
        
        response = notion.blocks.update(block_id, **update_data)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def delete_block(block_id: str) -> Dict[str, Any]:
    """Delete a block from Notion."""
    try:
        notion = get_notion_client()
        response = notion.blocks.delete(block_id)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def get_block_children(
    block_id: str,
    start_cursor: Optional[str] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """Retrieve children of a block."""
    try:
        notion = get_notion_client()
        
        params = {}
        if start_cursor:
            params["start_cursor"] = start_cursor
        if page_size:
            params["page_size"] = page_size
        
        response = notion.blocks.children.list(block_id, **params)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e)


async def append_block_children(
    block_id: str,
    children: List[Dict[str, Any]],
    after: Optional[str] = None
) -> Dict[str, Any]:
    """Append block children to a container block."""
    try:
        notion = get_notion_client()
        
        append_data = {"children": children}
        if after:
            append_data["after"] = after
        
        response = notion.blocks.children.append(block_id, **append_data)
        return clean_notion_response(response)
        
    except Exception as e:
        return handle_notion_error(e) 