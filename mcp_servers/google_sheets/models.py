import json
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator, model_validator

class CellErrorType(str, Enum):
    """The type of error in a cell

    Implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ErrorType
    """

    ERROR_TYPE_UNSPECIFIED = "ERROR_TYPE_UNSPECIFIED"  # The default error type, do not use this.
    ERROR = "ERROR"  # Corresponds to the #ERROR! error.
    NULL_VALUE = "NULL_VALUE"  # Corresponds to the #NULL! error.
    DIVIDE_BY_ZERO = "DIVIDE_BY_ZERO"  # Corresponds to the #DIV/0 error.
    VALUE = "VALUE"  # Corresponds to the #VALUE! error.
    REF = "REF"  # Corresponds to the #REF! error.
    NAME = "NAME"  # Corresponds to the #NAME? error.
    NUM = "NUM"  # Corresponds to the #NUM! error.
    N_A = "N_A"  # Corresponds to the #N/A error.
    LOADING = "LOADING"  # Corresponds to the Loading... state.


class CellErrorValue(BaseModel):
    """An error in a cell

    Implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ErrorValue
    """

    type: CellErrorType
    message: str


class CellExtendedValue(BaseModel):
    """The kinds of value that a cell in a spreadsheet can have

    Implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ExtendedValue
    """

    numberValue: float | None = None
    stringValue: str | None = None
    boolValue: bool | None = None
    formulaValue: str | None = None
    errorValue: Optional["CellErrorValue"] = None

    @model_validator(mode="after")
    def check_exactly_one_value(cls, instance):  # type: ignore[no-untyped-def]
        provided = [v for v in instance.__dict__.values() if v is not None]
        if len(provided) != 1:
            raise ValueError(
                "Exactly one of numberValue, stringValue, boolValue, "
                "formulaValue, or errorValue must be set."
            )
        return instance


class NumberFormatType(str, Enum):
    NUMBER = "NUMBER"
    PERCENT = "PERCENT"
    CURRENCY = "CURRENCY"


class NumberFormat(BaseModel):
    """The format of a number

    Implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#NumberFormat
    """

    pattern: str
    type: NumberFormatType


class CellFormat(BaseModel):
    """The format of a cell

    Partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellFormat
    """

    numberFormat: NumberFormat


class CellData(BaseModel):
    """Data about a specific cell

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellData
    """

    userEnteredValue: CellExtendedValue
    userEnteredFormat: CellFormat | None = None


class RowData(BaseModel):
    """Data about each cellin a row

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#RowData
    """

    values: list[CellData]


class GridData(BaseModel):
    """Data in the grid

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#GridData
    """

    startRow: int
    startColumn: int
    rowData: list[RowData]


class GridProperties(BaseModel):
    """Properties of a grid

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#GridProperties
    """

    rowCount: int
    columnCount: int


class SheetProperties(BaseModel):
    """Properties of a Sheet

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#SheetProperties
    """

    sheetId: int
    title: str
    gridProperties: GridProperties | None = None


class Sheet(BaseModel):
    """A Sheet in a spreadsheet

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/sheets#Sheet
    """

    properties: SheetProperties
    data: list[GridData] | None = None


class SpreadsheetProperties(BaseModel):
    """Properties of a spreadsheet

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#SpreadsheetProperties
    """

    title: str


class Spreadsheet(BaseModel):
    """A spreadsheet

    A partial implementation of https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
    """

    properties: SpreadsheetProperties
    sheets: list[Sheet]


CellValue = int | float | str | bool


class SheetDataInput(BaseModel):
    """
    SheetDataInput models the cell data of a spreadsheet in a custom format.

    It is a dictionary mapping row numbers (as ints) to dictionaries that map
    column letters (as uppercase strings) to cell values (int, float, str, or bool).

    This model enforces that:
      - The outer keys are convertible to int.
      - The inner keys are alphabetic strings (normalized to uppercase).
      - All cell values are only of type int, float, str, or bool.

    The model automatically serializes (via `json_data()`)
    and validates the inner types.
    """

    data: dict[int, dict[str, CellValue]]

    @classmethod
    def _parse_json_if_string(cls, value):  # type: ignore[no-untyped-def]
        """Parses the value if it is a JSON string, otherwise returns it.

        Helper method for when validating the `data` field.
        """
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise TypeError(f"Invalid JSON: {e}")
        return value

    @classmethod
    def _validate_row_key(cls, row_key) -> int:  # type: ignore[no-untyped-def]
        """Converts the row key to an integer, raising an error if conversion fails.

        Helper method for when validating the `data` field.
        """
        try:
            return int(row_key)
        except (ValueError, TypeError):
            raise TypeError(f"Row key '{row_key}' is not convertible to int.")

    @classmethod
    def _validate_inner_cells(cls, cells, row_int: int) -> dict:  # type: ignore[no-untyped-def]
        """Validates that 'cells' is a dict mapping column letters to valid cell values
        and normalizes the keys.

        Helper method for when validating the `data` field.
        """
        if not isinstance(cells, dict):
            raise TypeError(
                f"Value for row '{row_int}' must be a dict mapping column letters to cell values."
            )
        new_inner = {}
        for col_key, cell_value in cells.items():
            if not isinstance(col_key, str):
                raise TypeError(f"Column key '{col_key}' must be a string.")
            col_string = col_key.upper()
            if not col_string.isalpha():
                raise TypeError(f"Column key '{col_key}' is invalid. Must be alphabetic.")
            if not isinstance(cell_value, int | float | str | bool):
                raise TypeError(
                    f"Cell value for {col_string}{row_int} must be an int, float, str, or bool."
                )
            new_inner[col_string] = cell_value
        return new_inner

    @field_validator("data", mode="before")
    @classmethod
    def validate_and_convert_keys(cls, value):  # type: ignore[no-untyped-def]
        """
        Validates data when SheetDataInput is instantiated and converts it to the correct format.
        Uses private helper methods to parse JSON, validate row keys, and validate inner cell data.
        """
        if value is None:
            return {}

        value = cls._parse_json_if_string(value)
        if isinstance(value, dict):
            new_value = {}
            for row_key, cells in value.items():
                row_int = cls._validate_row_key(row_key)
                inner_cells = cls._validate_inner_cells(cells, row_int)
                new_value[row_int] = inner_cells
            return new_value

        raise TypeError("data must be a dict or a valid JSON string representing a dict")

    def json_data(self) -> str:
        """
        Serialize the sheet data to a JSON string.
        """
        return json.dumps(self.data)

    @classmethod
    def from_json(cls, json_str: str) -> "SheetDataInput":
        """
        Create a SheetData instance from a JSON string.
        """
        return cls.model_validate_json(json_str)
