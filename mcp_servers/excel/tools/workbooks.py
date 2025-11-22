import logging
from typing import Any, Dict
from urllib.parse import quote

import httpx

from .base import get_excel_client, parse_share_link
from .utils import (
    SheetDataParseError,
    build_workbook_bytes,
    format_api_error,
    parse_sheet_data,
    sanitize_workbook_name,
)

logger = logging.getLogger(__name__)

EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def excel_create_workbook(
    title: str,
    data: Any | None = None,
    sheet_name: str | None = None,
    parent_link: str | None = None,
) -> Dict[str, Any]:
    """
    Create a new Excel workbook in OneDrive or SharePoint using Microsoft Graph.

    Args:
        title: Desired workbook title. The `.xlsx` extension is added automatically.
        data: Optional JSON/dict mapping of row -> {column -> value} to seed the workbook.
        sheet_name: Optional name for the first worksheet.
        parent_link: Optional share link to the folder where the workbook should be created.
                     If not specified, creates in the root of the user's personal OneDrive.

    Returns:
        Metadata about the created workbook from Microsoft Graph.
    """
    client = get_excel_client()
    if not client:
        raise RuntimeError("Unable to initialize Excel client")

    try:
        parsed_data = parse_sheet_data(data)
    except SheetDataParseError as exc:
        raise RuntimeError(str(exc)) from exc

    workbook_bytes = build_workbook_bytes(parsed_data, sheet_title=sheet_name)
    filename = sanitize_workbook_name(title)
    encoded_filename = quote(filename)

    # Parse parent_link to get drive_id and parent_item_id if provided
    if parent_link:
        parent_info = await parse_share_link(parent_link, client)
        parent_item_id = parent_info.get("id")
        parent_ref = parent_info.get("parentReference", {})
        drive_id = parent_ref.get("driveId")

        if not parent_item_id or not drive_id:
            raise RuntimeError("Failed to extract drive ID and item ID from parent link")

        path = f"/drives/{drive_id}/items/{parent_item_id}/children/{encoded_filename}"
    else:
        # Personal OneDrive root
        path = f"/me/drive/root/children/{encoded_filename}"

    url = f"{client['base_url']}{path}/content"
    params = {"@microsoft.graph.conflictBehavior": "rename"}

    headers = {
        **client["headers"],
        "Content-Type": EXCEL_MIME_TYPE,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            response = await httpx_client.put(
                url, headers=headers, params=params, content=workbook_bytes
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_detail = format_api_error(exc.response.status_code, exc.response.text)
        logger.error("Excel workbook creation failed: %s", exc.response.text)
        raise RuntimeError(
            f"Excel API returned {exc.response.status_code}: {error_detail}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error creating workbook")
        raise RuntimeError(f"Failed to create workbook: {exc}") from exc

    item = response.json()
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "webUrl": item.get("webUrl"),
        "size": item.get("size"),
        "createdDateTime": item.get("createdDateTime"),
        "lastModifiedDateTime": item.get("lastModifiedDateTime"),
        "parentReference": item.get("parentReference"),
    }


__all__ = ["excel_create_workbook"]
