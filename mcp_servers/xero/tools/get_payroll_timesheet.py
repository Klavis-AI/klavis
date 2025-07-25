import logging
from typing import Dict, Any
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_get_payroll_timesheet(
    timesheet_id: str
) -> Dict[str, Any]:
    """Retrieve an existing Payroll Timesheet from Xero."""
    try:
        # Make API request to get specific timesheet
        response = await make_xero_api_request(f"payroll.xro/1.0/Timesheets/{timesheet_id}")
        
        if response.get("Timesheets") and len(response["Timesheets"]) > 0:
            timesheet = response["Timesheets"][0]
            
            # Extract timesheet lines for response
            timesheet_lines = []
            if timesheet.get("TimesheetLines"):
                for line in timesheet["TimesheetLines"]:
                    timesheet_lines.append({
                        "timesheet_line_id": line.get("TimesheetLineID"),
                        "tracking_item_id": line.get("TrackingItemID"),
                        "number_of_units": line.get("NumberOfUnits"),
                        "earnings_rate_id": line.get("EarningsRateID")
                    })
            
            return {
                "success": True,
                "message": "Timesheet retrieved successfully",
                "timesheet": {
                    "timesheet_id": timesheet.get("TimesheetID"),
                    "payroll_calendar_id": timesheet.get("PayrollCalendarID"),
                    "employee_id": timesheet.get("EmployeeID"),
                    "start_date": timesheet.get("StartDate"),
                    "end_date": timesheet.get("EndDate"),
                    "status": timesheet.get("Status"),
                    "hours": timesheet.get("Hours"),
                    "timesheet_lines": timesheet_lines,
                    "updated_date_utc": timesheet.get("UpdatedDateUTC")
                }
            }
        else:
            return {
                "success": False,
                "error": "Timesheet not found",
                "raw_response": response
            }
            
    except Exception as e:
        logger.error(f"Error retrieving timesheet: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve timesheet: {str(e)}"
        }