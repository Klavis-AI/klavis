import logging
from typing import Any, Dict, Optional

import httpx

from .base import get_excel_client, parse_workbook_url
from .utils import format_api_error

logger = logging.getLogger(__name__)


async def excel_list_worksheets(workbook_url: str) -> Dict[str, Any]:
    """
    List worksheets contained within the specified Excel workbook.
    Supports both OneDrive and SharePoint workbooks.

    Args:
        workbook_url: The shared URL of the Excel workbook
    """
    client = get_excel_client()
    if not client:
        raise RuntimeError("Unable to initialize Excel client")

    # Parse the workbook URL to get the workbook item information
    target_item_info = await parse_workbook_url(workbook_url, client)
    workbook_item_id = target_item_info.get("id")

    if not workbook_item_id:
        raise RuntimeError("Failed to extract workbook ID from workbook URL")

    # Extract parent reference to determine the drive path
    parent_ref = target_item_info.get("parentReference", {})
    drive_id = parent_ref.get("driveId")
    drive_type_raw = parent_ref.get("driveType", "unknown")

    if not drive_id:
        raise RuntimeError("Failed to extract drive ID from shared URL")

    # Construct the drive path
    drive_path = f"/drives/{drive_id}"
    drive_type = "sharepoint" if drive_type_raw == "documentLibrary" else "personal"

    url = (
        f"{client['base_url']}{drive_path}/items/"
        f"{workbook_item_id}/workbook/worksheets"
    )

    params = {
        "$select": "id,name,position,visibility",
        "$orderby": "position",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            response = await httpx_client.get(url, headers=client["headers"], params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_detail = format_api_error(exc.response.status_code, exc.response.text)
        logger.error("Excel worksheet listing failed: %s", exc.response.text)
        raise RuntimeError(
            f"Excel API returned {exc.response.status_code}: {error_detail}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error listing worksheets")
        raise RuntimeError(f"Failed to list worksheets: {exc}") from exc

    payload = response.json()
    worksheets = payload.get("value", [])

    formatted = [
        {
            "id": sheet.get("id"),
            "name": sheet.get("name"),
            "position": sheet.get("position"),
            "visibility": sheet.get("visibility"),
        }
        for sheet in worksheets
    ]

    return {
        "workbook_id": workbook_item_id,
        "drive_type": drive_type,
        "worksheets": formatted,
        "total_count": len(formatted),
    }


async def fetch_first_worksheet(
    httpx_client: httpx.AsyncClient,
    client_headers: Dict[str, str],
    base_url: str,
    workbook_item_id: str,
    drive_path: str = "/me/drive",
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the first worksheet (position == 0) for the specified workbook.

    Returns the worksheet JSON object or None if not found.
    """
    url = (
        f"{base_url}{drive_path}/items/{workbook_item_id}"
        "/workbook/worksheets"
    )
    params = {
        "$select": "id,name,position,visibility",
        "$orderby": "position",
        "$top": 1,
    }
    response = await httpx_client.get(url, headers=client_headers, params=params)
    response.raise_for_status()
    items = response.json().get("value", [])
    return items[0] if items else None


async def fetch_named_worksheet(
    httpx_client: httpx.AsyncClient,
    client_headers: Dict[str, str],
    base_url: str,
    workbook_item_id: str,
    worksheet_name: str,
    drive_path: str = "/me/drive",
) -> Optional[Dict[str, Any]]:
    """
    Retrieve worksheet metadata by name.
    """
    escaped_name = worksheet_name.replace("'", "''")
    url = (
        f"{base_url}{drive_path}/items/{workbook_item_id}"
        f"/workbook/worksheets('{escaped_name}')"
    )
    params = {"$select": "id,name,position,visibility"}
    response = await httpx_client.get(url, headers=client_headers, params=params)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def fetch_worksheet_by_id(
    httpx_client: httpx.AsyncClient,
    client_headers: Dict[str, str],
    base_url: str,
    workbook_item_id: str,
    worksheet_id: str,
    drive_path: str = "/me/drive",
) -> Optional[Dict[str, Any]]:
    """
    Retrieve worksheet metadata by ID.
    """
    url = (
        f"{base_url}{drive_path}/items/{workbook_item_id}"
        f"/workbook/worksheets/{worksheet_id}"
    )
    params = {"$select": "id,name,position,visibility"}
    response = await httpx_client.get(url, headers=client_headers, params=params)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


__all__ = [
    "excel_list_worksheets",
    "fetch_first_worksheet",
    "fetch_named_worksheet",
    "fetch_worksheet_by_id",
]
