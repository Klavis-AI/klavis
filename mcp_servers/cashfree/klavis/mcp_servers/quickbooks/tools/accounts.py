from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Minimal properties for account creation (required by QuickBooks)
account_properties_minimal = {
    "Name": {
        "type": "string",
        "description": "Account name (required, must be unique)"
    },
    "AccountType": {
        "type": "string",
        "description": "Account type classification. Valid values: Bank, Other Current Asset, Fixed Asset, Other Asset, Accounts Receivable, Equity, Expense, Other Expense, Cost of Goods Sold, Accounts Payable, Credit Card, Long Term Liability, Other Current Liability, Income, Other Income."
    }
}

# Account properties mapping (based on QuickBooks API documentation)
account_properties_user_define = {
    **account_properties_minimal,
    "Description": {
        "type": "string",
        "description": "User entered description for the account, which may include user entered information to guide bookkeepers/accountants in deciding what journal entries to post to the account"
    },
    "Active": {
        "type": "boolean",
        "description": "Whether or not the account is active. Inactive accounts may be hidden from most display purposes and may not be posted to"
    }
}

account_properties = {
    **account_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique QuickBooks account ID"
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
        "required": ["Name"]
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
            "Id": {"type": "string", "description": "The QuickBooks account ID"}
        },
        "required": ["Id"]
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
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "AccountType": {"type": "string", "description": "Filter by account type: Asset, Liability, Income, Expense, Equity"},
            "ActiveOnly": {"type": "boolean", "description": "Return only active accounts", "default": True}
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
        "required": ["Id", "Name"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT"})
)

search_accounts_tool = Tool(
    name="quickbooks_search_accounts",
    title="Search Accounts",
    description="Advanced Account Search - Search accounts with powerful filters including name, type, classification, status, and other criteria. Perfect for finding specific accounts based on various parameters",
    inputSchema={
        "type": "object",
        "properties": {
            "Name": {"type": "string", "description": "Search by account name (partial match)"},
            "AccountType": {"type": "string", "description": "Filter by account type: Bank, Other Current Asset, Fixed Asset, Other Asset, Accounts Receivable, Equity, Expense, Other Expense, Cost of Goods Sold, Accounts Payable, Credit Card, Long Term Liability, Other Current Liability, Income, Other Income"},
            "Classification": {"type": "string", "description": "Filter by classification: Asset, Liability, Income, Expense, Equity"},
            "Active": {"type": "boolean", "description": "Filter by active status"},
            "FullyQualifiedName": {"type": "string", "description": "Search by fully qualified name (partial match)"},
            "Description": {"type": "string", "description": "Search by description (partial match)"},

            # Currency filters
            "CurrencyRefValue": {"type": "string", "description": "Filter by currency code"},
            "CurrencyRefName": {"type": "string", "description": "Search by currency name (partial match)"},

            # Date filters
            "CreateTimeFrom": {"type": "string", "description": "Search accounts created from this date (YYYY-MM-DD format)"},
            "CreateTimeTo": {"type": "string", "description": "Search accounts created to this date (YYYY-MM-DD format)"},
            "LastUpdatedTimeFrom": {"type": "string", "description": "Search accounts last updated from this date (YYYY-MM-DD format)"},
            "LastUpdatedTimeTo": {"type": "string", "description": "Search accounts last updated to this date (YYYY-MM-DD format)"},

            # Pagination
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_ACCOUNT", "readOnlyHint": True})
)


def mcp_object_to_account_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks account data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    account_data = {}

    # Basic account information - direct copy
    for field in ['Name', 'AccountType', 'Description', 'Active']:
        if field in kwargs:
            account_data[field] = kwargs[field]

    return account_data


def account_data_to_mcp_object(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks account data format to MCP object format.
    This function flattens the nested QuickBooks structure to the flat format expected by MCP tools.
    """
    mcp_object = {}

    # Copy basic fields if present
    field_mappings = {
        'Id': 'Id',
        'Name': 'Name',
        'AccountType': 'AccountType',
        'Description': 'Description',
        'Active': 'Active',
        'Classification': 'Classification',
        'FullyQualifiedName': 'FullyQualifiedName',
        'CurrentBalance': 'CurrentBalance'
    }

    for qb_field, mcp_field in field_mappings.items():
        if qb_field in account_data:
            mcp_object[mcp_field] = account_data[qb_field]

    # Currency reference
    if 'CurrencyRef' in account_data and isinstance(account_data['CurrencyRef'], dict):
        if 'value' in account_data['CurrencyRef']:
            mcp_object['CurrencyRefValue'] = account_data['CurrencyRef']['value']
        if 'name' in account_data['CurrencyRef']:
            mcp_object['CurrencyRefName'] = account_data['CurrencyRef']['name']

    # MetaData fields
    if 'MetaData' in account_data and isinstance(account_data['MetaData'], dict):
        metadata = account_data['MetaData']
        if 'CreateTime' in metadata:
            mcp_object['CreateTime'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            mcp_object['LastUpdatedTime'] = metadata['LastUpdatedTime']

    # SyncToken
    if 'SyncToken' in account_data:
        mcp_object['SyncToken'] = account_data['SyncToken']

    return mcp_object


class AccountManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_account(self, **kwargs) -> Dict[str, Any]:
        """Create a new account with comprehensive property support."""
        account_data = mcp_object_to_account_data(**kwargs)

        response = await self.client._post('account', account_data)
        return account_data_to_mcp_object(response['Account'])

    async def get_account(self, Id: str) -> Dict[str, Any]:
        """Get a specific account by ID."""
        response = await self.client._get(f"account/{Id}")
        return account_data_to_mcp_object(response['Account'])

    async def list_accounts(self, MaxResults: int = 100, AccountType: str = None, ActiveOnly: bool = True) -> List[Dict[str, Any]]:
        """List all accounts with comprehensive properties and pagination support."""
        query = "SELECT * FROM Account"

        conditions = []
        if ActiveOnly:
            conditions.append("Active = true")
        if AccountType:
            conditions.append(f"Classification = '{AccountType}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" MAXRESULTS {MaxResults}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no accounts are returned
        if 'Account' not in response['QueryResponse']:
            return []

        accounts = response['QueryResponse']['Account']
        return [account_data_to_mcp_object(account) for account in accounts]

    async def update_account(self, **kwargs) -> Dict[str, Any]:
        """Update an existing account with comprehensive property support."""
        account_id = kwargs.get('Id')
        if not account_id:
            raise ValueError("Id is required for updating an account")

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
            Name: Search by account name (partial match)
            AccountType: Filter by account type
            Classification: Filter by classification (Asset, Liability, Income, Expense, Equity)
            Active: Filter by active status
            FullyQualifiedName: Search by fully qualified name (partial match)
            Description: Search by description (partial match)

            # Balance filters
            MinCurrentBalance/MaxCurrentBalance: Filter by current balance range

            # Currency filters
            CurrencyRefValue: Filter by currency code
            CurrencyRefName: Search by currency name (partial match)

            # Date filters
            CreateTimeFrom/CreateTimeTo: Filter by creation date range
            LastUpdatedTimeFrom/LastUpdatedTimeTo: Filter by last updated date range

            MaxResults: Maximum number of results to return (default: 100)
            StartPosition: Starting position for pagination (default: 1)

        Returns:
            List of accounts matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters
        if kwargs.get('AccountType'):
            conditions.append(f"AccountType = '{kwargs['AccountType']}'")

        if kwargs.get('Classification'):
            conditions.append(f"Classification = '{kwargs['Classification']}'")

        if kwargs.get('Active') is not None:
            conditions.append(f"Active = {str(kwargs['Active']).lower()}")

        if kwargs.get('CurrencyRefValue'):
            conditions.append(
                f"CurrencyRef.value = '{kwargs['CurrencyRefValue']}'")

        # Name searches (partial match) - we'll need to post-filter these due to QB API limitations
        partial_match_filters = {}
        
        if kwargs.get('Name'):
            partial_match_filters['Name'] = kwargs['Name'].lower()

        if kwargs.get('FullyQualifiedName'):
            partial_match_filters['FullyQualifiedName'] = kwargs['FullyQualifiedName'].lower()

        if kwargs.get('Description'):
            partial_match_filters['Description'] = kwargs['Description'].lower()

        if kwargs.get('CurrencyRefName'):
            partial_match_filters['CurrencyRefName'] = kwargs['CurrencyRefName'].lower()

        # Balance range filters
        if kwargs.get('MinCurrentBalance') is not None:
            conditions.append(
                f"CurrentBalance >= {kwargs['MinCurrentBalance']}")
        if kwargs.get('MaxCurrentBalance') is not None:
            conditions.append(
                f"CurrentBalance <= {kwargs['MaxCurrentBalance']}")

        # Date range filters
        if kwargs.get('CreateTimeFrom'):
            conditions.append(
                f"MetaData.CreateTime >= '{kwargs['CreateTimeFrom']}'")
        if kwargs.get('CreateTimeTo'):
            conditions.append(
                f"MetaData.CreateTime <= '{kwargs['CreateTimeTo']}'")

        if kwargs.get('LastUpdatedTimeFrom'):
            conditions.append(
                f"MetaData.LastUpdatedTime >= '{kwargs['LastUpdatedTimeFrom']}'")
        if kwargs.get('LastUpdatedTimeTo'):
            conditions.append(
                f"MetaData.LastUpdatedTime <= '{kwargs['LastUpdatedTimeTo']}'")

        # Build the query
        query = "SELECT * FROM Account"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add pagination
        max_results = kwargs.get('MaxResults', 100)
        start_position = kwargs.get('StartPosition', 1)

        query += f" STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no accounts are returned
        if 'Account' not in response['QueryResponse']:
            return []

        accounts = response['QueryResponse']['Account']

        # Apply post-filtering for partial matches
        if partial_match_filters:
            filtered_accounts = []
            for account in accounts:
                should_include = True

                for field, search_value in partial_match_filters.items():
                    if field == 'Name' and 'Name' in account:
                        if search_value not in account['Name'].lower():
                            should_include = False
                            break
                    elif field == 'FullyQualifiedName' and 'FullyQualifiedName' in account:
                        if search_value not in account['FullyQualifiedName'].lower():
                            should_include = False
                            break
                    elif field == 'Description' and 'Description' in account:
                        if search_value not in account['Description'].lower():
                            should_include = False
                            break
                    elif field == 'CurrencyRefName' and 'CurrencyRef' in account and isinstance(account['CurrencyRef'], dict):
                        currency_name = account['CurrencyRef'].get(
                            'name', '').lower()
                        if search_value not in currency_name:
                            should_include = False
                            break

                if should_include:
                    filtered_accounts.append(account)

            accounts = filtered_accounts

        return [account_data_to_mcp_object(account) for account in accounts]


# Export tools
tools = [create_account_tool, get_account_tool,
         list_accounts_tool, search_accounts_tool, update_account_tool]
