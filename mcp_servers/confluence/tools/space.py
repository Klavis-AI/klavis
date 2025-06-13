import re
from typing import Annotated

from client import ConfluenceClientV2
from utils import remove_none_values


async def get_space(
    space_identifier: Annotated[
        str, "Can be a space's ID or key. Numerical keys are NOT supported"
    ],
) -> Annotated[dict, "The space"]:
    """Get the details of a space by its ID or key."""
    client = ConfluenceClientV2()
    if space_identifier.isdigit():
        return await client.get_space_by_id(space_identifier)
    else:
        return await client.get_space_by_key(space_identifier)


async def list_spaces(
    limit: Annotated[
        int, "The maximum number of spaces to return. Defaults to 25. Max is 250"
    ] = 25,
    pagination_token: Annotated[
        str | None, "The pagination token to use for the next page of results"
    ] = None,
) -> Annotated[dict, "The spaces"]:
    """List all spaces sorted by name in ascending order."""
    client = ConfluenceClientV2()
    params = {"limit": max(1, min(limit, 250)), "sort": "name"}
    
    # Only add cursor parameter if pagination_token has a value
    if pagination_token:
        params["cursor"] = pagination_token
    spaces = await client.get("spaces", params=params)
    return client.transform_get_spaces_response(spaces)


async def get_space_hierarchy(
    space_identifier: Annotated[
        str, "Can be a space's ID or key. Numerical keys are NOT supported"
    ],
) -> Annotated[dict, "The space hierarchy"]:
    """Retrieve the full hierarchical structure of a Confluence space as a tree structure

    Only structural metadata is returned (not content).
    The response is akin to the sidebar in the Confluence UI.

    Includes all pages, folders, whiteboards, databases,
    smart links, etc. organized by parent-child relationships.
    """
    client = ConfluenceClientV2()

    space = await client.get_space(space_identifier)
    tree = client.create_space_tree(space)

    # Get root pages
    root_pages = await client.get_root_pages_in_space(space["space"]["id"])
    tree["children"] = client.convert_root_pages_to_tree_nodes(root_pages["pages"])

    if not tree["children"]:
        return tree

    # Extract base URL for children URLs. The base URL is the space's URL.
    root_page_url = tree["url"]
    match = re.match(r"(.*?/spaces/[^/]+)", root_page_url)
    children_base_url = match.group(1) if match else ""

    # Get descendants for each root page
    await client.process_page_descendants(tree["children"], children_base_url)

    return tree


 