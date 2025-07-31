from typing import Any, Dict, List
from datetime import datetime, timedelta

from mcp.types import Tool

# MCP Tool definitions
profit_loss_report_tool = Tool(
    name="profit_loss_report",
    description="Generate profit and loss report from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date", "description": "Start date for report (YYYY-MM-DD)"},
            "end_date": {"type": "string", "format": "date", "description": "End date for report (YYYY-MM-DD)"},
            "summarize_column_by": {"type": "string", "description": "Summarize by", "default": "Month", "enum": ["Month", "Quarter", "Year"]}
        },
        "additionalProperties": False
    }
)

balance_sheet_report_tool = Tool(
    name="balance_sheet_report",
    description="Generate balance sheet report from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "as_of_date": {"type": "string", "format": "date", "description": "As of date for balance sheet (YYYY-MM-DD)"},
            "summarize_column_by": {"type": "string", "description": "Summarize by", "default": "Month", "enum": ["Month", "Quarter", "Year"]}
        },
        "additionalProperties": False
    }
)

# Tool implementations
async def profit_loss_report(client=None, start_date: str = None, end_date: str = None, summarize_column_by: str = "Month") -> Dict[str, Any]:
    """Generate profit and loss report from QuickBooks."""
    if not client or not client.is_configured():
        raise ValueError("QuickBooks client not configured")
    
    try:
        from quickbooks.objects import Account
        
        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        accounts = Account.all(qb=client.client)
        
        income_accounts = [a for a in accounts if a.AccountType == "Income" and a.Active]
        expense_accounts = [a for a in accounts if a.AccountType == "Expense" and a.Active]
        
        # Group by account type
        income = sum(float(a.CurrentBalance or 0) for a in income_accounts)
        expenses = sum(float(a.CurrentBalance or 0) for a in expense_accounts)
        
        return {
            "report_type": "Profit and Loss",
            "period": f"{start_date} to {end_date}",
            "total_income": income,
            "total_expenses": expenses,
            "net_income": income - expenses,
            "summarize_column_by": summarize_column_by,
            "income_accounts": [
                {
                    "name": a.Name,
                    "balance": float(a.CurrentBalance or 0)
                }
                for a in income_accounts[:10]  # Limit to top 10
            ],
            "expense_accounts": [
                {
                    "name": a.Name,
                    "balance": float(a.CurrentBalance or 0)
                }
                for a in expense_accounts[:10]  # Limit to top 10
            ]
        }
    except Exception as e:
        raise RuntimeError(f"Failed to generate profit and loss report: {str(e)}")

async def balance_sheet_report(client=None, as_of_date: str = None, summarize_column_by: str = "Month") -> Dict[str, Any]:
    """Generate balance sheet report from QuickBooks."""
    if not client or not client.is_configured():
        raise ValueError("QuickBooks client not configured")
    
    try:
        from quickbooks.objects import Account
        
        # Default to current date if not provided
        if not as_of_date:
            as_of_date = datetime.now().strftime('%Y-%m-%d')
        
        accounts = Account.all(qb=client.client)
        
        # Group accounts by classification
        assets = [a for a in accounts if a.Classification == "Asset" and a.Active]
        liabilities = [a for a in accounts if a.Classification == "Liability" and a.Active]
        equity = [a for a in accounts if a.Classification == "Equity" and a.Active]
        
        total_assets = sum(float(a.CurrentBalance or 0) for a in assets)
        total_liabilities = sum(float(a.CurrentBalance or 0) for a in liabilities)
        total_equity = sum(float(a.CurrentBalance or 0) for a in equity)
        
        return {
            "report_type": "Balance Sheet",
            "as_of_date": as_of_date,
            "assets": {
                "total": total_assets,
                "accounts": [
                    {"name": a.Name, "balance": float(a.CurrentBalance or 0)}
                    for a in assets[:10]
                ]
            },
            "liabilities": {
                "total": total_liabilities,
                "accounts": [
                    {"name": a.Name, "balance": float(a.CurrentBalance or 0)}
                    for a in liabilities[:10]
                ]
            },
            "equity": {
                "total": total_equity,
                "accounts": [
                    {"name": a.Name, "balance": float(a.CurrentBalance or 0)}
                    for a in equity[:10]
                ]
            },
            "liabilities_plus_equity": total_liabilities + total_equity,
            "summarize_column_by": summarize_column_by
        }
    except Exception as e:
        raise RuntimeError(f"Failed to generate balance sheet report: {str(e)}")

# Export tools and implementations
tools = [profit_loss_report_tool, balance_sheet_report_tool]
tool_map = {
    "profit_loss_report": profit_loss_report,
    "balance_sheet_report": balance_sheet_report
}