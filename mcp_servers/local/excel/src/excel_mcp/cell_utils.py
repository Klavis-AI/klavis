import re

from openpyxl.utils import column_index_from_string

def parse_cell_range(
    cell_ref: str,
    end_ref: str | None = None
) -> tuple[int, int, int | None, int | None]:
    """Parse Excel cell reference into row and column indices."""
    if end_ref:
        start_cell = cell_ref
        end_cell = end_ref
    else:
        start_cell = cell_ref
        end_cell = None

    match = re.match(r"([A-Z]+)([0-9]+)", start_cell.upper())
    if not match:
        raise ValueError(f"Invalid cell reference: {start_cell}")
    col_str, row_str = match.groups()
    start_row = int(row_str)
    start_col = column_index_from_string(col_str)

    if end_cell:
        match = re.match(r"([A-Z]+)([0-9]+)", end_cell.upper())
        if not match:
            raise ValueError(f"Invalid cell reference: {end_cell}")
        col_str, row_str = match.groups()
        end_row = int(row_str)
        end_col = column_index_from_string(col_str)
    else:
        end_row = None
        end_col = None

    return start_row, start_col, end_row, end_col

def validate_cell_reference(cell_ref: str) -> bool:
    """Validate Excel cell reference format (e.g., 'A1', 'BC123')"""
    if not cell_ref:
        return False

    # Split into column and row parts
    col = row = ""
    for c in cell_ref:
        if c.isalpha():
            if row:  # Letters after numbers not allowed
                return False
            col += c
        elif c.isdigit():
            row += c
        else:
            return False

    return bool(col and row) 