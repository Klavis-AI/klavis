from typing import Any, Dict, List
from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

# MCP Tool definitions
list_accounts_tool = Tool(
    name="list_accounts",
    description="List all chart of accounts from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "account_type": {"type": "string", "description": "Filter by account type: Asset, Liability, Income, Expense, Equity"},
            "active_only": {"type": "boolean", "description": "Return only active accounts", "default": True}
        }
    }
)

get_account_tool = Tool(
    name="get_account",
    description="Get a specific account by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "account_id": {"type": "string", "description": "The QuickBooks account ID"}
        },
        "required": ["account_id"]
    }
)

create_account_tool = Tool(
    name="create_account",
    description="Create a new account in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Account name (required, must be unique)"},
            "account_type": {"type": "string", "description": "Account type: Asset, Liability, Income, Expense, Equity (required)"},
            "account_subtype": {"type": "string", "description": "Account sub-type based on the AccountType"},
            "acct_num": {"type": "string", "description": "User-defined account number"},
            "description": {"type": "string", "description": "Description of the account"},
            "parent_ref": {"type": "string", "description": "Parent account ID (if creating sub-account)"}
        },
        "required": ["name", "account_type"]
    }
)

update_account_tool = Tool(
    name="update_account",
    description="Update an existing account in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "account_id": {"type": "string", "description": "The QuickBooks account ID (required)"},
            "name": {"type": "string", "description": "Updated account name (optional)"},
            "account_type": {"type": "string", "description": "Updated account type: Asset, Liability, Income, Expense, Equity (optional)"},
            "account_subtype": {"type": "string", "description": "Updated account sub-type based on the AccountType (optional)"},
            "acct_num": {"type": "string", "description": "Updated user-defined account number (optional)"},
            "description": {"type": "string", "description": "Updated description of the account (optional)"},
            "parent_ref": {"type": "string", "description": "Updated parent account ID for sub-account (optional)"},
            "active": {"type": "boolean", "description": "Whether the account is active (optional)"}
        },
        "required": ["account_id"]
    }
)

class AccountManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def list_accounts(self, max_results: int = 100, **filters) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Account"
        where_clauses = []
        for key, value in filters.items():
            if key not in ['max_results', 'active_only']:
                where_clauses.append(f"{key} = '{value}'")
        if filters.get('active_only'):
            where_clauses.append("Active = true")
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += f" MAXRESULTS {max_results}"
        return await self.client._get('query', params={'query': query})

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        return await self.client._get(f"account/{account_id}")

    async def create_account(self, **kwargs) -> Dict[str, Any]:
        return await self.client._post('account', kwargs)

    async def update_account(self, account_id: str, **kwargs) -> Dict[str, Any]:
        kwargs["Id"] = account_id
        kwargs["sparse"] = True
        return await self.client._post('account', kwargs)

tools = [list_accounts_tool, get_account_tool, create_account_tool, update_account_tool]
