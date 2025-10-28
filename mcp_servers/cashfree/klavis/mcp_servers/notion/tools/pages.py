from typing import Dict, Any, Optional, List
import re
from .base import get_notion_client, handle_notion_error, clean_notion_response


def markdown_to_notion_blocks(markdown_content: str) -> List[Dict[str, Any]]:
    """Convert markdown content to Notion block format."""
    blocks = []
    lines = markdown_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
            
        # Headers
        if line.startswith('#'):
            header_match = re.match(r'^(#{1,3})\s+(.+)', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                block_type = ['heading_1', 'heading_2', 'heading_3'][level - 1]
                blocks.append({
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": text}
                        }]
                    }
                })
                i += 1
                continue
        
        # Code blocks
        if line.startswith('```'):
            code_lines = []
            language = line[3:].strip() or "plain text"
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": '\n'.join(code_lines)}
                    }],
                    "language": language
                }
            })
            i += 1
            continue
            
        # Bullet lists
        if line.startswith('- ') or line.startswith('* '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[2:].strip()}
                    }]
                }
            })
            i += 1
            continue
            
        # Numbered lists
        numbered_match = re.match(r'^\d+\.\s+(.+)', line)
        if numbered_match:
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": numbered_match.group(1)}
                    }]
                }
            })
            i += 1
            continue
            
        # Regular paragraphs
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": line}
                }]
            }
        })
        i += 1
    
    return blocks


async def create_page(
    page: Optional[Dict[str, Any]] = None,
    parent: Optional[Dict[str, Any]] = None,
    properties: Optional[Dict[str, Any]] = None,
    children: Optional[List[Dict[str, Any]]] = None,
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new page in Notion with support for both old and new input formats.
    
    New format:
    - page: Contains content (markdown) and properties (with title)
    - parent: Contains page_id, database_id, or workspace (optional - defaults to private page)
    
    Old format:
    - properties: Direct properties dict
    - parent: Parent object (optional - defaults to private page)
    - children: Optional blocks
    
    If parent is not specified or cannot be found, a private page will be created in the workspace.
    """
    try:
        notion = get_notion_client()
        
        # Handle new format with page object
        if page:
            # Extract and convert content to blocks if provided
            if page.get('content'):
                children = markdown_to_notion_blocks(page['content'])
            
            # Extract properties and format title
            if page.get('properties'):
                page_props = page['properties']
                if 'title' in page_props:
                    # Convert simple title string to Notion title property format
                    properties = {
                        "title": {
                            "title": [{
                                "type": "text",
                                "text": {"content": page_props['title']}
                            }]
                        }
                    }
                    # Add any other properties from page_props
                    for key, value in page_props.items():
                        if key != 'title':
                            properties[key] = value
                else:
                    properties = page_props
        
        # Ensure we have properties
        if not properties:
            raise ValueError("Properties are required")
        
        # If parent is not specified, create a private page (workspace-level)
        if not parent:
            parent = {"workspace": True}
        
        # Build the page data
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