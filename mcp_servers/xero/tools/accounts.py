import logging
from typing import Dict, Any
from .base import make_xero_api_request

logger = logging.getLogger(__name__)

async def xero_list_accounts(account_type: str = None, status: str = None) -> Dict[str, Any]:
    """Retrieve a list of accounts from Xero."""
    try:
        # Build endpoint with optional filters
        endpoint = "Accounts"
        filters = []
        
        if account_type:
            valid_types = [
                "BANK", "CURRENT", "CURRENTLIABILITY", "DEPRECIATN", "DIRECTCOSTS", 
                "EQUITY", "EXPENSE", "FIXED", "INVENTORY", "LIABILITY", "NONCURRENT", 
                "OTHERINCOME", "OVERHEADS", "PREPAYMENT", "REVENUE", "SALES", 
                "TERMLIABILITY", "PAYGLIABILITY"
            ]
            if account_type.upper() in valid_types:
                filters.append(f"Type%3D%22{account_type.upper()}%22")
        
        if status:
            valid_statuses = ["ACTIVE", "ARCHIVED"]
            if status.upper() in valid_statuses:
                filters.append(f"Status%3D%22{status.upper()}%22")
        
        if filters:
            endpoint += "?where=" + "%20AND%20".join(filters)
        
        # Get accounts from API
        response = await make_xero_api_request(endpoint)
        
        accounts_list = []
        if response.get("Accounts"):
            for account in response["Accounts"]:
                account_data = {
                    "account_id": account.get("AccountID"),
                    "code": account.get("Code"),
                    "name": account.get("Name"),
                    "type": account.get("Type"),
                    "bank_account_number": account.get("BankAccountNumber"),
                    "status": account.get("Status"),
                    "description": account.get("Description"),
                    "bank_account_type": account.get("BankAccountType"),
                    "currency_code": account.get("CurrencyCode"),
                    "tax_type": account.get("TaxType"),
                    "enable_payments_to_account": account.get("EnablePaymentsToAccount"),
                    "show_in_expense_claims": account.get("ShowInExpenseClaims"),
                    "class": account.get("Class"),
                    "system_account": account.get("SystemAccount"),
                    "reporting_code": account.get("ReportingCode"),
                    "reporting_code_name": account.get("ReportingCodeName"),
                    "has_attachments": account.get("HasAttachments"),
                    "updated_date_utc": account.get("UpdatedDateUTC"),
                    "add_to_watchlist": account.get("AddToWatchlist")
                }
                
                accounts_list.append(account_data)
        
        return {
            "accounts": accounts_list,
            "total_returned": len(accounts_list),
            "account_type_filter": account_type,
            "status_filter": status
        }
            
    except Exception as e:
        logger.error(f"Error retrieving accounts: {e}")
        return {"error": f"Failed to retrieve accounts: {str(e)}"}