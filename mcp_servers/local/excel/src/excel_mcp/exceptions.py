class ExcelMCPError(Exception):
    """Base exception for Excel MCP errors."""
    pass

class WorkbookError(ExcelMCPError):
    """Raised when workbook operations fail."""
    pass

class SheetError(ExcelMCPError):
    """Raised when sheet operations fail."""
    pass

class DataError(ExcelMCPError):
    """Raised when data operations fail."""
    pass

class ValidationError(ExcelMCPError):
    """Raised when validation fails."""
    pass

class FormattingError(ExcelMCPError):
    """Raised when formatting operations fail."""
    pass

class CalculationError(ExcelMCPError):
    """Raised when formula calculations fail."""
    pass

class PivotError(ExcelMCPError):
    """Raised when pivot table operations fail."""
    pass

class ChartError(ExcelMCPError):
    """Raised when chart operations fail."""
    pass
