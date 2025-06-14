import re
from typing import Annotated

from client import ConfluenceClientV1
from client import ConfluenceClientV2
from errors import ToolExecutionError 


async def create_space(
    name: Annotated[str, "The name of the space"],
    key: Annotated[str | None, "The key of the space. If not provided, one will be generated automatically"] = None,
    description: Annotated[str | None, "The description of the space"] = None,
    is_private: Annotated[bool, "If true, the space will be private to the creator. Defaults to False"] = False,
) -> Annotated[dict, "The created space"]:
    """Create a new space in Confluence.
    
    Creates a new space with the specified name, key, and description.
    The space can be either public (default) or private to the creator.
    """
    # Use V2 API for space creation as it's the current standard
    client = ConfluenceClientV2()
    
    # Prepare the space data according to v2 API format
    space_data = {
        "name": name,
    }
    
    # Automatically generate a space key if one is not provided. A Confluence space key
    # must be 1-255 characters long and only contain upper-case letters and numbers.
    # We generate it by taking the first character of each word in the space name and
    # falling back to the first 3 alphanumeric characters when the result is too short.
    if key is None:
        # Remove any character that is not a letter or number and split the words
        words = re.findall(r"[A-Za-z0-9]+", name)
        generated_key = "".join(word[0] for word in words).upper()
        if len(generated_key) < 3:
            generated_key = re.sub(r"[^A-Za-z0-9]", "", name.upper())[:3]
        key = generated_key[:50]  # keep it short but well within 255-char limit

    # Add key (generated or provided by the caller)
    space_data["key"] = key
    
    # Add description if provided (v2 API format)
    if description:
        space_data["description"] = {
            "value": description,
            "representation": "plain"
        }
    
    # Note: v2 API doesn't have a separate private space endpoint
    # Private spaces are created through roleAssignments or permissions
    if is_private:
        # For private spaces, we'll create a regular space and note the limitation
        # The user will need to set permissions manually or through the UI
        pass
    
    # Create the space using v2 API endpoint
    try:
        response = await client.post("spaces", json=space_data)
    except Exception as e:
        # If the v2 API returns 403 Forbidden (which can happen on some tenants)
        # fall back to the older v1 endpoint.
        print(f"--- error: {e}, falling back to v1 endpoint")
        if isinstance(e, ToolExecutionError) and "HTTP 403" in str(e):
            client_v1 = ConfluenceClientV1()
            v1_data = {
                "key": key,
                "name": name,
            }
            if description:
                v1_data["description"] = {
                    "plain": {
                        "value": description,
                        "representation": "plain",
                    }
                }
            response = await client_v1.post("space", json=v1_data)
        else:
            raise
            
    # Transform the response to match our format
    space_copy = response.copy()
    
    # Add URL if available from _links
    if "_links" in space_copy and "webui" in space_copy["_links"]:
        space_copy["url"] = space_copy["_links"]["webui"]
    
    # Clean up _links if present
    if "_links" in space_copy:
        del space_copy["_links"]
    
    return {"space": space_copy}


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


 