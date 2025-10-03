from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Minimal properties for vendor creation (required by QuickBooks)
# Either DisplayName or at least one of GivenName, MiddleName, FamilyName is required
vendor_properties_minimal = {
    "DisplayName": {
        "type": "string",
        "description": "The name of the vendor as displayed. Must be unique across all Vendor, Customer, and Employee objects. Cannot be removed with sparse update. If not supplied, the system generates DisplayName by concatenating vendor name components supplied in the request from the following list: GivenName, MiddleName, FamilyName."
    },
    "GivenName": {
        "type": "string",
        "description": "Given name or first name of a person. The DisplayName attribute or at least one of GivenName, MiddleName, FamilyName attributes is required for object create."
    },
    "MiddleName": {
        "type": "string",
        "description": "Middle name of the person. The person can have zero or more middle names. The DisplayName attribute or at least one of GivenName, MiddleName, FamilyName attributes is required for object create."
    },
    "FamilyName": {
        "type": "string",
        "description": "Family name or the last name of the person. The DisplayName attribute or at least one of GivenName, MiddleName, FamilyName attributes is required for object create."
    }
}

# Vendor properties mapping (based on QuickBooks API documentation)
vendor_properties_user_define = {
    **vendor_properties_minimal,
    "PrimaryEmailAddr": {
        "type": "string",
        "description": "Primary email address."
    },
    "CompanyName": {
        "type": "string",
        "description": "The name of the company associated with the person or organization."
    },
    "PrintOnCheckName": {
        "type": "string",
        "description": "Name of the person or organization as printed on a check. If not provided, this is populated from DisplayName. Cannot be removed with sparse update."
    },
    "PrimaryPhone": {
        "type": "string",
        "description": "Primary phone number."
    },
    "WebAddr": {
        "type": "string",
        "description": "Website address."
    },
    "BusinessNumber": {
        "type": "string",
        "description": "Also called, PAN (in India) is a code that acts as an identification for individuals, families and corporates, especially for those who pay taxes on their income."
    },
    "CurrencyRefValue": {
        "type": "string",
        "description": "A three letter string representing the ISO 4217 code for the currency. For example, USD, AUD, EUR, and so on."
    },
    "CurrencyRefName": {
        "type": "string",
        "description": "The full name of the currency."
    },
    "Vendor1099": {
        "type": "boolean",
        "description": "This vendor is an independent contractor; someone who is given a 1099-MISC form at the end of the year. A 1099 vendor is paid with regular checks, and taxes are not withheld on their behalf."
    },
    "CostRate": {
        "type": "number",
        "description": "Pay rate of the vendor"
    },
    "BillRate": {
        "type": "number",
        "description": "BillRate can be set to specify this vendor's hourly billing rate."
    },
    "TaxIdentifier": {
        "type": "string",
        "description": "The tax ID of the Person or Organization. The value is masked in responses, exposing only last four characters. For example, the ID of 123-45-6789 is returned as XXXXXXX6789."
    },
    "AcctNum": {
        "type": "string",
        "description": "Name or number of the account associated with this vendor."
    },
    "GSTRegistrationType": {
        "type": "string",
        "description": "For the filing of GSTR, transactions need to be classified depending on the type of vendor from whom the purchase is made. Possible values are: GST_REG_REG, GST_REG_COMP, GST_UNREG, CONSUMER, OVERSEAS, SEZ, DEEMED."
    },
    # Billing Address fields
    "BillAddrLine1": {
        "type": "string",
        "description": "First line of the billing address."
    },
    "BillAddrLine2": {
        "type": "string",
        "description": "Second line of the billing address."
    },
    "BillAddrCity": {
        "type": "string",
        "description": "City name for the billing address."
    },
    "BillAddrCountry": {
        "type": "string",
        "description": "Country name for the billing address. For international addresses - countries should be passed as 3 ISO alpha-3 characters or the full name of the country."
    },
    "BillAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the billing address. For example, state name for USA, province name for Canada."
    },
    "BillAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the billing address."
    },
    # Vendor Payment Bank Detail fields
    "VendorPaymentBankDetailBankAccountName": {
        "type": "string",
        "description": "Name on the Bank Account"
    },
    "VendorPaymentBankDetailBankBranchIdentifier": {
        "type": "string",
        "description": "Bank identification number used to identify the Bank Branch. 6 digit value in format xxx-xxx."
    },
    "VendorPaymentBankDetailBankAccountNumber": {
        "type": "string",
        "description": "Vendor's Bank Account number. In response the value is masked and last four digit is only returned"
    },
    "VendorPaymentBankDetailStatementText": {
        "type": "string",
        "description": "Text/note/comment for Remittance"
    }
}

vendor_properties = {
    **vendor_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique QuickBooks vendor ID"
    }
}

# MCP Tool definitions
create_vendor_tool = Tool(
    name="quickbooks_create_vendor",
    title="Create Vendor",
    description="Create a new vendor in QuickBooks. Either DisplayName or at least one of GivenName, MiddleName, FamilyName is required.",
    inputSchema={
        "type": "object",
        "properties": vendor_properties_minimal,
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

get_vendor_tool = Tool(
    name="quickbooks_get_vendor",
    title="Get Vendor",
    description="Get a specific vendor by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks vendor ID"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

list_vendors_tool = Tool(
    name="quickbooks_list_vendors",
    title="List Vendors",
    description="List all vendors from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "ActiveOnly": {"type": "boolean", "description": "Return only active vendors", "default": True},
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
        },
        "required": [],
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

search_vendors_tool = Tool(
    name="quickbooks_search_vendors",
    title="Search Vendors",
    description="Search vendors with various filters including name, company, contact info, and status",
    inputSchema={
        "type": "object",
        "properties": {
            "Name": {"type": "string", "description": "Search by vendor name (partial match)"},
            "DisplayName": {"type": "string", "description": "Search by vendor display name (partial match)"},
            "CompanyName": {"type": "string", "description": "Search by company name (partial match)"},
            "GivenName": {"type": "string", "description": "Search by given/first name (partial match)"},
            "FamilyName": {"type": "string", "description": "Search by family/last name (partial match)"},
            "PrimaryEmailAddr": {"type": "string", "description": "Search by email address (partial match)"},
            "PrimaryPhone": {"type": "string", "description": "Search by phone number (partial match)"},
            "Active": {"type": "boolean", "description": "Filter by active status"},
            "Vendor1099": {"type": "boolean", "description": "Filter by 1099 vendor status"},
            "GSTIN": {"type": "string", "description": "Search by GSTIN"},
            "BusinessNumber": {"type": "string", "description": "Search by business number"},
            "AcctNum": {"type": "string", "description": "Search by account number"},
            "GSTRegistrationType": {"type": "string", "description": "Filter by GST registration type"},
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": [],
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR", "readOnlyHint": True})
)

update_vendor_tool = Tool(
    name="quickbooks_update_vendor",
    title="Update Vendor",
    description="Update an existing vendor in QuickBooks. Use activate_vendor/deactivate_vendor for status changes.",
    inputSchema={
        "type": "object",
        "properties": {
            key: value for key, value in vendor_properties.items() 
            if key != "Active"  # Remove Active from update inputs
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

activate_vendor_tool = Tool(
    name="quickbooks_activate_vendor",
    title="Activate Vendor",
    description="Activate a vendor in QuickBooks (set Active to true)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks vendor ID to activate"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)

deactivate_vendor_tool = Tool(
    name="quickbooks_deactivate_vendor",
    title="Deactivate Vendor",
    description="Deactivate a vendor from QuickBooks (set Active to false)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks vendor ID to deactivate"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_VENDOR"})
)


def mcp_object_to_vendor_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks vendor data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    vendor_data = {}

    # Basic vendor information - direct copy
    for field in ['DisplayName', 'GivenName', 'MiddleName', 'FamilyName',
                  'CompanyName', 'PrintOnCheckName', 'BusinessNumber', 'Vendor1099', 'CostRate',
                  'BillRate', 'TaxIdentifier', 'AcctNum', 'GSTRegistrationType']:
        if field in kwargs:
            vendor_data[field] = kwargs[field]

    # Handle Active field only for create operation (not for update)
    if 'Active' in kwargs:
        vendor_data['Active'] = kwargs['Active']

    # Email address
    if 'PrimaryEmailAddr' in kwargs:
        vendor_data['PrimaryEmailAddr'] = {
            'Address': kwargs['PrimaryEmailAddr']}

    # Phone numbers
    phone_fields = ['PrimaryPhone']
    for field in phone_fields:
        if field in kwargs:
            vendor_data[field] = {'FreeFormNumber': kwargs[field]}

    # Website address
    if 'WebAddr' in kwargs:
        vendor_data['WebAddr'] = {'URI': kwargs['WebAddr']}

    # Reference objects - convert separate value/name fields to structured objects
    ref_mappings = [
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName')
        # Removed APAccountRef, TermRef from input
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if value_field in kwargs:
            ref_obj = {'value': kwargs[value_field]}
            if name_field in kwargs:
                ref_obj['name'] = kwargs[name_field]
            vendor_data[ref_name] = ref_obj

    # Billing Address
    bill_addr_fields = ['BillAddrLine1', 'BillAddrLine2', 'BillAddrCity', 'BillAddrCountry', 'BillAddrCountrySubDivisionCode', 'BillAddrPostalCode']

    bill_addr = {}
    for field in bill_addr_fields:
        if field in kwargs:
            # Remove the BillAddr prefix
            addr_field = field.replace('BillAddr', '')
            bill_addr[addr_field] = kwargs[field]

    if bill_addr:
        vendor_data['BillAddr'] = bill_addr

    # Vendor Payment Bank Detail
    bank_detail_fields = {
        'VendorPaymentBankDetailBankAccountName': 'BankAccountName',
        'VendorPaymentBankDetailBankBranchIdentifier': 'BankBranchIdentifier',
        'VendorPaymentBankDetailBankAccountNumber': 'BankAccountNumber',
        'VendorPaymentBankDetailStatementText': 'StatementText'
    }

    bank_detail = {}
    for mcp_field, qb_field in bank_detail_fields.items():
        if mcp_field in kwargs:
            bank_detail[qb_field] = kwargs[mcp_field]

    if bank_detail:
        vendor_data['VendorPaymentBankDetail'] = bank_detail

    return vendor_data


def vendor_data_to_mcp_object(vendor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks vendor data format to MCP object format.
    This function flattens the nested QuickBooks structure to the flat format expected by MCP tools.
    """
    mcp_object = {}

    # Copy basic fields if present
    for field in [
        'Id', 'DisplayName', 'GivenName', 'MiddleName', 'FamilyName',
        'CompanyName', 'PrintOnCheckName', 'Active', 'BusinessNumber', 'Vendor1099', 'CostRate',
        'BillRate', 'TaxIdentifier', 'AcctNum', 'GSTRegistrationType',
        'Balance'
    ]:
        if field in vendor_data:
            mcp_object[field] = vendor_data[field]

    # Handle fields that are output-only (not in input schema but preserved in output)
    for field in ['Title', 'Suffix', 'AlternatePhone', 'Mobile', 'Fax', 'Source', 'GSTIN', 'T4AEligible', 'HasTPAR', 'TaxReportingBasis', 'T5018Eligible']:
        if field in vendor_data:
            mcp_object[field] = vendor_data[field]

    # Email address
    if 'PrimaryEmailAddr' in vendor_data and isinstance(vendor_data['PrimaryEmailAddr'], dict):
        if 'Address' in vendor_data['PrimaryEmailAddr']:
            mcp_object['PrimaryEmailAddr'] = vendor_data['PrimaryEmailAddr']['Address']

    # Phone numbers - handle primary phone as input, others as output-only
    if 'PrimaryPhone' in vendor_data and isinstance(vendor_data['PrimaryPhone'], dict):
        if 'FreeFormNumber' in vendor_data['PrimaryPhone']:
            mcp_object['PrimaryPhone'] = vendor_data['PrimaryPhone']['FreeFormNumber']
    
    # Handle other phone fields as output-only
    phone_mappings = ['AlternatePhone', 'Mobile', 'Fax']
    for field in phone_mappings:
        if field in vendor_data and isinstance(vendor_data[field], dict):
            if 'FreeFormNumber' in vendor_data[field]:
                mcp_object[field] = vendor_data[field]['FreeFormNumber']

    # Website address
    if 'WebAddr' in vendor_data and isinstance(vendor_data['WebAddr'], dict):
        if 'URI' in vendor_data['WebAddr']:
            mcp_object['WebAddr'] = vendor_data['WebAddr']['URI']

    # Reference objects - flatten to separate value and name fields
    ref_mappings = [
        ('APAccountRef', 'APAccountRefValue', 'APAccountRefName'),
        ('TermRef', 'TermRefValue', 'TermRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('SyncToken', 'SyncToken', None)
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if ref_name in vendor_data:
            ref = vendor_data[ref_name]
            if isinstance(ref, dict):
                if 'value' in ref:
                    mcp_object[value_field] = ref['value']
                if name_field and 'name' in ref:
                    mcp_object[name_field] = ref['name']
            else:
                # Handle cases where SyncToken might be directly in vendor_data
                mcp_object[value_field] = ref

    # Billing Address
    if 'BillAddr' in vendor_data and isinstance(vendor_data['BillAddr'], dict):
        bill_addr = vendor_data['BillAddr']
        addr_mappings = {
            'Line1': 'BillAddrLine1',
            'Line2': 'BillAddrLine2',
            'City': 'BillAddrCity',
            'Country': 'BillAddrCountry',
            'CountrySubDivisionCode': 'BillAddrCountrySubDivisionCode',
            'PostalCode': 'BillAddrPostalCode'
        }

        for qb_field, mcp_field in addr_mappings.items():
            if qb_field in bill_addr:
                mcp_object[mcp_field] = bill_addr[qb_field]

    # Vendor Payment Bank Detail
    if 'VendorPaymentBankDetail' in vendor_data and isinstance(vendor_data['VendorPaymentBankDetail'], dict):
        bank_detail = vendor_data['VendorPaymentBankDetail']
        bank_mappings = {
            'BankAccountName': 'VendorPaymentBankDetailBankAccountName',
            'BankBranchIdentifier': 'VendorPaymentBankDetailBankBranchIdentifier',
            'BankAccountNumber': 'VendorPaymentBankDetailBankAccountNumber',
            'StatementText': 'VendorPaymentBankDetailStatementText'
        }

        for qb_field, mcp_field in bank_mappings.items():
            if qb_field in bank_detail:
                mcp_object[mcp_field] = bank_detail[qb_field]

    # MetaData fields
    if 'MetaData' in vendor_data and isinstance(vendor_data['MetaData'], dict):
        metadata = vendor_data['MetaData']
        if 'CreateTime' in metadata:
            mcp_object['MetaDataCreateTime'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            mcp_object['MetaDataLastUpdatedTime'] = metadata['LastUpdatedTime']

    return mcp_object


class VendorManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_vendor(self, **kwargs) -> Dict[str, Any]:
        """Create a new vendor with comprehensive property support."""
        vendor_data = mcp_object_to_vendor_data(**kwargs)

        response = await self.client._post('vendor', vendor_data)
        return vendor_data_to_mcp_object(response['Vendor'])

    async def get_vendor(self, Id: str) -> Dict[str, Any]:
        """Get a specific vendor by ID."""
        response = await self.client._get(f"vendor/{Id}")
        return vendor_data_to_mcp_object(response['Vendor'])

    async def list_vendors(self, ActiveOnly: bool = True, MaxResults: int = 100) -> List[Dict[str, Any]]:
        """List all vendors with comprehensive properties and pagination support."""
        query = f"select * from Vendor"

        if ActiveOnly:
            query += " WHERE Active = true"

        query += f" MAXRESULTS {MaxResults}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no vendors are returned
        if 'Vendor' not in response['QueryResponse']:
            return []

        vendors = response['QueryResponse']['Vendor']
        return [vendor_data_to_mcp_object(vendor) for vendor in vendors]

    async def search_vendors(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search vendors with various filters and pagination support.

        Args:
            Name: Search by vendor name (partial match)
            DisplayName: Search by vendor display name (partial match)
            CompanyName: Search by company name (partial match)
            GivenName: Search by given/first name (partial match)
            FamilyName: Search by family/last name (partial match)
            PrimaryEmailAddr: Search by email address (partial match)
            PrimaryPhone: Search by phone number (partial match)
            Active: Filter by active status
            Vendor1099: Filter by 1099 vendor status
            GSTIN: Search by GSTIN
            BusinessNumber: Search by business number
            AcctNum: Search by account number
            GSTRegistrationType: Filter by GST registration type
            MaxResults: Maximum number of results to return (default: 100)
            StartPosition: Starting position for pagination (default: 1)

        Returns:
            List of vendors matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Name-based filters (partial match)
        name_filters = {
            'Name': 'Name',
            'DisplayName': 'DisplayName',
            'CompanyName': 'CompanyName',
            'GivenName': 'GivenName',
            'FamilyName': 'FamilyName'
        }

        for param, field in name_filters.items():
            if kwargs.get(param):
                value = kwargs[param].replace(
                    "'", "''")  # Escape single quotes
                conditions.append(f"{field} LIKE '%{value}%'")

        # Exact match filters
        exact_filters = {
            'Active': 'Active',
            'Vendor1099': 'Vendor1099',
            'GSTIN': 'GSTIN',
            'BusinessNumber': 'BusinessNumber',
            'AcctNum': 'AcctNum',
            'GSTRegistrationType': 'GSTRegistrationType'
        }

        for param, field in exact_filters.items():
            if kwargs.get(param) is not None:
                value = kwargs[param]
                if isinstance(value, bool):
                    conditions.append(f"{field} = {str(value).lower()}")
                else:
                    conditions.append(f"{field} = '{value}'")

        # Contact info filters (partial match)
        if kwargs.get('PrimaryEmailAddr'):
            email = kwargs['PrimaryEmailAddr'].replace("'", "''")
            conditions.append(f"PrimaryEmailAddr LIKE '%{email}%'")

        if kwargs.get('PrimaryPhone'):
            phone = kwargs['PrimaryPhone'].replace("'", "''")
            conditions.append(f"PrimaryPhone LIKE '%{phone}%'")

        # Build the complete query
        base_query = "SELECT * FROM Vendor"

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            base_query += where_clause

        # Add pagination
        start_position = kwargs.get('StartPosition', 1)
        max_results = kwargs.get('MaxResults', 100)

        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no vendors are returned
        if 'Vendor' not in response['QueryResponse']:
            return []

        vendors = response['QueryResponse']['Vendor']
        results = [vendor_data_to_mcp_object(vendor) for vendor in vendors]

        return results

    async def update_vendor(self, **kwargs) -> Dict[str, Any]:
        """Update an existing vendor with comprehensive property support."""
        Id = kwargs.get('Id')
        if not Id:
            raise ValueError("Id is required for updating a vendor")

        # Auto-fetch current sync token
        current_vendor_response = await self.client._get(f"vendor/{Id}")
        sync_token = current_vendor_response.get(
            'Vendor', {}).get('SyncToken', '0')

        vendor_data = mcp_object_to_vendor_data(**kwargs)
        vendor_data.update({
            "Id": Id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('vendor', vendor_data)
        return vendor_data_to_mcp_object(response['Vendor'])

    async def activate_vendor(self, Id: str) -> Dict[str, Any]:
        """Activate a vendor (set Active to true)."""
        return await self.update_vendor(Id=Id, Active=True)

    async def deactivate_vendor(self, Id: str) -> Dict[str, Any]:
        """Deactivate a vendor (set Active to false)."""
        return await self.update_vendor(Id=Id, Active=False)


# Export tools
tools = [create_vendor_tool, get_vendor_tool, list_vendors_tool, search_vendors_tool,
         update_vendor_tool, activate_vendor_tool, deactivate_vendor_tool]
