import json
import re
from io import BytesIO
from typing import Any, Dict

from openpyxl import Workbook

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'
MAX_SHEET_NAME_LENGTH = 31


class SheetDataParseError(ValueError):
    """Raised when sheet data cannot be parsed into the expected structure."""


def format_api_error(status_code: int, error_text: str) -> str:
    """
    Format API error messages to be more user-friendly.

    Args:
        status_code: HTTP status code
        error_text: Raw error response text

    Returns:
        Formatted error message
    """
    # For 401 authentication errors
    if status_code == 401:
        try:
            error_json = json.loads(error_text)
            error_code = error_json.get("error", {}).get("code", "")

            # Check for specific authentication error codes
            if error_code in ["InvalidAuthenticationToken", "UnauthorizedAccessError"]:
                return "Authentication token is invalid or expired. Please re-authenticate and try again."
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # Generic 401 message if we can't parse the error
        return "Authentication token is invalid or expired. Please re-authenticate and try again."

    # For 400 errors that are actually authentication/permission issues
    # Microsoft returns 400 with "invalidRequest" and "Invalid shares key" when it should be 403
    if status_code == 400:
        try:
            error_json = json.loads(error_text)
            error_code = error_json.get("error", {}).get("code", "")
            error_message = error_json.get("error", {}).get("message", "")

            # Check for "Invalid shares key" which indicates auth/permission issue
            if error_code == "invalidRequest" and "Invalid shares key" in error_message:
                return "Authentication token is invalid, expired, or lacks permission to access this resource. Please re-authenticate and ensure you have access to the shared file."
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # For other errors, return the original error text
    return error_text


def sanitize_workbook_name(title: str) -> str:
    """
    Sanitize the workbook title so it can be safely used as a filename.

    Replaces characters Excel does not permit in filenames and trims whitespace.
    Defaults to 'Workbook' if the sanitized name would be empty.
    """
    sanitized = re.sub(INVALID_FILENAME_CHARS, "_", title or "").strip()
    if not sanitized:
        sanitized = "Workbook"
    if not sanitized.lower().endswith(".xlsx"):
        sanitized = f"{sanitized}.xlsx"
    return sanitized


def _normalize_column(column: str) -> str:
    if not isinstance(column, str) or not column.strip() or not column.isalpha():
        raise SheetDataParseError(
            f"Column keys must be alphabetic strings, received: {column!r}"
        )
    return column.upper()


def parse_sheet_data(data: Any) -> Dict[int, Dict[str, Any]]:
    """
    Parse sheet data into a {row -> {column -> value}} mapping.

    Accepts a dict-like object or a JSON string representing the mapping. The outer
    keys must be integers (or strings convertible to ints) and inner keys must be
    alphabetic column labels (e.g. 'A', 'AA').
    """
    if data is None or data == "":
        return {}

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise SheetDataParseError(f"Invalid JSON for sheet data: {exc}") from exc

    if not isinstance(data, dict):
        raise SheetDataParseError("Sheet data must be a dict mapping rows to columns")

    parsed: Dict[int, Dict[str, Any]] = {}
    for row_key, columns in data.items():
        try:
            row_index = int(row_key)
        except (ValueError, TypeError) as exc:
            raise SheetDataParseError(
                f"Row keys must be integers, received: {row_key!r}"
            ) from exc

        if row_index <= 0:
            raise SheetDataParseError("Row indices must be positive integers")

        if not isinstance(columns, dict):
            raise SheetDataParseError(
                f"Row {row_index} must map to a dict of column/value pairs"
            )

        parsed[row_index] = {}
        for column_key, value in columns.items():
            column_label = _normalize_column(column_key)
            parsed[row_index][column_label] = value

    return parsed


def clamp_sheet_title(sheet_title: str | None) -> str:
    """Ensure sheet names are non-empty and within Excel's 31 character limit."""
    title = (sheet_title or "Sheet1").strip() or "Sheet1"
    if len(title) > MAX_SHEET_NAME_LENGTH:
        title = title[:MAX_SHEET_NAME_LENGTH]
    return title


def build_workbook_bytes(
    data: Dict[int, Dict[str, Any]] | None = None,
    sheet_title: str | None = None,
) -> bytes:
    """
    Create an in-memory .xlsx workbook populated with the provided data.
    """
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = clamp_sheet_title(sheet_title)

    if data:
        for row_index in sorted(data.keys()):
            for column_label, value in data[row_index].items():
                cell_reference = f"{column_label}{row_index}"
                worksheet[cell_reference] = value

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream.read()


__all__ = [
    "SheetDataParseError",
    "build_workbook_bytes",
    "clamp_sheet_title",
    "format_api_error",
    "parse_sheet_data",
    "sanitize_workbook_name",
]
