
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from models import (
    CellData,
    CellExtendedValue,
    CellFormat,
    CellValue,
    GridData,
    GridProperties,
    NumberFormat,
    NumberFormatType,
    RowData,
    Sheet,
    SheetDataInput,
    SheetProperties,
)

DEFAULT_SEARCH_CONTACTS_LIMIT = 30

DEFAULT_SHEET_ROW_COUNT = 1000
DEFAULT_SHEET_COLUMN_COUNT = 26

# ----------------------------------------------------------------
# Sheets utils
# ----------------------------------------------------------------

def col_to_index(col: str) -> int:
    """Convert a sheet's column string to a 0-indexed column index

    Args:
        col (str): The column string to convert. e.g., "A", "AZ", "QED"

    Returns:
        int: The 0-indexed column index.
    """
    result = 0
    for char in col.upper():
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1


def index_to_col(index: int) -> str:
    """Convert a 0-indexed column index to its corresponding column string

    Args:
        index (int): The 0-indexed column index to convert.

    Returns:
        str: The column string. e.g., "A", "AZ", "QED"
    """
    result = ""
    index += 1
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(rem + ord("A")) + result
    return result


def is_col_greater(col1: str, col2: str) -> bool:
    """Determine if col1 represents a column that comes after col2 in a sheet

    This comparison is based on:
      1. The length of the column string (longer means greater).
      2. Lexicographical comparison if both strings are the same length.

    Args:
        col1 (str): The first column string to compare.
        col2 (str): The second column string to compare.

    Returns:
        bool: True if col1 comes after col2, False otherwise.
    """
    if len(col1) != len(col2):
        return len(col1) > len(col2)
    return col1.upper() > col2.upper()


def compute_sheet_data_dimensions(
    sheet_data_input: SheetDataInput,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Compute the dimensions of a sheet based on the data provided.

    Args:
        sheet_data_input (SheetDataInput):
            The data to compute the dimensions of.

    Returns:
        tuple[tuple[int, int], tuple[int, int]]: The dimensions of the sheet. The first tuple
            contains the row range (start, end) and the second tuple contains the column range
            (start, end).
    """
    max_row = 0
    min_row = 10_000_000  # max number of cells in a sheet
    max_col_str = None
    min_col_str = None

    for key, row in sheet_data_input.data.items():
        try:
            row_num = int(key)
        except ValueError:
            continue
        if row_num > max_row:
            max_row = row_num
        if row_num < min_row:
            min_row = row_num

        if isinstance(row, dict):
            for col in row:
                # Update max column string
                if max_col_str is None or is_col_greater(col, max_col_str):
                    max_col_str = col
                # Update min column string
                if min_col_str is None or is_col_greater(min_col_str, col):
                    min_col_str = col

    max_col_index = col_to_index(max_col_str) if max_col_str is not None else -1
    min_col_index = col_to_index(min_col_str) if min_col_str is not None else 0

    return (min_row, max_row), (min_col_index, max_col_index)


def create_sheet(sheet_data_input: SheetDataInput) -> Sheet:
    """Create a Google Sheet from a dictionary of data.

    Args:
        sheet_data_input (SheetDataInput): The data to create the sheet from.

    Returns:
        Sheet: The created sheet.
    """
    (_, max_row), (min_col_index, max_col_index) = compute_sheet_data_dimensions(sheet_data_input)
    sheet_data = create_sheet_data(sheet_data_input, min_col_index, max_col_index)
    sheet_properties = create_sheet_properties(
        row_count=max(DEFAULT_SHEET_ROW_COUNT, max_row),
        column_count=max(DEFAULT_SHEET_COLUMN_COUNT, max_col_index + 1),
    )

    return Sheet(properties=sheet_properties, data=sheet_data)


def create_sheet_properties(
    sheet_id: int = 1,
    title: str = "Sheet1",
    row_count: int = DEFAULT_SHEET_ROW_COUNT,
    column_count: int = DEFAULT_SHEET_COLUMN_COUNT,
) -> SheetProperties:
    """Create a SheetProperties object

    Args:
        sheet_id (int): The ID of the sheet.
        title (str): The title of the sheet.
        row_count (int): The number of rows in the sheet.
        column_count (int): The number of columns in the sheet.

    Returns:
        SheetProperties: The created sheet properties object.
    """
    return SheetProperties(
        sheetId=sheet_id,
        title=title,
        gridProperties=GridProperties(rowCount=row_count, columnCount=column_count),
    )


def group_contiguous_rows(row_numbers: list[int]) -> list[list[int]]:
    """Groups a sorted list of row numbers into contiguous groups

    A contiguous group is a list of row numbers that are consecutive integers.
    For example, [1,2,3,5,6] is converted to [[1,2,3],[5,6]].

    Args:
        row_numbers (list[int]): The list of row numbers to group.

    Returns:
        list[list[int]]: The grouped row numbers.
    """
    if not row_numbers:
        return []
    groups = []
    current_group = [row_numbers[0]]
    for r in row_numbers[1:]:
        if r == current_group[-1] + 1:
            current_group.append(r)
        else:
            groups.append(current_group)
            current_group = [r]
    groups.append(current_group)
    return groups


def create_cell_data(cell_value: CellValue) -> CellData:
    """
    Create a CellData object based on the type of cell_value.
    """
    if isinstance(cell_value, bool):
        return _create_bool_cell(cell_value)
    elif isinstance(cell_value, int):
        return _create_int_cell(cell_value)
    elif isinstance(cell_value, float):
        return _create_float_cell(cell_value)
    elif isinstance(cell_value, str):
        return _create_string_cell(cell_value)


def _create_formula_cell(cell_value: str) -> CellData:
    cell_val = CellExtendedValue(formulaValue=cell_value)
    return CellData(userEnteredValue=cell_val)


def _create_currency_cell(cell_value: str) -> CellData:
    value_without_symbol = cell_value[1:]
    try:
        num_value = int(value_without_symbol)
        cell_format = CellFormat(
            numberFormat=NumberFormat(type=NumberFormatType.CURRENCY, pattern="$#,##0")
        )
        cell_val = CellExtendedValue(numberValue=num_value)
        return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
    except ValueError:
        try:
            num_value = float(value_without_symbol)  # type: ignore[assignment]
            cell_format = CellFormat(
                numberFormat=NumberFormat(type=NumberFormatType.CURRENCY, pattern="$#,##0.00")
            )
            cell_val = CellExtendedValue(numberValue=num_value)
            return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
        except ValueError:
            return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def _create_percent_cell(cell_value: str) -> CellData:
    try:
        num_value = float(cell_value[:-1].strip())
        cell_format = CellFormat(
            numberFormat=NumberFormat(type=NumberFormatType.PERCENT, pattern="0.00%")
        )
        cell_val = CellExtendedValue(numberValue=num_value)
        return CellData(userEnteredValue=cell_val, userEnteredFormat=cell_format)
    except ValueError:
        return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def _create_bool_cell(cell_value: bool) -> CellData:
    return CellData(userEnteredValue=CellExtendedValue(boolValue=cell_value))


def _create_int_cell(cell_value: int) -> CellData:
    cell_format = CellFormat(
        numberFormat=NumberFormat(type=NumberFormatType.NUMBER, pattern="#,##0")
    )
    return CellData(
        userEnteredValue=CellExtendedValue(numberValue=cell_value), userEnteredFormat=cell_format
    )


def _create_float_cell(cell_value: float) -> CellData:
    cell_format = CellFormat(
        numberFormat=NumberFormat(type=NumberFormatType.NUMBER, pattern="#,##0.00")
    )
    return CellData(
        userEnteredValue=CellExtendedValue(numberValue=cell_value), userEnteredFormat=cell_format
    )


def _create_string_cell(cell_value: str) -> CellData:
    if cell_value.startswith("="):
        return _create_formula_cell(cell_value)
    elif cell_value.startswith("$") and len(cell_value) > 1:
        return _create_currency_cell(cell_value)
    elif cell_value.endswith("%") and len(cell_value) > 1:
        return _create_percent_cell(cell_value)

    return CellData(userEnteredValue=CellExtendedValue(stringValue=cell_value))


def create_row_data(
    row_data: dict[str, CellValue], min_col_index: int, max_col_index: int
) -> RowData:
    """Constructs RowData for a single row using the provided row_data.

    Args:
        row_data (dict[str, CellValue]): The data to create the row from.
        min_col_index (int): The minimum column index from the SheetDataInput.
        max_col_index (int): The maximum column index from the SheetDataInput.
    """
    row_cells = []
    for col_idx in range(min_col_index, max_col_index + 1):
        col_letter = index_to_col(col_idx)
        if col_letter in row_data:
            cell_data = create_cell_data(row_data[col_letter])
        else:
            cell_data = CellData(userEnteredValue=CellExtendedValue(stringValue=""))
        row_cells.append(cell_data)
    return RowData(values=row_cells)


def create_sheet_data(
    sheet_data_input: SheetDataInput,
    min_col_index: int,
    max_col_index: int,
) -> list[GridData]:
    """Create grid data from SheetDataInput by grouping contiguous rows and processing cells.

    Args:
        sheet_data_input (SheetDataInput): The data to create the sheet from.
        min_col_index (int): The minimum column index from the SheetDataInput.
        max_col_index (int): The maximum column index from the SheetDataInput.

    Returns:
        list[GridData]: The created grid data.
    """
    row_numbers = list(sheet_data_input.data.keys())
    if not row_numbers:
        return []

    sorted_rows = sorted(row_numbers)
    groups = group_contiguous_rows(sorted_rows)

    sheet_data = []
    for group in groups:
        rows_data = []
        for r in group:
            current_row_data = sheet_data_input.data.get(r, {})
            row = create_row_data(current_row_data, min_col_index, max_col_index)
            rows_data.append(row)
        grid_data = GridData(
            startRow=group[0] - 1,  # convert to 0-indexed
            startColumn=min_col_index,
            rowData=rows_data,
        )
        sheet_data.append(grid_data)

    return sheet_data


def parse_get_spreadsheet_response(api_response: dict) -> dict:
    """
    Parse the get spreadsheet Google Sheets API response into a structured dictionary.
    """
    properties = api_response.get("properties", {})
    sheets = [parse_sheet(sheet) for sheet in api_response.get("sheets", [])]

    return {
        "title": properties.get("title", ""),
        "spreadsheetId": api_response.get("spreadsheetId", ""),
        "spreadsheetUrl": api_response.get("spreadsheetUrl", ""),
        "sheets": sheets,
    }


def parse_sheet(api_sheet: dict) -> dict:
    """
    Parse an individual sheet's data from the Google Sheets 'get spreadsheet'
    API response into a structured dictionary.
    """
    props = api_sheet.get("properties", {})
    grid_props = props.get("gridProperties", {})
    cell_data = convert_api_grid_data_to_dict(api_sheet.get("data", []))

    return {
        "sheetId": props.get("sheetId"),
        "title": props.get("title", ""),
        "rowCount": grid_props.get("rowCount", 0),
        "columnCount": grid_props.get("columnCount", 0),
        "data": cell_data,
    }


def extract_user_entered_cell_value(cell: dict) -> Any:
    """
    Extract the user entered value from a cell's 'userEnteredValue'.

    Args:
        cell (dict): A cell dictionary from the grid data.

    Returns:
        The extracted value if present, otherwise None.
    """
    user_val = cell.get("userEnteredValue", {})
    for key in ["stringValue", "numberValue", "boolValue", "formulaValue"]:
        if key in user_val:
            return user_val[key]

    return ""


def process_row(row: dict, start_column_index: int) -> dict:
    """
    Process a single row from grid data, converting non-empty cells into a dictionary
    that maps column letters to cell values.

    Args:
        row (dict): A row from the grid data.
        start_column_index (int): The starting column index for this row.

    Returns:
        dict: A mapping of column letters to cell values for non-empty cells.
    """
    row_result = {}
    for j, cell in enumerate(row.get("values", [])):
        column_index = start_column_index + j
        column_string = index_to_col(column_index)
        user_entered_cell_value = extract_user_entered_cell_value(cell)
        formatted_cell_value = cell.get("formattedValue", "")

        if user_entered_cell_value != "" or formatted_cell_value != "":
            row_result[column_string] = {
                "userEnteredValue": user_entered_cell_value,
                "formattedValue": formatted_cell_value,
            }

    return row_result


def convert_api_grid_data_to_dict(grids: list[dict]) -> dict:
    """
    Convert a list of grid data dictionaries from the 'get spreadsheet' API
    response into a structured cell dictionary.

    The returned dictionary maps row numbers to sub-dictionaries that map column letters
    (e.g., 'A', 'B', etc.) to their corresponding non-empty cell values.

    Args:
        grids (list[dict]): The list of grid data dictionaries from the API.

    Returns:
        dict: A dictionary mapping row numbers to dictionaries of column letter/value pairs.
            Only includes non-empty rows and non-empty cells.
    """
    result = {}
    for grid in grids:
        start_row = grid.get("startRow", 0)
        start_column = grid.get("startColumn", 0)

        for i, row in enumerate(grid.get("rowData", []), start=1):
            current_row = start_row + i
            row_data = process_row(row, start_column)

            if row_data:
                result[current_row] = row_data

    return dict(sorted(result.items()))


def validate_write_to_cell_params(  # type: ignore[no-any-unimported]
    service: Resource,
    spreadsheet_id: str,
    sheet_name: str,
    column: str,
    row: int,
) -> None:
    """Validates the input parameters for the write to cell tool.

    Args:
        service (Resource): The Google Sheets service.
        spreadsheet_id (str): The ID of the spreadsheet provided to the tool.
        sheet_name (str): The name of the sheet provided to the tool.
        column (str): The column to write to provided to the tool.
        row (int): The row to write to provided to the tool.

    Raises:
        RetryableToolError:
            If the sheet name is not found in the spreadsheet
        ToolExecutionError:
            If the column is not alphabetical
            If the row is not a positive number
            If the row is out of bounds for the sheet
            If the column is out of bounds for the sheet
    """
    if not column.isalpha():
        raise ToolExecutionError(
            message=(
                f"Invalid column name {column}. "
                "It must be a non-empty string containing only letters"
            ),
        )

    if row < 1:
        raise ToolExecutionError(
            message=(f"Invalid row number {row}. It must be a positive integer greater than 0."),
        )

    sheet_properties = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            includeGridData=True,
            fields="sheets/properties/title,sheets/properties/gridProperties/rowCount,sheets/properties/gridProperties/columnCount",
        )
        .execute()
    )
    sheet_names = [sheet["properties"]["title"] for sheet in sheet_properties["sheets"]]
    sheet_row_count = sheet_properties["sheets"][0]["properties"]["gridProperties"]["rowCount"]
    sheet_column_count = sheet_properties["sheets"][0]["properties"]["gridProperties"][
        "columnCount"
    ]

    if sheet_name not in sheet_names:
        raise RetryableToolError(
            message=f"Sheet name {sheet_name} not found in spreadsheet with id {spreadsheet_id}",
            additional_prompt_content=f"Sheet names in the spreadsheet: {sheet_names}",
            retry_after_ms=100,
        )

    if row > sheet_row_count:
        raise ToolExecutionError(
            message=(
                f"Row {row} is out of bounds for sheet {sheet_name} "
                f"in spreadsheet with id {spreadsheet_id}. "
                f"Sheet only has {sheet_row_count} rows which is less than the requested row {row}"
            )
        )

    if col_to_index(column) > sheet_column_count:
        raise ToolExecutionError(
            message=(
                f"Column {column} is out of bounds for sheet {sheet_name} "
                f"in spreadsheet with id {spreadsheet_id}. "
                f"Sheet only has {sheet_column_count} columns which "
                f"is less than the requested column {column}"
            )
        )


def parse_write_to_cell_response(response: dict) -> dict:
    return {
        "spreadsheetId": response["spreadsheetId"],
        "sheetTitle": response["updatedData"]["range"].split("!")[0],
        "updatedCell": response["updatedData"]["range"].split("!")[1],
        "value": response["updatedData"]["values"][0][0],
    }
