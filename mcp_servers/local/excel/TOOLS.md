# Excel MCP Server Tools

This document provides detailed information about all available tools in the Excel MCP server.

## Workbook Operations

### create_workbook

Creates a new Excel workbook.

```python
create_workbook(filepath: str) -> str
```

- `filepath`: Path where to create workbook
- Returns: Success message with created file path

### create_worksheet

Creates a new worksheet in an existing workbook.

```python
create_worksheet(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Name for the new worksheet
- Returns: Success message

### get_workbook_metadata

Get metadata about workbook including sheets and ranges.

```python
get_workbook_metadata(filepath: str, include_ranges: bool = False) -> str
```

- `filepath`: Path to Excel file
- `include_ranges`: Whether to include range information
- Returns: String representation of workbook metadata

## Data Operations

### write_data_to_excel

Write data to Excel worksheet.

```python
write_data_to_excel(
    filepath: str,
    sheet_name: str,
    data: List[Dict],
    start_cell: str = "A1"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data`: List of dictionaries containing data to write
- `start_cell`: Starting cell (default: "A1")
- Returns: Success message

### read_data_from_excel

Read data from Excel worksheet.

```python
read_data_from_excel(
    filepath: str,
    sheet_name: str,
    start_cell: str = "A1",
    end_cell: str = None,
    preview_only: bool = False
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Source worksheet name
- `start_cell`: Starting cell (default: "A1")
- `end_cell`: Optional ending cell
- `preview_only`: Whether to return only a preview
- Returns: String representation of data

## Formatting Operations

### format_range

Apply formatting to a range of cells.

```python
format_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    font_size: int = None,
    font_color: str = None,
    bg_color: str = None,
    border_style: str = None,
    border_color: str = None,
    number_format: str = None,
    alignment: str = None,
    wrap_text: bool = False,
    merge_cells: bool = False,
    protection: Dict[str, Any] = None,
    conditional_format: Dict[str, Any] = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Optional ending cell of range
- Various formatting options (see parameters)
- Returns: Success message

### merge_cells

Merge a range of cells.

```python
merge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- Returns: Success message

### unmerge_cells

Unmerge a previously merged range of cells.

```python
unmerge_cells(filepath: str, sheet_name: str, start_cell: str, end_cell: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- Returns: Success message

### get_merged_cells

Get merged cells in a worksheet.

```python
get_merged_cells(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- Returns: String representation of merged cells


## Formula Operations

### apply_formula

Apply Excel formula to cell.

```python
apply_formula(filepath: str, sheet_name: str, cell: str, formula: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `cell`: Target cell reference
- `formula`: Excel formula to apply
- Returns: Success message

### validate_formula_syntax

Validate Excel formula syntax without applying it.

```python
validate_formula_syntax(filepath: str, sheet_name: str, cell: str, formula: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `cell`: Target cell reference
- `formula`: Excel formula to validate
- Returns: Validation result message

## Chart Operations

### create_chart

Create chart in worksheet.

```python
create_chart(
    filepath: str,
    sheet_name: str,
    data_range: str,
    chart_type: str,
    target_cell: str,
    title: str = "",
    x_axis: str = "",
    y_axis: str = ""
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data_range`: Range containing chart data
- `chart_type`: Type of chart (line, bar, pie, scatter, area)
- `target_cell`: Cell where to place chart
- `title`: Optional chart title
- `x_axis`: Optional X-axis label
- `y_axis`: Optional Y-axis label
- Returns: Success message

## Pivot Table Operations

### create_pivot_table

Create pivot table in worksheet.

```python
create_pivot_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    target_cell: str,
    rows: List[str],
    values: List[str],
    columns: List[str] = None,
    agg_func: str = "mean"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `data_range`: Range containing source data
- `target_cell`: Cell where to place pivot table
- `rows`: Fields for row labels
- `values`: Fields for values
- `columns`: Optional fields for column labels
- `agg_func`: Aggregation function (sum, count, average, max, min)
- Returns: Success message

## Table Operations

### create_table

Creates a native Excel table from a specified range of data.

```python
create_table(
    filepath: str,
    sheet_name: str,
    data_range: str,
    table_name: str = None,
    table_style: str = "TableStyleMedium9"
) -> str
```

- `filepath`: Path to the Excel file.
- `sheet_name`: Name of the worksheet.
- `data_range`: The cell range for the table (e.g., "A1:D5").
- `table_name`: Optional unique name for the table.
- `table_style`: Optional visual style for the table.
- Returns: Success message.

## Worksheet Operations

### copy_worksheet

Copy worksheet within workbook.

```python
copy_worksheet(filepath: str, source_sheet: str, target_sheet: str) -> str
```

- `filepath`: Path to Excel file
- `source_sheet`: Name of sheet to copy
- `target_sheet`: Name for new sheet
- Returns: Success message

### delete_worksheet

Delete worksheet from workbook.

```python
delete_worksheet(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Name of sheet to delete
- Returns: Success message

### rename_worksheet

Rename worksheet in workbook.

```python
rename_worksheet(filepath: str, old_name: str, new_name: str) -> str
```

- `filepath`: Path to Excel file
- `old_name`: Current sheet name
- `new_name`: New sheet name
- Returns: Success message

## Range Operations

### copy_range

Copy a range of cells to another location.

```python
copy_range(
    filepath: str,
    sheet_name: str,
    source_start: str,
    source_end: str,
    target_start: str,
    target_sheet: str = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Source worksheet name
- `source_start`: Starting cell of source range
- `source_end`: Ending cell of source range
- `target_start`: Starting cell for paste
- `target_sheet`: Optional target worksheet name
- Returns: Success message

### delete_range

Delete a range of cells and shift remaining cells.

```python
delete_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str,
    shift_direction: str = "up"
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Ending cell of range
- `shift_direction`: Direction to shift cells ("up" or "left")
- Returns: Success message

### validate_excel_range

Validate if a range exists and is properly formatted.

```python
validate_excel_range(
    filepath: str,
    sheet_name: str,
    start_cell: str,
    end_cell: str = None
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_cell`: Starting cell of range
- `end_cell`: Optional ending cell of range
- Returns: Validation result message

### get_data_validation_info

Get data validation rules and metadata for a worksheet.

```python
get_data_validation_info(filepath: str, sheet_name: str) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- Returns: JSON string containing all data validation rules with metadata including:
  - Validation type (list, whole, decimal, date, time, textLength)
  - Operator (between, notBetween, equal, greaterThan, lessThan, etc.)
  - Allowed values for list validations (resolved from ranges)
  - Formula constraints for numeric/date validations
  - Cell ranges where validation applies
  - Prompt and error messages

**Note**: The `read_data_from_excel` tool automatically includes validation metadata for individual cells when available.

## Row and Column Operations

### insert_rows

Insert one or more rows starting at the specified row.

```python
insert_rows(
    filepath: str,
    sheet_name: str,
    start_row: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_row`: Row number where to start inserting (1-based)
- `count`: Number of rows to insert (default: 1)
- Returns: Success message

### insert_columns

Insert one or more columns starting at the specified column.

```python
insert_columns(
    filepath: str,
    sheet_name: str,
    start_col: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_col`: Column number where to start inserting (1-based)
- `count`: Number of columns to insert (default: 1)
- Returns: Success message

### delete_sheet_rows

Delete one or more rows starting at the specified row.

```python
delete_sheet_rows(
    filepath: str,
    sheet_name: str,
    start_row: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_row`: Row number where to start deleting (1-based)
- `count`: Number of rows to delete (default: 1)
- Returns: Success message

### delete_sheet_columns

Delete one or more columns starting at the specified column.

```python
delete_sheet_columns(
    filepath: str,
    sheet_name: str,
    start_col: int,
    count: int = 1
) -> str
```

- `filepath`: Path to Excel file
- `sheet_name`: Target worksheet name
- `start_col`: Column number where to start deleting (1-based)
- `count`: Number of columns to delete (default: 1)
- Returns: Success message
