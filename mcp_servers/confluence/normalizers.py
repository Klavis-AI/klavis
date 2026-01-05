"""
Normalizers for Confluence API responses.

This module provides Klavis-defined abstractions for transforming raw vendor API
responses into normalized schemas. These normalizers ensure that:
- Raw vendor responses are never exposed directly
- Vendor-specific field names are mapped to Klavis-defined names
- The output follows Klavis Interface conventions
"""

from typing import Any, Dict


def get_path(data: Dict, path: str) -> Any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: Dict, mapping: Dict[str, Any]) -> Dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    
    Args:
        source: Raw vendor JSON.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# =============================================================================
# Klavis Normalization Rules for Confluence Entities
# =============================================================================

# Version information rules
VERSION_RULES = {
    "number": "number",
    "message": "message",
    "createdAt": "createdAt",
    "authorId": "authorId",
    "isMinorEdit": "minorEdit",
}

# Page entity rules - maps Confluence API fields to Klavis fields
PAGE_RULES = {
    "id": "id",
    "title": "title",
    "type": "type",
    "status": "status",
    "spaceId": "spaceId",
    "parentId": "parentId",
    "parentType": "parentType",
    "position": "position",
    "authorId": "authorId",
    "ownerId": "ownerId",
    "createdAt": "createdAt",
    # Nested body content - handled specially
    "body": lambda x: x.get("body") if x.get("body") else None,
    # Version info - normalized
    "version": lambda x: normalize(x.get("version", {}), VERSION_RULES) if x.get("version") else None,
}

# Space entity rules
SPACE_RULES = {
    "id": "id",
    "key": "key",
    "name": "name",
    "type": "type",
    "status": "status",
    "authorId": "authorId",
    "createdAt": "createdAt",
    "homepageId": "homepageId",
    # Description - extract plain text value
    "description": lambda x: get_path(x, "description.plain.value"),
    # Icon path
    "iconPath": lambda x: get_path(x, "icon.path"),
}

# Attachment entity rules
ATTACHMENT_RULES = {
    "id": "id",
    "title": "title",
    "status": "status",
    "mediaType": "mediaType",
    "mediaTypeDescription": "mediaTypeDescription",
    "comment": "comment",
    "fileId": "fileId",
    "fileSize": "fileSize",
    "pageId": "pageId",
    "createdAt": "createdAt",
    # Version info - normalized
    "version": lambda x: normalize(x.get("version", {}), VERSION_RULES) if x.get("version") else None,
}

# Search result rules (v1 API)
SEARCH_RESULT_RULES = {
    "id": "content.id",
    "title": "content.title",
    "type": "content.type",
    "status": "content.status",
    "excerpt": "excerpt",
}

# Tree node rules for hierarchy
TREE_NODE_RULES = {
    "id": "id",
    "title": "title",
    "type": "type",
    "status": "status",
}


def normalize_page(raw_page: Dict, url: str | None = None) -> Dict:
    """Normalize a single page response."""
    page = normalize(raw_page, PAGE_RULES)
    # Default type to "page" if not present (v2 API doesn't include type for pages)
    if "type" not in page:
        page["type"] = "page"
    if url:
        page["url"] = url
    return page


def normalize_space(raw_space: Dict, url: str | None = None) -> Dict:
    """Normalize a single space response."""
    space = normalize(raw_space, SPACE_RULES)
    if url:
        space["url"] = url
    return space


def normalize_attachment(raw_attachment: Dict, url: str | None = None, download_link: str | None = None) -> Dict:
    """Normalize a single attachment response."""
    attachment = normalize(raw_attachment, ATTACHMENT_RULES)
    if url:
        attachment["url"] = url
    if download_link:
        attachment["downloadLink"] = download_link
    return attachment


def normalize_search_result(raw_result: Dict, url: str | None = None) -> Dict:
    """Normalize a single search result."""
    result = normalize(raw_result, SEARCH_RESULT_RULES)
    if url:
        result["url"] = url
    return result


def normalize_tree_node(raw_node: Dict, url: str | None = None) -> Dict:
    """Normalize a tree node for hierarchy responses."""
    node = normalize(raw_node, TREE_NODE_RULES)
    if url:
        node["url"] = url
    node["children"] = []
    return node

