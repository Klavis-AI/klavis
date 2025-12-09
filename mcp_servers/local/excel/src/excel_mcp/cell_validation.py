import logging
from typing import Any, Dict, List, Optional

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

logger = logging.getLogger(__name__)

def get_data_validation_for_cell(worksheet: Worksheet, cell_address: str) -> Optional[Dict[str, Any]]:
    """Get data validation metadata for a specific cell.
    
    Args:
        worksheet: The openpyxl worksheet object
        cell_address: Cell address like 'A1', 'B2', etc.
        
    Returns:
        Dictionary with validation metadata or None if no validation exists
    """
    try:
        # Convert cell address to row/col coordinates
        col_letter, row = coordinate_from_string(cell_address)
        col_idx = column_index_from_string(col_letter)
        
        # Check each data validation rule in the worksheet
        for dv in worksheet.data_validations.dataValidation:
            # Check if this cell is covered by the validation rule
            if _cell_in_validation_range(row, col_idx, dv):
                return _extract_validation_metadata(dv, cell_address, worksheet)
                
        return None
        
    except Exception as e:
        logger.warning(f"Failed to get validation for cell {cell_address}: {e}")
        return None

def _cell_in_validation_range(row: int, col: int, data_validation) -> bool:
    """Check if a cell is within a data validation range."""
    try:
        # data_validation.sqref contains the cell ranges this validation applies to
        for cell_range in data_validation.sqref.ranges:
            if (cell_range.min_row <= row <= cell_range.max_row and 
                cell_range.min_col <= col <= cell_range.max_col):
                return True
        return False
    except Exception as e:
        logger.warning(f"Error checking if cell ({row}, {col}) is in validation range for DV sqref '{getattr(data_validation, 'sqref', 'N/A')}': {e}")
        return False

def _extract_validation_metadata(data_validation, cell_address: str, worksheet: Optional[Worksheet] = None) -> Dict[str, Any]:
    """Extract metadata from a DataValidation object."""
    try:
        validation_info = {
            "cell": cell_address,
            "has_validation": True,
            "validation_type": data_validation.type,
            "allow_blank": data_validation.allowBlank,
        }
        
        # Add operator for validation types that use it
        if data_validation.operator:
            validation_info["operator"] = data_validation.operator
        
        # Add optional fields if they exist
        if data_validation.prompt:
            validation_info["prompt"] = data_validation.prompt
        if data_validation.promptTitle:
            validation_info["prompt_title"] = data_validation.promptTitle
        if data_validation.error:
            validation_info["error_message"] = data_validation.error
        if data_validation.errorTitle:
            validation_info["error_title"] = data_validation.errorTitle
            
        # For list type validations (dropdown lists), extract allowed values
        if data_validation.type == "list" and data_validation.formula1:
            allowed_values = _extract_list_values(data_validation.formula1, worksheet)
            validation_info["allowed_values"] = allowed_values
            
        # For other validation types, include the formulas
        elif data_validation.formula1:
            validation_info["formula1"] = data_validation.formula1
            if data_validation.formula2:
                validation_info["formula2"] = data_validation.formula2
                
        return validation_info
        
    except Exception as e:
        logger.warning(f"Failed to extract validation metadata: {e}")
        return {
            "cell": cell_address,
            "has_validation": True,
            "validation_type": "unknown",
            "error": f"Failed to parse validation: {e}"
        }

def _extract_list_values(formula: str, worksheet: Optional[Worksheet] = None) -> List[str]:
    """Extract allowed values from a list validation formula."""
    try:
        # Remove quotes if present
        formula = formula.strip('"')
        
        # Handle comma-separated list
        if ',' in formula:
            # Split by comma and clean up each value
            values = [val.strip().strip('"') for val in formula.split(',')]
            return [val for val in values if val]  # Remove empty values
            
        # Handle range reference (e.g., "$A$1:$A$5" or "Sheet1!$A$1:$A$5")
        elif (':' in formula or formula.startswith('$')) and worksheet:
            try:
                # Remove potential leading '=' if it's a formula like '=Sheet1!$A$1:$A$5'
                range_ref = formula
                if formula.startswith('='):
                    range_ref = formula[1:]
                
                actual_values = []
                # worksheet[range_ref] can resolve ranges like "A1:A5" or "SheetName!A1:A5"
                # It returns a tuple of tuples of cells for ranges, or a single cell
                range_cells = worksheet[range_ref]
                
                # Handle single cell or range
                if hasattr(range_cells, 'value'):  # Single cell
                    if range_cells.value is not None:
                        actual_values.append(str(range_cells.value))
                else:  # Range of cells
                    for row_of_cells in range_cells:
                        # Handle case where row_of_cells might be a single cell
                        if hasattr(row_of_cells, 'value'):
                            if row_of_cells.value is not None:
                                actual_values.append(str(row_of_cells.value))
                        else:
                            for cell in row_of_cells:
                                if cell.value is not None:
                                    actual_values.append(str(cell.value))
                
                if actual_values:
                    return actual_values
                return [f"Range: {formula} (empty or unresolvable)"]
                
            except Exception as e:
                logger.warning(f"Could not resolve range '{formula}' for list validation: {e}")
                return [f"Range: {formula} (resolution error)"]
                
        # Handle range reference when worksheet not available
        elif ':' in formula or formula.startswith('$'):
            return [f"Range: {formula}"]
            
        # Single value
        else:
            return [formula.strip('"')]
            
    except Exception as e:
        logger.warning(f"Failed to parse list formula '{formula}': {e}")
        return [formula]  # Return original formula if parsing fails

def get_all_validation_ranges(worksheet: Worksheet) -> List[Dict[str, Any]]:
    """Get all data validation ranges in a worksheet.
    
    Returns:
        List of dictionaries containing validation range information
    """
    validations = []
    
    try:
        for dv in worksheet.data_validations.dataValidation:
            validation_info = {
                "ranges": str(dv.sqref),
                "validation_type": dv.type,
                "allow_blank": dv.allowBlank,
            }
            
            if dv.type == "list" and dv.formula1:
                validation_info["allowed_values"] = _extract_list_values(dv.formula1, worksheet)
                
            validations.append(validation_info)
            
    except Exception as e:
        logger.warning(f"Failed to get validation ranges: {e}")
        
    return validations 