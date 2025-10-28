from typing import Annotated

from client import ConfluenceClientV2
from enums import BodyFormat, PageSortOrder, PageUpdateMode
from errors import ToolExecutionError
from utils import remove_none_values, validate_ids


async def create_page(
    space_identifier: Annotated[str, "The ID or title of the space to create the page in"],
    title: Annotated[str, "The title of the page"],
    content: Annotated[str, "The content of the page. Only plain text is supported"],
    parent_id: Annotated[
        str | None,
        "The ID of the parent. If not provided, the page will be created at the root of the space.",
    ] = None,
    is_private: Annotated[
        bool,
        "If true, then only the user who creates this page will be able to see it. "
        "Defaults to False",
    ] = False,
    is_draft: Annotated[
        bool,
        "If true, then the page will be created as a draft. Defaults to False",
    ] = False,
) -> Annotated[dict, "The page"]:
    """Create a new page at the root of the given space."""
    client = ConfluenceClientV2()
    space_id = await client.get_space_id(space_identifier)

    parent_id = parent_id or (await client.get_space_homepage(space_id)).get("id")
    params = remove_none_values({
        "root-level": False,
        "private": is_private,
    })

    body = remove_none_values({
        "spaceId": space_id,
        "status": "draft" if is_draft else None,
        "parentId": parent_id,
        "title": title,
        "body": {
            "storage": {
                "value": content,
                "representation": BodyFormat.STORAGE.to_api_value(),
            }
        },
    })
    page = await client.post("pages", params=params, json=body)
    return client.transform_page_response(page)


async def update_page_content(
    page_identifier: Annotated[
        str, "The ID or title of the page to update. Numerical titles are NOT supported."
    ],
    content: Annotated[str, "The content of the page. Only plain text is supported"],
    update_mode: Annotated[
        PageUpdateMode,
        "The mode of update. Defaults to 'append'.",
    ] = PageUpdateMode.APPEND,
) -> Annotated[dict, "The page"]:
    """Update a page's content."""
    # Get the page to update
    client = ConfluenceClientV2()
    page_id = await client.get_page_id(page_identifier)

    page = await get_page(page_identifier)
    if not page.get("page"):
        raise ToolExecutionError(message=f"No page found with identifier: '{page_identifier}'")
    status = page.get("page", {}).get("status", "current")
    title = page.get("page", {}).get("title", "Untitled page")
    body = page.get("page", {}).get("body", {})
    old_content = body.get(BodyFormat.STORAGE, {}).get("value", "")
    old_version_number = page.get("page", {}).get("version", {}).get("number", 0)

    # Update the page content
    payload = client.prepare_update_page_content_payload(
        content=content,
        update_mode=update_mode,
        old_content=old_content,
        page_id=page_id,
        status=status,
        title=title,
        body_representation=BodyFormat.STORAGE,
        old_version_number=old_version_number,
    )
    updated_page = await client.put(f"pages/{page_id}", json=payload)

    return client.transform_page_response(updated_page)


async def rename_page(
    page_identifier: Annotated[
        str, "The ID or title of the page to rename. Numerical titles are NOT supported."
    ],
    title: Annotated[str, "The title of the page"],
) -> Annotated[dict, "The page"]:
    """Rename a page by changing its title."""
    # Get the page to rename
    client = ConfluenceClientV2()
    page_id = await client.get_page_id(page_identifier)

    page = await get_page(page_identifier)
    if not page.get("page"):
        raise ToolExecutionError(message=f"No page found with identifier: '{page_identifier}'")
    status = page.get("page", {}).get("status", "current")
    content = page.get("page", {}).get("body", {}).get(BodyFormat.STORAGE, {}).get("value", "")
    old_version_number = page.get("page", {}).get("version", {}).get("number", 0)

    # Rename the page
    payload = client.prepare_update_page_payload(
        page_id=page_id,
        status=status,
        title=title,
        body_representation=BodyFormat.STORAGE,
        body_value=content,
        version_number=old_version_number + 1,
        version_message="Rename the page",
    )
    updated_page = await client.put(f"pages/{page_id}", json=payload)

    return client.transform_page_response(updated_page)


async def get_page(
    page_identifier: Annotated[
        str, "Can be a page's ID or title. Numerical titles are NOT supported."
    ],
) -> Annotated[dict, "The page"]:
    """Retrieve a SINGLE page's content by its ID or title.

    If a title is provided, then the first page with an exact matching title will be returned.

    IMPORTANT: For retrieving MULTIPLE pages, use `get_pages_by_id` instead
    for a massive performance and efficiency boost. If you call this function multiple times
    instead of using `get_pages_by_id`, then the universe will explode.
    """
    client = ConfluenceClientV2()
    if page_identifier.isdigit():
        return await client.get_page_by_id(page_identifier, BodyFormat.STORAGE)
    else:
        return await client.get_page_by_title(page_identifier, BodyFormat.STORAGE)


async def get_pages_by_id(
    page_ids: Annotated[
        list[str],
        "The IDs of the pages to get. IDs are numeric. Titles of pages are NOT supported. "
        "Maximum of 250 page ids supported.",
    ],
) -> Annotated[dict, "The pages"]:
    """Get the content of MULTIPLE pages by their ID in a single efficient request.

    IMPORTANT: Always use this function when you need to retrieve content from more than one page,
    rather than making multiple separate calls to get_page, because this function is significantly
    more efficient than calling get_page multiple times.
    """
    validate_ids(page_ids, max_length=250)
    client = ConfluenceClientV2()
    pages = await client.get(
        "pages", params={"id": page_ids, "body-format": BodyFormat.STORAGE.to_api_value()}
    )
    return client.transform_get_multiple_pages_response(pages)


async def list_pages(
    space_ids: Annotated[
        list[str] | None,
        "Restrict the response to only include pages in these spaces. "
        "Only space IDs are supported. Titles of spaces are NOT supported. "
        "If not provided, then no restriction is applied. "
        "Maximum of 100 space ids supported.",
    ] = None,
    sort_by: Annotated[
        PageSortOrder | None,
        "The order of the pages to sort by. Defaults to created-date-newest-to-oldest",
    ] = None,
    limit: Annotated[int, "The maximum number of pages to return. Defaults to 25. Max is 250"] = 25,
    pagination_token: Annotated[
        str | None,
        "The pagination token to use for the next page of results",
    ] = None,
) -> Annotated[dict, "The pages"]:
    """Get the content of multiple pages by their ID"""
    validate_ids(space_ids, max_length=100)
    limit = max(1, min(limit, 250))
    client = ConfluenceClientV2()
    
    # Handle sort_by - use default if None
    if sort_by is None:
        sort_by = PageSortOrder.CREATED_DATE_DESCENDING
    
    params = remove_none_values({
        "space-id": space_ids,
        "sort": sort_by.to_api_value(),
        "body-format": BodyFormat.STORAGE.to_api_value(),
        "limit": limit,
    })
    
    # Only add cursor parameter if pagination_token has a value
    if pagination_token:
        params["cursor"] = pagination_token
    pages = await client.get("pages", params=params)
    return client.transform_list_pages_response(pages)


 