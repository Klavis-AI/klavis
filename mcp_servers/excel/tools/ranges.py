import logging
import re
from typing import Any, Dict, Optional, Tuple

import httpx

from .base import get_excel_client, parse_workbook_url
from .utils import format_api_error
from .worksheets import (
    fetch_first_worksheet,
    fetch_named_worksheet,
    fetch_worksheet_by_id,
)

logger = logging.getLogger(__name__)

class WorksheetResolutionError(RuntimeError):
    """Raised when a worksheet cannot be resolved for a workbook."""


CELL_REF_RE = re.compile(r"^\$?([A-Za-z]+)?\$?(\d+)?$")

def _escape_range_address(address: str) -> str:
    return address.replace("'", "''")


def _validate_cell_coordinates(column: str, row: int) -> str:
    if not isinstance(column, str) or not column.strip() or not column.isalpha():
        raise ValueError("Column must be alphabetic (e.g. 'A', 'AB').")
    if not isinstance(row, int) or row <= 0:
        raise ValueError("Row must be a positive integer.")
    return column.upper()


def _column_label_to_index(label: str) -> int:
    label = label.upper()
    value = 0
    for char in label:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def _index_to_column_label(index: int) -> str:
    result = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(remainder + ord("A")) + result
    return result or "A"


def _clean_sheet_name(raw: str, fallback: str) -> str:
    sheet = raw.strip()
    if sheet.startswith("'") and sheet.endswith("'") and len(sheet) >= 2:
        sheet = sheet[1:-1].replace("''", "'")
    return sheet or fallback


def _parse_range_metadata(address: str | None, fallback_sheet_name: str) -> tuple[str, int, int]:
    sheet_name = fallback_sheet_name
    start_row = 1
    start_column_index = 0

    if not address:
        return sheet_name, start_row, start_column_index

    range_part = address
    if "!" in address:
        sheet_segment, range_part = address.split("!", 1)
        sheet_name = _clean_sheet_name(sheet_segment, fallback_sheet_name)

    range_part = range_part.strip()
    if not range_part:
        return sheet_name, start_row, start_column_index

    if ":" in range_part:
        start_ref = range_part.split(":", 1)[0]
    else:
        start_ref = range_part

    start_ref = start_ref.replace("$", "").strip()
    match = CELL_REF_RE.match(start_ref)
    if not match:
        return sheet_name, start_row, start_column_index

    column_label, row_part = match.groups()
    if column_label:
        start_column_index = max(0, _column_label_to_index(column_label))
    if row_part:
        try:
            parsed_row = int(row_part)
            if parsed_row > 0:
                start_row = parsed_row
        except ValueError:
            pass

    return sheet_name, start_row, start_column_index


def _ensure_matrix(values: Any) -> list[list[Any]]:
    if not isinstance(values, list):
        return []
    matrix: list[list[Any]] = []
    for row in values:
        if isinstance(row, list):
            matrix.append(row)
        elif row is None:
            matrix.append([])
        else:
            matrix.append([row])
    return matrix


def _build_user_entered_matrix(
    calculated_values: list[list[Any]],
    formulas: Any,
) -> list[list[Any]]:
    normalized_formulas = _ensure_matrix(formulas)
    row_count = max(len(calculated_values), len(normalized_formulas))
    if row_count == 0:
        return calculated_values

    result: list[list[Any]] = []
    for row_idx in range(row_count):
        value_row = calculated_values[row_idx] if row_idx < len(calculated_values) else []
        formula_row = normalized_formulas[row_idx] if row_idx < len(normalized_formulas) else []
        max_cols = max(len(value_row), len(formula_row))
        row_values: list[Any] = []
        for col_idx in range(max_cols):
            formula_cell = formula_row[col_idx] if col_idx < len(formula_row) else None
            value_cell = value_row[col_idx] if col_idx < len(value_row) else None
            if formula_cell not in (None, ""):
                row_values.append(formula_cell)
            else:
                row_values.append(value_cell)
        result.append(row_values)

    return result


def _normalize_formatted_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    return False


def _build_sheet_data(
    formatted_matrix: list[list[Any]],
    user_matrix: list[list[Any]],
    cell_value_format: str,
    start_row: int,
    start_column_index: int,
) -> dict[int, dict[str, Any]]:
    match cell_value_format:
        case "formatted":
            total_rows = len(formatted_matrix)
        case "userEntered":
            total_rows = len(user_matrix)
        case _:
            total_rows = max(len(formatted_matrix), len(user_matrix))

    cells: dict[int, dict[str, Any]] = {}

    for row_idx in range(total_rows):
        formatted_row = formatted_matrix[row_idx] if row_idx < len(formatted_matrix) else []
        user_row = user_matrix[row_idx] if row_idx < len(user_matrix) else []

        match cell_value_format:
            case "formatted":
                max_cols = len(formatted_row)
            case "userEntered":
                max_cols = len(user_row)
            case _:
                max_cols = max(len(formatted_row), len(user_row))

        row_data: dict[str, Any] = {}

        for col_idx in range(max_cols):
            formatted_value = (
                formatted_row[col_idx] if col_idx < len(formatted_row) else None
            )
            user_value = user_row[col_idx] if col_idx < len(user_row) else None

            normalized_formatted = _normalize_formatted_value(formatted_value)
            has_formatted = not _is_empty(normalized_formatted)
            has_user = not _is_empty(user_value)

            column_label = _index_to_column_label(start_column_index + col_idx)

            if cell_value_format == "formatted":
                if not has_formatted:
                    continue
                row_data[column_label] = normalized_formatted
            elif cell_value_format == "userEntered":
                if not has_user:
                    continue
                row_data[column_label] = user_value
            else:
                if not (has_formatted or has_user):
                    continue
                row_data[column_label] = {
                    "userEnteredValue": user_value if has_user else "",
                    "formattedValue": normalized_formatted,
                }

        if row_data:
            cells[start_row + row_idx] = row_data

    return cells


async def _resolve_worksheet(
    httpx_client: httpx.AsyncClient,
    base_url: str,
    headers: Dict[str, str],
    workbook_item_id: str,
    drive_path: str,
    worksheet_id: str | None = None,
    worksheet_name: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve the worksheet identifier to a URL segment accepted by Microsoft Graph.
    """
    if worksheet_id:
        metadata = await fetch_worksheet_by_id(
            httpx_client, headers, base_url, workbook_item_id, worksheet_id, drive_path
        )
        if metadata:
            segment = f"/workbook/worksheets/{worksheet_id}"
            return segment, metadata
        raise WorksheetResolutionError(
            f"Worksheet with ID '{worksheet_id}' was not found in workbook '{workbook_item_id}'"
        )

    if worksheet_name:
        metadata = await fetch_named_worksheet(
            httpx_client, headers, base_url, workbook_item_id, worksheet_name, drive_path
        )
        if metadata:
            escaped_name = worksheet_name.replace("'", "''")
            segment = f"/workbook/worksheets('{escaped_name}')"
            return segment, metadata
        raise WorksheetResolutionError(
            f"Worksheet named '{worksheet_name}' was not found in workbook '{workbook_item_id}'"
        )

    metadata = await fetch_first_worksheet(
        httpx_client, headers, base_url, workbook_item_id, drive_path
    )
    if not metadata:
        raise WorksheetResolutionError(
            f"No worksheets were found in workbook '{workbook_item_id}'"
        )

    worksheet_id = metadata.get("id")
    segment = f"/workbook/worksheets/{worksheet_id}"
    return segment, metadata


async def excel_get_worksheet(
    workbook_url: str,
    worksheet_id: str | None = None,
    worksheet_name: str | None = None,
    range_address: str | None = None,
    cell_value_format: str = "formatted",
) -> Dict[str, Any]:
    """
    Retrieve cell data for the specified range or the used range of a worksheet.
    Supports both OneDrive and SharePoint workbooks.

    Args:
        workbook_url: The shared URL of the Excel workbook
    """
    client = get_excel_client()
    if not client:
        raise RuntimeError("Unable to initialize Excel client")

    if cell_value_format not in {"formatted", "userEntered", "all"}:
        raise ValueError(
            "cell_value_format must be one of: 'formatted', 'userEntered', 'all'"
        )

    # Parse the workbook URL to get the workbook item information
    target_item_info = await parse_workbook_url(workbook_url, client)
    workbook_item_id = target_item_info.get("id")

    if not workbook_item_id:
        raise RuntimeError("Failed to extract workbook ID from workbook URL")

    # Extract parent reference to determine the drive path
    parent_ref = target_item_info.get("parentReference", {})
    drive_id = parent_ref.get("driveId")
    if not drive_id:
        raise RuntimeError("Failed to extract drive ID from shared URL")

    # Construct the drive path
    drive_path = f"/drives/{drive_id}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            worksheet_segment, worksheet_metadata = await _resolve_worksheet(
                httpx_client,
                client["base_url"],
                client["headers"],
                workbook_item_id,
                drive_path,
                worksheet_id=worksheet_id,
                worksheet_name=worksheet_name,
            )

            normalized_range = None
            if range_address:
                range_part = range_address.split("!", 1)[-1] if "!" in range_address else range_address
                range_part = range_part.strip()
                if range_part:
                    normalized_range = range_part

            if normalized_range:
                escaped_range = _escape_range_address(normalized_range)
                url = (
                    f"{client['base_url']}{drive_path}/items/{workbook_item_id}"
                    f"{worksheet_segment}/range(address='{escaped_range}')"
                )
            else:
                url = (
                    f"{client['base_url']}{drive_path}/items/{workbook_item_id}"
                    f"{worksheet_segment}/usedRange(valuesOnly=false)"
                )

            response = await httpx_client.get(url, headers=client["headers"])
            response.raise_for_status()
    except WorksheetResolutionError as exc:
        raise RuntimeError(str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        error_detail = format_api_error(exc.response.status_code, exc.response.text)
        logger.error("Excel get range failed: %s", exc.response.text)
        raise RuntimeError(
            f"Excel API returned {exc.response.status_code}: {error_detail}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error retrieving Excel range")
        raise RuntimeError(f"Failed to retrieve range: {exc}") from exc

    payload = response.json()

    workbook_title = target_item_info.get("name", "")
    workbook_url_value = target_item_info.get("webUrl") or workbook_url

    formatted_matrix_raw = payload.get("text") or payload.get("values")
    calculated_matrix = _ensure_matrix(payload.get("values"))
    formatted_matrix = _ensure_matrix(formatted_matrix_raw)
    user_entered_matrix = _build_user_entered_matrix(calculated_matrix, payload.get("formulas"))

    sheet_name_from_address, start_row, start_column_index = _parse_range_metadata(
        payload.get("address"), worksheet_metadata.get("name", "")
    )

    sheet_data = _build_sheet_data(
        formatted_matrix,
        user_entered_matrix,
        cell_value_format,
        start_row,
        start_column_index,
    )

    sheet_entry = {
        "sheetId": worksheet_metadata.get("id"),
        "title": worksheet_metadata.get("name") or sheet_name_from_address,
        "rowCount": payload.get("rowCount"),
        "columnCount": payload.get("columnCount"),
        "data": sheet_data,
    }

    return {
        "title": workbook_title,
        "spreadsheetId": workbook_item_id,
        "spreadsheetUrl": workbook_url_value,
        "sheets": [sheet_entry],
    }


async def excel_write_to_cell(
    workbook_url: str,
    column: str,
    row: int,
    value: Any,
    worksheet_id: str | None = None,
    worksheet_name: str | None = None,
) -> Dict[str, Any]:
    """
    Write a value to a single cell within the specified worksheet.
    Supports both OneDrive and SharePoint workbooks.
    Uses session-based editing to support concurrent editing when file is open.

    Args:
        workbook_url: The shared URL of the Excel workbook
    """
    client = get_excel_client()
    if not client:
        raise RuntimeError("Unable to initialize Excel client")

    column_label = _validate_cell_coordinates(column, row)
    range_address = f"{column_label}{row}"

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

    try:
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            worksheet_segment, worksheet_metadata = await _resolve_worksheet(
                httpx_client,
                client["base_url"],
                client["headers"],
                workbook_item_id,
                drive_path,
                worksheet_id=worksheet_id,
                worksheet_name=worksheet_name,
            )

            # Step 1: Create a workbook session for concurrent editing
            session_url = (
                f"{client['base_url']}{drive_path}/items/{workbook_item_id}"
                f"/workbook/createSession"
            )
            session_payload = {"persistChanges": True}
            headers = {**client["headers"], "Content-Type": "application/json"}

            session_response = await httpx_client.post(
                session_url, headers=headers, json=session_payload
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data.get("id")

            if not session_id:
                raise RuntimeError("Failed to create workbook session")

            logger.info("Created workbook session: %s", session_id)

            try:
                # Step 2: Write to cell using the session
                escaped_range = _escape_range_address(range_address)
                url = (
                    f"{client['base_url']}{drive_path}/items/{workbook_item_id}"
                    f"{worksheet_segment}/range(address='{escaped_range}')"
                )

                payload = {"values": [[value]]}
                # Add session ID to headers
                session_headers = {**headers, "workbook-session-id": session_id}

                response = await httpx_client.patch(url, headers=session_headers, json=payload)
                response.raise_for_status()

                result_payload = response.json()

            finally:
                # Step 3: Close the session
                close_session_url = (
                    f"{client['base_url']}{drive_path}/items/{workbook_item_id}"
                    f"/workbook/closeSession"
                )
                close_headers = {**headers, "workbook-session-id": session_id}
                try:
                    await httpx_client.post(close_session_url, headers=close_headers)
                    logger.info("Closed workbook session: %s", session_id)
                except Exception as close_exc:
                    logger.warning("Failed to close session %s: %s", session_id, close_exc)

    except WorksheetResolutionError as exc:
        raise RuntimeError(str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        error_detail = format_api_error(exc.response.status_code, exc.response.text)
        logger.error("Excel write to cell failed: %s", exc.response.text)
        raise RuntimeError(
            f"Excel API returned {exc.response.status_code}: {error_detail}"
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error writing to Excel cell")
        raise RuntimeError(f"Failed to write to cell: {exc}") from exc

    return {
        "workbook_id": workbook_item_id,
        "drive_type": drive_type,
        "worksheet": {
            "id": worksheet_metadata.get("id"),
            "name": worksheet_metadata.get("name"),
            "position": worksheet_metadata.get("position"),
        },
        "range": result_payload.get("address"),
        "values": result_payload.get("values"),
        "text": result_payload.get("text"),
    }


__all__ = ["excel_get_worksheet", "excel_write_to_cell"]
