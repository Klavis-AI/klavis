import logging
from typing import Any, Dict, List, Optional
from .base import get_salesforce_conn, handle_salesforce_error

# Configure logging
logger = logging.getLogger(__name__)

async def get_reports(folder_id: Optional[str] = None, limit: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get reports, optionally filtered by folder."""
    logger.info(f"Executing tool: get_reports with folder_id: {folder_id}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Name', 'DeveloperName', 'FolderName', 'Type', 'Format',
                     'CreatedDate', 'LastModifiedDate', 'LastRunDate', 'OwnerId']
        
        field_list = ', '.join(fields)
        where_clause = f" WHERE FolderId = '{folder_id}'" if folder_id else ""
        query = f"SELECT {field_list} FROM Report{where_clause} ORDER BY Name LIMIT {limit}"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_reports: {e}")
        raise e

async def get_report_by_id(report_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get a specific report by ID."""
    logger.info(f"Executing tool: get_report_by_id with report_id: {report_id}")
    try:
        sf = get_salesforce_conn()
        
        if not fields:
            fields = ['Id', 'Name', 'DeveloperName', 'FolderName', 'Type', 'Format',
                     'Description', 'CreatedDate', 'LastModifiedDate', 'LastRunDate', 'OwnerId']
        
        field_list = ', '.join(fields)
        query = f"SELECT {field_list} FROM Report WHERE Id = '{report_id}'"
        
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool get_report_by_id: {e}")
        raise e

async def run_report(report_id: str, include_details: bool = True) -> Dict[str, Any]:
    """Run a report and get its results."""
    logger.info(f"Executing tool: run_report with report_id: {report_id}")
    try:
        sf = get_salesforce_conn()
        
        # Use Analytics API to run the report
        report_url = f"analytics/reports/{report_id}"
        if include_details:
            report_url += "?includeDetails=true"
        
        result = sf.restful(report_url, method='GET')
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tool run_report: {e}")
        raise e 