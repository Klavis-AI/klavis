from typing import Annotated

from client import ConfluenceClientV2
from enums import AttachmentSortOrder
from utils import remove_none_values


async def get_attachments_for_page(
    page_identifier: Annotated[str, "The ID or title of the page to get attachments for"],
    limit: Annotated[
        int, "The maximum number of attachments to return. Defaults to 25. Max is 250"
    ] = 25,
    pagination_token: Annotated[
        str | None,
        "The pagination token to use for the next page of results",
    ] = None,
) -> Annotated[dict, "The attachments"]:
    """Get attachments for a page by its ID or title.

    If a page title is provided, then the first page with an exact matching title will be returned.
    """
    client = ConfluenceClientV2()
    page_id = await client.get_page_id(page_identifier)

    params = remove_none_values({
        "limit": max(1, min(limit, 250)),
    })
    
    # Only add cursor parameter if pagination_token has a value
    if pagination_token:
        params["cursor"] = pagination_token
    attachments = await client.get(f"pages/{page_id}/attachments", params=params)
    return client.transform_get_attachments_response(attachments)


async def list_attachments(
    sort_order: Annotated[
        AttachmentSortOrder | None,
        "The order of the attachments to sort by. Defaults to created-date-newest-to-oldest",
    ] = None,
    limit: Annotated[
        int, "The maximum number of attachments to return. Defaults to 25. Max is 250"
    ] = 25,
    pagination_token: Annotated[
        str | None,
        "The pagination token to use for the next page of results",
    ] = None,
) -> Annotated[dict, "The attachments"]:
    """List attachments in a workspace"""
    client = ConfluenceClientV2()
    
    # Handle sort_order - use default if None
    if sort_order is None:
        sort_order = AttachmentSortOrder.CREATED_DATE_DESCENDING
    
    params = remove_none_values({
        "sort": sort_order.to_api_value(),
        "limit": max(1, min(limit, 250)),
    })
    
    # Only add cursor parameter if pagination_token has a value
    if pagination_token:
        params["cursor"] = pagination_token
    attachments = await client.get("attachments", params=params)
    return client.transform_get_attachments_response(attachments)


async def get_attachment(
    attachment_id: Annotated[str, "The ID of the attachment to get"],
) -> Annotated[dict, "The attachment"]:
    """Get a specific attachment by its ID"""
    client = ConfluenceClientV2()
    
    response = await client.get(f"attachments/{attachment_id}")
    return client.transform_attachment_response(response) 