import re

from errors import ToolExecutionError, RetryableToolError


def remove_none_values(data: dict) -> dict:
    """Remove all keys with None values from the dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def validate_ids(ids: list[str] | None, max_length: int) -> None:
    """Validate a list of IDs. The ids can be page ids, space ids, etc.

    A valid id is a string that is a number.

    Args:
        ids: A list of IDs to validate.
        max_length: Maximum number of IDs allowed.

    Returns:
        None

    Raises:
        ToolExecutionError: If any of the IDs are not valid.
        RetryableToolError: If the number of IDs is greater than the max length.
    """
    if not ids:
        return
    if len(ids) > max_length:
        raise RetryableToolError(
            message=f"The 'ids' parameter must have less than {max_length} items. Got {len(ids)}"
        )
    if any(not id_.isdigit() for id_ in ids):
        raise ToolExecutionError(message="Invalid ID provided. IDs are numeric")


def build_child_url(base_url: str, child: dict) -> str | None:
    """Build URL for a child node based on its type and status.

    Args:
        base_url: The base URL for the Confluence space
        child: A dictionary representing a Confluence content item

    Returns:
        The URL for the child, or None if it can't be determined
    """
    if child["type"] in ("whiteboard", "database", "embed"):
        return f"{base_url}/{child['type']}/{child['id']}"
    elif child["type"] == "folder":
        return None
    elif child["type"] == "page":
        parsed_title = re.sub(r"[ '\s]+", "+", child["title"].strip())
        if child.get("status") == "draft":
            return f"{base_url}/{child['type']}s/edit-v2/{child['id']}"
        else:
            return f"{base_url}/{child['type']}s/{child['id']}/{parsed_title}"
    return None


def build_hierarchy(transformed_children: list, parent_id: str, parent_node: dict) -> None:
    """Build parent-child hierarchy from a flat list of descendants.

    This function takes a flat list of items that have parent_id references and
    builds a hierarchical tree structure. It modifies the parent_node in place.

    Args:
        transformed_children: List of child nodes with parent_id fields
        parent_id: The ID of the parent node
        parent_node: The parent node to attach direct children to

    Returns:
        None (modifies parent_node in place)
    """
    # Create a map of children by their ID for efficient lookups
    child_map = {child["id"]: child for child in transformed_children}

    # Find all direct children of the given parent_id
    direct_children = []
    for child in transformed_children:
        if child.get("parent_id") == parent_id:
            direct_children.append(child)
        elif child.get("parent_id") in child_map:
            # Add child to its parent's children list
            parent = child_map[child.get("parent_id")]
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(child)

    # Set the direct children on the parent node
    parent_node["children"] = direct_children 