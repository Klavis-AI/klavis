from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Minimal properties for vendor creation
vendor_properties_minimal = {
    "display_name": {
        "type": "string",
        "description": "Display name (must be unique)"
    },
    "first_name": {
        "type": "string",
        "description": "First/given name"
    },
    "last_name": {
        "type": "string",
        "description": "Last/family name"
    }
}

# Vendor properties mapping
vendor_properties_user_define = {
    **vendor_properties_minimal,
    "middle_name": {
        "type": "string",
        "description": "Middle name"
    },
    "company": {
        "type": "string",
        "description": "Company name"
    },
    "email": {
        "type": "string",
        "description": "Email address"
    },
    "phone": {
        "type": "string",
        "description": "Phone number"
    },
    "website": {
        "type": "string",
        "description": "Website URL"
    },
    "check_name": {
        "type": "string",
        "description": "Name printed on checks"
    },
    "is_1099_vendor": {
        "type": "boolean",
        "description": "1099 independent contractor"
    },
    "cost_rate": {
        "type": "number",
        "description": "Pay rate"
    },
    "bill_rate": {
        "type": "number",
        "description": "Hourly billing rate"
    },
    "tax_id": {
        "type": "string",
        "description": "Tax ID (SSN or EIN)"
    },
    "account_number": {
        "type": "string",
        "description": "Account number"
    },
    "currency": {
        "type": "string",
        "description": "Currency code (e.g., USD)"
    },
    "street": {
        "type": "string",
        "description": "Street address"
    },
    "street2": {
        "type": "string",
        "description": "Street address line 2"
    },
    "city": {
        "type": "string",
        "description": "City"
    },
    "state": {
        "type": "string",
        "description": "State/province"
    },
    "postal_code": {
        "type": "string",
        "description": "Postal code"
    },
    "country": {
        "type": "string",
        "description": "Country"
    }
}

vendor_properties = {
    **vendor_properties_user_define,
    "id": {
        "type": "string",
        "description": "Vendor ID"
    }
}

# MCP Tool definitions
create_vendor_tool = Tool(
    name="quickbooks_create_vendor",
    title="Create Vendor",
    description="Create a new vendor. Requires display_name or first_name/last_name.",
    inputSchema={
        "type": "object",
        "properties": vendor_properties_user_define,
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

get_vendor_tool = Tool(
    name="quickbooks_get_vendor",
    title="Get Vendor",
    description="Get a vendor by ID",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Vendor ID"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

list_vendors_tool = Tool(
    name="quickbooks_list_vendors",
    title="List Vendors",
    description="List all vendors",
    inputSchema={
        "type": "object",
        "properties": {
            "active_only": {"type": "boolean", "description": "Return only active vendors (default: true)"},
            "max_results": {"type": "integer", "description": "Maximum results (default: 100)"}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

search_vendors_tool = Tool(
    name="quickbooks_search_vendors",
    title="Search Vendors",
    description="Search vendors with filters",
    inputSchema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Search by name (partial match)"},
            "display_name": {"type": "string", "description": "Search by display name"},
            "company": {"type": "string", "description": "Search by company name"},
            "first_name": {"type": "string", "description": "Search by first name"},
            "last_name": {"type": "string", "description": "Search by last name"},
            "email": {"type": "string", "description": "Search by email"},
            "phone": {"type": "string", "description": "Search by phone"},
            "is_active": {"type": "boolean", "description": "Filter by active status"},
            "is_1099_vendor": {"type": "boolean", "description": "Filter by 1099 status"},
            "account_number": {"type": "string", "description": "Search by account number"},
            "max_results": {"type": "integer", "description": "Maximum results (default: 100)"},
            "start_position": {"type": "integer", "description": "Starting position (default: 1)"}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

update_vendor_tool = Tool(
    name="quickbooks_update_vendor",
    title="Update Vendor",
    description="Update a vendor",
    inputSchema={
        "type": "object",
        "properties": vendor_properties,
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

activate_vendor_tool = Tool(
    name="quickbooks_activate_vendor",
    title="Activate Vendor",
    description="Activate a vendor",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Vendor ID to activate"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

deactivate_vendor_tool = Tool(
    name="quickbooks_deactivate_vendor",
    title="Deactivate Vendor",
    description="Deactivate a vendor",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Vendor ID to deactivate"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)


def mcp_object_to_vendor_data(**kwargs) -> Dict[str, Any]:
    """
    Convert simplified MCP input format to QuickBooks vendor data format.
    """
    vendor_data = {}

    # Field mappings: simplified name -> QB field name
    direct_mappings = {
        'display_name': 'DisplayName',
        'first_name': 'GivenName',
        'middle_name': 'MiddleName',
        'last_name': 'FamilyName',
        'company': 'CompanyName',
        'check_name': 'PrintOnCheckName',
        'is_1099_vendor': 'Vendor1099',
        'cost_rate': 'CostRate',
        'bill_rate': 'BillRate',
        'tax_id': 'TaxIdentifier',
        'account_number': 'AcctNum',
        'is_active': 'Active',
    }

    for simple_name, qb_name in direct_mappings.items():
        if simple_name in kwargs and kwargs[simple_name] is not None:
            vendor_data[qb_name] = kwargs[simple_name]

    # Email address
    if kwargs.get('email'):
        vendor_data['PrimaryEmailAddr'] = {'Address': kwargs['email']}

    # Phone number
    if kwargs.get('phone'):
        vendor_data['PrimaryPhone'] = {'FreeFormNumber': kwargs['phone']}

    # Website
    if kwargs.get('website'):
        vendor_data['WebAddr'] = {'URI': kwargs['website']}

    # Currency
    if kwargs.get('currency'):
        vendor_data['CurrencyRef'] = {'value': kwargs['currency']}

    # Address fields
    address_mappings = {
        'street': 'Line1',
        'street2': 'Line2',
        'city': 'City',
        'state': 'CountrySubDivisionCode',
        'postal_code': 'PostalCode',
        'country': 'Country',
    }

    bill_addr = {}
    for simple_name, qb_name in address_mappings.items():
        if kwargs.get(simple_name):
            bill_addr[qb_name] = kwargs[simple_name]

    if bill_addr:
        vendor_data['BillAddr'] = bill_addr

    return vendor_data


def vendor_data_to_mcp_object(vendor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks vendor data format to simplified MCP object format.
    Uses cleaner, more intuitive field names for better usability.
    """
    result = {}

    # Core identification
    if 'Id' in vendor_data:
        result['id'] = vendor_data['Id']
    if 'DisplayName' in vendor_data:
        result['display_name'] = vendor_data['DisplayName']
    if 'CompanyName' in vendor_data:
        result['company'] = vendor_data['CompanyName']
    if 'PrintOnCheckName' in vendor_data:
        result['check_name'] = vendor_data['PrintOnCheckName']

    # Personal name fields
    name_parts = {}
    if 'GivenName' in vendor_data:
        name_parts['first'] = vendor_data['GivenName']
    if 'MiddleName' in vendor_data:
        name_parts['middle'] = vendor_data['MiddleName']
    if 'FamilyName' in vendor_data:
        name_parts['last'] = vendor_data['FamilyName']
    if 'Title' in vendor_data:
        name_parts['title'] = vendor_data['Title']
    if 'Suffix' in vendor_data:
        name_parts['suffix'] = vendor_data['Suffix']
    if name_parts:
        result['name'] = name_parts

    # Contact information
    contact = {}
    if 'PrimaryEmailAddr' in vendor_data:
        email = vendor_data['PrimaryEmailAddr']
        contact['email'] = email.get('Address') if isinstance(email, dict) else email
    if 'PrimaryPhone' in vendor_data:
        phone = vendor_data['PrimaryPhone']
        contact['phone'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'Mobile' in vendor_data:
        phone = vendor_data['Mobile']
        contact['mobile'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'Fax' in vendor_data:
        phone = vendor_data['Fax']
        contact['fax'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'WebAddr' in vendor_data:
        web = vendor_data['WebAddr']
        contact['website'] = web.get('URI') if isinstance(web, dict) else web
    if contact:
        result['contact'] = contact

    # Address
    if 'BillAddr' in vendor_data and isinstance(vendor_data['BillAddr'], dict):
        addr = vendor_data['BillAddr']
        address = {}
        if 'Line1' in addr:
            address['street'] = addr['Line1']
        if 'Line2' in addr:
            address['street2'] = addr['Line2']
        if 'City' in addr:
            address['city'] = addr['City']
        if 'CountrySubDivisionCode' in addr:
            address['state'] = addr['CountrySubDivisionCode']
        if 'PostalCode' in addr:
            address['postal_code'] = addr['PostalCode']
        if 'Country' in addr:
            address['country'] = addr['Country']
        if address:
            result['address'] = address

    # Financial info
    if 'Balance' in vendor_data:
        result['balance'] = vendor_data['Balance']
    if 'CostRate' in vendor_data:
        result['cost_rate'] = vendor_data['CostRate']
    if 'BillRate' in vendor_data:
        result['bill_rate'] = vendor_data['BillRate']

    # Status
    if 'Active' in vendor_data:
        result['is_active'] = vendor_data['Active']
    if 'Vendor1099' in vendor_data:
        result['is_1099_vendor'] = vendor_data['Vendor1099']

    # Tax info
    if 'TaxIdentifier' in vendor_data:
        result['tax_id'] = vendor_data['TaxIdentifier']
    if 'BusinessNumber' in vendor_data:
        result['business_number'] = vendor_data['BusinessNumber']
    if 'AcctNum' in vendor_data:
        result['account_number'] = vendor_data['AcctNum']

    # Currency
    if 'CurrencyRef' in vendor_data and isinstance(vendor_data['CurrencyRef'], dict):
        result['currency'] = vendor_data['CurrencyRef'].get('value')

    # Terms
    if 'TermRef' in vendor_data and isinstance(vendor_data['TermRef'], dict):
        result['payment_terms'] = vendor_data['TermRef'].get('name') or vendor_data['TermRef'].get('value')

    # Bank details (simplified)
    if 'VendorPaymentBankDetail' in vendor_data and isinstance(vendor_data['VendorPaymentBankDetail'], dict):
        bank = vendor_data['VendorPaymentBankDetail']
        bank_info = {}
        if 'BankAccountName' in bank:
            bank_info['account_name'] = bank['BankAccountName']
        if 'BankBranchIdentifier' in bank:
            bank_info['branch_id'] = bank['BankBranchIdentifier']
        if 'BankAccountNumber' in bank:
            bank_info['account_number'] = bank['BankAccountNumber']
        if bank_info:
            result['bank_details'] = bank_info

    # Timestamps
    if 'MetaData' in vendor_data and isinstance(vendor_data['MetaData'], dict):
        metadata = vendor_data['MetaData']
        if 'CreateTime' in metadata:
            result['created_at'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            result['updated_at'] = metadata['LastUpdatedTime']

    return result


class VendorManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_vendor(self, **kwargs) -> Dict[str, Any]:
        """Create a new vendor."""
        vendor_data = mcp_object_to_vendor_data(**kwargs)
        response = await self.client._post('vendor', vendor_data)
        return vendor_data_to_mcp_object(response['Vendor'])

    async def get_vendor(self, id: str) -> Dict[str, Any]:
        """Get a vendor by ID."""
        response = await self.client._get(f"vendor/{id}")
        return vendor_data_to_mcp_object(response['Vendor'])

    async def list_vendors(self, active_only: bool = True, max_results: int = 100) -> List[Dict[str, Any]]:
        """List all vendors."""
        query = "select * from Vendor"

        if active_only:
            query += " WHERE Active = true"

        query += f" MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        if 'Vendor' not in response['QueryResponse']:
            return []

        vendors = response['QueryResponse']['Vendor']
        return [vendor_data_to_mcp_object(vendor) for vendor in vendors]

    async def search_vendors(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search vendors with filters.

        Args:
            name: Search by name (partial match)
            display_name: Search by display name
            company: Search by company name
            first_name: Search by first name
            last_name: Search by last name
            email: Search by email
            phone: Search by phone
            is_active: Filter by active status
            is_1099_vendor: Filter by 1099 status
            account_number: Search by account number
            max_results/start_position: Pagination
        """
        conditions = []

        # Name-based filters (partial match)
        name_filters = {
            'name': 'Name',
            'display_name': 'DisplayName',
            'company': 'CompanyName',
            'first_name': 'GivenName',
            'last_name': 'FamilyName'
        }

        for simple_name, qb_field in name_filters.items():
            if kwargs.get(simple_name):
                value = kwargs[simple_name].replace("'", "''")
                conditions.append(f"{qb_field} LIKE '%{value}%'")

        # Boolean filters
        if kwargs.get('is_active') is not None:
            conditions.append(f"Active = {str(kwargs['is_active']).lower()}")

        if kwargs.get('is_1099_vendor') is not None:
            conditions.append(f"Vendor1099 = {str(kwargs['is_1099_vendor']).lower()}")

        # Exact match filters
        if kwargs.get('account_number'):
            conditions.append(f"AcctNum = '{kwargs['account_number']}'")

        # Contact filters (partial match)
        if kwargs.get('email'):
            email = kwargs['email'].replace("'", "''")
            conditions.append(f"PrimaryEmailAddr LIKE '%{email}%'")

        if kwargs.get('phone'):
            phone = kwargs['phone'].replace("'", "''")
            conditions.append(f"PrimaryPhone LIKE '%{phone}%'")

        base_query = "SELECT * FROM Vendor"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        start_position = kwargs.get('start_position', 1)
        max_results = kwargs.get('max_results', 100)
        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        if 'Vendor' not in response['QueryResponse']:
            return []

        vendors = response['QueryResponse']['Vendor']
        return [vendor_data_to_mcp_object(vendor) for vendor in vendors]

    async def update_vendor(self, **kwargs) -> Dict[str, Any]:
        """Update a vendor."""
        vendor_id = kwargs.get('id')
        if not vendor_id:
            raise ValueError("id is required for updating a vendor")

        current_vendor_response = await self.client._get(f"vendor/{vendor_id}")
        sync_token = current_vendor_response.get('Vendor', {}).get('SyncToken', '0')

        vendor_data = mcp_object_to_vendor_data(**kwargs)
        vendor_data.update({
            "Id": vendor_id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('vendor', vendor_data)
        return vendor_data_to_mcp_object(response['Vendor'])

    async def activate_vendor(self, id: str) -> Dict[str, Any]:
        """Activate a vendor."""
        return await self.update_vendor(id=id, is_active=True)

    async def deactivate_vendor(self, id: str) -> Dict[str, Any]:
        """Deactivate a vendor."""
        return await self.update_vendor(id=id, is_active=False)


# Export tools
tools = [create_vendor_tool, get_vendor_tool, list_vendors_tool, search_vendors_tool,
         update_vendor_tool, activate_vendor_tool, deactivate_vendor_tool]
