from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Simplified input properties for account creation
account_properties_minimal = {
    "name": {
        "type": "string",
        "description": "Account name (required, must be unique)"
    },
    "type": {
        "type": "string",
        "description": "Account type. Valid values: Bank, Other Current Asset, Fixed Asset, Other Asset, Accounts Receivable, Equity, Expense, Other Expense, Cost of Goods Sold, Accounts Payable, Credit Card, Long Term Liability, Other Current Liability, Income, Other Income"
    }
}

# Full account properties for create/update
account_properties_user_define = {
    **account_properties_minimal,
    "description": {
        "type": "string",
        "description": "Description of the account to help with bookkeeping decisions"
    },
    "is_active": {
        "type": "boolean",
        "description": "Whether the account is active (inactive accounts are hidden and cannot be posted to)"
    }
}

account_properties = {
    **account_properties_user_define,
    "id": {
        "type": "string",
        "description": "The unique account ID"
    }
}

# MCP Tool definitions
create_account_tool = Tool(
    name="quickbooks_create_account",
    title="Create Account",
    description="Create a new account in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": account_properties_minimal,
        "required": ["name"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT"})
)

get_account_tool = Tool(
    name="quickbooks_get_account",
    title="Get Account",
    description="Get a specific account by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The account ID"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT", "readOnlyHint": True})
)

list_accounts_tool = Tool(
    name="quickbooks_list_accounts",
    title="List Accounts",
    description="List all chart of accounts from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "type": {"type": "string", "description": "Filter by account type: Asset, Liability, Income, Expense, Equity"},
            "active_only": {"type": "boolean", "description": "Return only active accounts", "default": True}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT", "readOnlyHint": True})
)

update_account_tool = Tool(
    name="quickbooks_update_account",
    title="Update Account",
    description="Update an existing account in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": account_properties,
        "required": ["id", "name"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT"})
)

search_accounts_tool = Tool(
    name="quickbooks_search_accounts",
    title="Search Accounts",
    description="Search accounts with filters including name, type, classification, and status",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Search by account name (partial match)"},
            "type": {"type": "string", "description": "Filter by account type: Bank, Other Current Asset, Fixed Asset, Other Asset, Accounts Receivable, Equity, Expense, Other Expense, Cost of Goods Sold, Accounts Payable, Credit Card, Long Term Liability, Other Current Liability, Income, Other Income"},
            "classification": {"type": "string", "description": "Filter by classification: Asset, Liability, Income, Expense, Equity"},
            "is_active": {"type": "boolean", "description": "Filter by active status"},
            "currency": {"type": "string", "description": "Filter by currency code (e.g., USD, EUR)"},
            "created_after": {"type": "string", "description": "Filter accounts created after this date (YYYY-MM-DD)"},
            "created_before": {"type": "string", "description": "Filter accounts created before this date (YYYY-MM-DD)"},
            "updated_after": {"type": "string", "description": "Filter accounts updated after this date (YYYY-MM-DD)"},
            "updated_before": {"type": "string", "description": "Filter accounts updated before this date (YYYY-MM-DD)"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "start_position": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT", "readOnlyHint": True})
)


def mcp_object_to_account_data(**kwargs) -> Dict[str, Any]:
    """
    Convert simplified MCP input to QuickBooks account data format.
    Maps user-friendly field names to QuickBooks API field names.
    """
    account_data = {}

    # Map simplified field names to QuickBooks API names
    field_mappings = {
        'name': 'Name',
        'type': 'AccountType',
        'description': 'Description',
        'is_active': 'Active',
    }

    for simple_name, qb_name in field_mappings.items():
        if simple_name in kwargs:
            account_data[qb_name] = kwargs[simple_name]

    return account_data


def account_data_to_mcp_object(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks account data format to simplified MCP object format.
    Uses cleaner, more intuitive field names for better usability.
    """
    result = {}

    # Core identification
    if 'Id' in account_data:
        result['id'] = account_data['Id']
    if 'Name' in account_data:
        result['name'] = account_data['Name']
    if 'FullyQualifiedName' in account_data:
        result['full_name'] = account_data['FullyQualifiedName']
    if 'Description' in account_data:
        result['description'] = account_data['Description']

    # Account classification
    if 'AccountType' in account_data:
        result['type'] = account_data['AccountType']
    if 'Classification' in account_data:
        result['classification'] = account_data['Classification']

    # Status and balance
    if 'Active' in account_data:
        result['is_active'] = account_data['Active']
    if 'CurrentBalance' in account_data:
        result['balance'] = account_data['CurrentBalance']

    # Currency (simplified)
    if 'CurrencyRef' in account_data and isinstance(account_data['CurrencyRef'], dict):
        result['currency'] = account_data['CurrencyRef'].get('value')

    # Timestamps
    if 'MetaData' in account_data and isinstance(account_data['MetaData'], dict):
        metadata = account_data['MetaData']
        if 'CreateTime' in metadata:
            result['created_at'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            result['updated_at'] = metadata['LastUpdatedTime']

    return result


class AccountManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_account(self, **kwargs) -> Dict[str, Any]:
        """Create a new account."""
        account_data = mcp_object_to_account_data(**kwargs)

        response = await self.client._post('account', account_data)
        return account_data_to_mcp_object(response['Account'])

    async def get_account(self, id: str) -> Dict[str, Any]:
        """Get a specific account by ID."""
        response = await self.client._get(f"account/{id}")
        return account_data_to_mcp_object(response['Account'])

    async def list_accounts(self, max_results: int = 100, type: str = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all accounts with optional filters."""
        query = "SELECT * FROM Account"

        conditions = []
        if active_only:
            conditions.append("Active = true")
        if type:
            conditions.append(f"Classification = '{type}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no accounts are returned
        if 'Account' not in response['QueryResponse']:
            return []

        accounts = response['QueryResponse']['Account']
        return [account_data_to_mcp_object(account) for account in accounts]

    async def update_account(self, **kwargs) -> Dict[str, Any]:
        """Update an existing account."""
        account_id = kwargs.get('id')
        if not account_id:
            raise ValueError("id is required for updating an account")

        # Auto-fetch current sync token
        current_account_response = await self.client._get(f"account/{account_id}")
        sync_token = current_account_response.get(
            'Account', {}).get('SyncToken', '0')

        account_data = mcp_object_to_account_data(**kwargs)
        account_data.update({
            "Id": account_id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('account', account_data)
        return account_data_to_mcp_object(response['Account'])

    async def search_accounts(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search accounts with various filters and pagination support.

        Args:
            name: Search by account name (partial match)
            type: Filter by account type
            classification: Filter by classification (Asset, Liability, Income, Expense, Equity)
            is_active: Filter by active status
            currency: Filter by currency code

            # Date filters
            created_after/created_before: Filter by creation date range
            updated_after/updated_before: Filter by last updated date range

            max_results: Maximum number of results to return (default: 100)
            start_position: Starting position for pagination (default: 1)

        Returns:
            List of accounts matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters
        if kwargs.get('type'):
            conditions.append(f"AccountType = '{kwargs['type']}'")

        if kwargs.get('classification'):
            conditions.append(f"Classification = '{kwargs['classification']}'")

        if kwargs.get('is_active') is not None:
            conditions.append(f"Active = {str(kwargs['is_active']).lower()}")

        if kwargs.get('currency'):
            conditions.append(f"CurrencyRef.value = '{kwargs['currency']}'")

        # Name searches (partial match) - we'll need to post-filter these due to QB API limitations
        partial_match_filters = {}
        
        if kwargs.get('name'):
            partial_match_filters['Name'] = kwargs['name'].lower()

        # Date range filters
        if kwargs.get('created_after'):
            conditions.append(f"MetaData.CreateTime >= '{kwargs['created_after']}'")
        if kwargs.get('created_before'):
            conditions.append(f"MetaData.CreateTime <= '{kwargs['created_before']}'")

        if kwargs.get('updated_after'):
            conditions.append(f"MetaData.LastUpdatedTime >= '{kwargs['updated_after']}'")
        if kwargs.get('updated_before'):
            conditions.append(f"MetaData.LastUpdatedTime <= '{kwargs['updated_before']}'")

        # Build the query
        query = "SELECT * FROM Account"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add pagination
        max_results = kwargs.get('max_results', 100)
        start_position = kwargs.get('start_position', 1)

        query += f" STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no accounts are returned
        if 'Account' not in response['QueryResponse']:
            return []

        accounts = response['QueryResponse']['Account']

        # Apply post-filtering for partial matches (name search)
        if partial_match_filters:
            filtered_accounts = []
            for account in accounts:
                should_include = True

                if 'Name' in partial_match_filters and 'Name' in account:
                    if partial_match_filters['Name'] not in account['Name'].lower():
                        should_include = False

                if should_include:
                    filtered_accounts.append(account)

            accounts = filtered_accounts

        return [account_data_to_mcp_object(account) for account in accounts]


# Export tools
tools = [create_account_tool, get_account_tool,
         list_accounts_tool, search_accounts_tool, update_account_tool]
