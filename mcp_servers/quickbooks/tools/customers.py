from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

customer_properties_user_define = {
    "DisplayName": {
        "type": "string",
        "description": "The name of the person or organization as displayed. Must be unique across all Customer, Vendor, and Employee objects. Cannot be removed with sparse update."
    },
    "GivenName": {
        "type": "string",
        "description": "Given name or first name of a person."
    },
    "MiddleName": {
        "type": "string",
        "description": "Middle name of the person. The person can have zero or more middle names."
    },
    "FamilyName": {
        "type": "string",
        "description": "Family name or the last name of the person."
    },
    "PrimaryEmailAddr": {
        "type": "string",
        "description": "Primary email address."
    },
    "DefaultTaxCodeRefValue": {
        "type": "string",
        "description": "The ID for the default tax code associated with this Customer object. Valid if Customer.Taxable is set to true; otherwise, it is ignored. If automated sales tax is enabled, the default tax code is set by the system and cannot be overridden."
    },
    "DefaultTaxCodeRefName": {
        "type": "string",
        "description": "The name of the default tax code associated with this Customer object."
    },
    "BillWithParent": {
        "type": "boolean",
        "description": "If true, this Customer object is billed with its parent. If false, or null the customer is not to be billed with its parent. This attribute is valid only if this entity is a Job or sub Customer."
    },
    "CurrencyRefValue": {
        "type": "string",
        "description": "The ID for the currency in which all amounts associated with this customer are expressed. Once set, it cannot be changed."
    },
    "CurrencyRefName": {
        "type": "string",
        "description": "The name of the currency in which all amounts associated with this customer are expressed."
    },
    "PrimaryPhone": {
        "type": "string",
        "description": "Primary phone number."
    },
    "Taxable": {
        "type": "boolean",
        "description": "If true, transactions for this customer are taxable."
    },
    "Notes": {
        "type": "string",
        "description": "Free form text describing the Customer."
    },
    "WebAddr": {
        "type": "string",
        "description": "Website address of the Customer."
    },
    "CompanyName": {
        "type": "string",
        "description": "The name of the company associated with the person or organization."
    },
    "Balance": {
        "type": "number",
        "description": "Specifies the open balance amount or the amount unpaid by the customer. For the create operation, this represents the opening balance for the customer. When returned in response to the query request it represents the current open balance (unpaid amount) for that customer. Write-on-create."
    },
    "OpenBalanceDate": {
        "type": "string",
        "description": "Date of the Open Balance for the create operation. Write-on-create."
    },
    "ShipAddrLine1": {
        "type": "string",
        "description": "First line of the shipping address."
    },
    "ShipAddrLine2": {
        "type": "string",
        "description": "Second line of the shipping address."
    },
    "ShipAddrCity": {
        "type": "string",
        "description": "City name for the shipping address."
    },
    "ShipAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the shipping address. For example, state name for USA, province name for Canada."
    },
    "ShipAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the shipping address."
    },
    "ShipAddrCountry": {
        "type": "string",
        "description": "Country name for the shipping address. For international addresses - countries should be passed as 3 ISO alpha-3 characters or the full name of the country."
    },
    "PaymentMethodRefValue": {
        "type": "string",
        "description": "The ID for the payment method associated with this Customer object."
    },
    "PaymentMethodRefName": {
        "type": "string",
        "description": "The name of the payment method associated with this Customer object."
    },
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
    "BillAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the billing address. For example, state name for USA, province name for Canada."
    },
    "BillAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the billing address."
    },
    "BillAddrCountry": {
        "type": "string",
        "description": "Country name for the billing address. For international addresses - countries should be passed as 3 ISO alpha-3 characters or the full name of the country."
    }
}

customer_properties = {
    **customer_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique identifier for the customer in QuickBooks. Sort order is ASC by default. System generated"
    },
}

# MCP Tool definitions
create_customer_tool = Tool(
    name="quickbooks_create_customer",
    description="Create a new customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": customer_properties_user_define,
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

get_customer_tool = Tool(
    name="quickbooks_get_customer",
    description="Get a specific customer by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER", "readOnlyHint": True}),
)

list_customers_tool = Tool(
    name="quickbooks_list_customers",
    description="List all customers from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "ActiveOnly": {"type": "boolean", "description": "Return only active customers", "default": True}
        }
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER", "readOnlyHint": True}),
)

update_customer_tool = Tool(
    name="quickbooks_update_customer",
    description="Update an existing customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": customer_properties,
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

deactivate_customer_tool = Tool(
    name="quickbooks_deactivate_customer",
    description="Deactivate a customer from QuickBooks (set Active to false)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID to deactivate"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

activate_customer_tool = Tool(
    name="quickbooks_activate_customer",
    description="Activate a customer in QuickBooks (set Active to true)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID to activate"}
        },
        "required": ["Id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

search_customers_tool = Tool(
    name="quickbooks_search_customers",
    title="Search Customers",
    description="Advanced Customer Search - Search customers with powerful filters including name, contact info, address, balance, status, and other criteria. Perfect for finding specific customers based on various parameters",
    inputSchema={
        "type": "object",
        "properties": {
            "DisplayName": {"type": "string", "description": "Search by customer display name (partial match)"},
            "GivenName": {"type": "string", "description": "Search by given/first name (partial match)"},
            "FamilyName": {"type": "string", "description": "Search by family/last name (partial match)"},
            "MiddleName": {"type": "string", "description": "Search by middle name (partial match)"},
            "CompanyName": {"type": "string", "description": "Search by company name (partial match)"},
            "PrimaryEmailAddr": {"type": "string", "description": "Search by email address (partial match)"},
            "PrimaryPhone": {"type": "string", "description": "Search by phone number (partial match)"},

            # Status filters
            "Active": {"type": "boolean", "description": "Filter by active status"},
            "Taxable": {"type": "boolean", "description": "Filter by taxable status"},

            # Address filters - Billing Address
            "BillAddrCity": {"type": "string", "description": "Search by billing address city"},
            "BillAddrCountrySubDivisionCode": {"type": "string", "description": "Search by billing address state/province"},
            "BillAddrPostalCode": {"type": "string", "description": "Search by billing address postal code"},
            "BillAddrCountry": {"type": "string", "description": "Search by billing address country"},
            "BillAddrLine1": {"type": "string", "description": "Search by billing address line 1 (partial match)"},

            # Address filters - Shipping Address
            "ShipAddrCity": {"type": "string", "description": "Search by shipping address city"},
            "ShipAddrCountrySubDivisionCode": {"type": "string", "description": "Search by shipping address state/province"},
            "ShipAddrPostalCode": {"type": "string", "description": "Search by shipping address postal code"},
            "ShipAddrCountry": {"type": "string", "description": "Search by shipping address country"},
            "ShipAddrLine1": {"type": "string", "description": "Search by shipping address line 1 (partial match)"},

            # Balance filters
            "MinBalance": {"type": "number", "description": "Minimum balance amount"},
            "MaxBalance": {"type": "number", "description": "Maximum balance amount"},

            # Reference filters
            "CurrencyRefValue": {"type": "string", "description": "Filter by currency code"},
            "CurrencyRefName": {"type": "string", "description": "Search by currency name (partial match)"},
            "PaymentMethodRefValue": {"type": "string", "description": "Filter by payment method ID"},
            "PaymentMethodRefName": {"type": "string", "description": "Search by payment method name (partial match)"},

            # Date filters
            "OpenBalanceDateFrom": {"type": "string", "description": "Search by opening balance date from (YYYY-MM-DD format)"},
            "OpenBalanceDateTo": {"type": "string", "description": "Search by opening balance date to (YYYY-MM-DD format)"},

            # Other filters
            "WebAddr": {"type": "string", "description": "Search by website address (partial match)"},
            "Notes": {"type": "string", "description": "Search by notes/description (partial match)"},

            # Pagination
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER", "readOnlyHint": True})
)


def mcp_object_to_customer_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks customer data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    customer_data = {}

    # Basic customer information - direct copy
    for field in ['DisplayName', 'GivenName', 'MiddleName', 'FamilyName',
                  'CompanyName']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Contact information - convert to structured objects
    if 'PrimaryEmailAddr' in kwargs:
        customer_data['PrimaryEmailAddr'] = {
            'Address': kwargs['PrimaryEmailAddr']}

    # Handle phone fields - use PrimaryPhone as the standard input field
    if 'PrimaryPhone' in kwargs:
        customer_data['PrimaryPhone'] = {
            'FreeFormNumber': kwargs['PrimaryPhone']}

    # Handle Mobile input (for backward compatibility with existing code)
    if 'Mobile' in kwargs:
        customer_data['Mobile'] = {
            'FreeFormNumber': kwargs['Mobile']}

    if 'WebAddr' in kwargs:
        customer_data['WebAddr'] = {'URI': kwargs['WebAddr']}

    # Reference objects - convert separate value/name fields to structured objects
    ref_mappings = [
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('PaymentMethodRef', 'PaymentMethodRefValue', 'PaymentMethodRefName')
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if value_field in kwargs:
            ref_obj = {'value': kwargs[value_field]}
            if name_field in kwargs:
                ref_obj['name'] = kwargs[name_field]
            customer_data[ref_name] = ref_obj

    # Address fields - convert flattened fields to structured objects
    for addr_type in ['BillAddr', 'ShipAddr']:
        address_fields = ['Line1', 'Line2', 'City',
                          'CountrySubDivisionCode', 'PostalCode', 'Country']
        has_address = any(kwargs.get(f'{addr_type}{field}')
                          for field in address_fields)
        if has_address:
            addr_obj = {}
            for field in address_fields:
                if kwargs.get(f'{addr_type}{field}'):
                    addr_obj[field] = kwargs[f'{addr_type}{field}']
            customer_data[addr_type] = addr_obj

    # Boolean fields
    for field in ['BillWithParent', 'Taxable', 'Active']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Numeric fields
    for field in ['Balance']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Date fields
    for field in ['OpenBalanceDate']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Metadata fields - removed for input

    return customer_data


def customer_data_to_mcp_object(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks customer data format to MCP object format.
    This function flattens the nested QuickBooks structure to the flat format expected by MCP tools.
    All fields from customer_properties_full are included with default values if not present.
    """
    mcp_object = {}
    # Only set fields that exist in customer_data
    for field in [
        'Id', 'DisplayName', 'Title', 'GivenName', 'MiddleName', 'FamilyName',
        'Suffix', 'CompanyName', 'FullyQualifiedName', 'ResaleNum', 'SecondaryTaxIdentifier',
        'BusinessNumber', 'GSTIN', 'GSTRegistrationType', 'PrimaryTaxIdentifier',
        'PreferredDeliveryMethod', 'Notes', 'PrintOnCheckName',
        'ARAccountRefValue', 'ARAccountRefName', 'DefaultTaxCodeRefValue', 'DefaultTaxCodeRefName',
        'SalesTermRefValue', 'SalesTermRefName', 'CurrencyRefValue', 'CurrencyRefName',
        'CustomerTypeRef', 'ParentRefValue', 'ParentRefName', 'PaymentMethodRefValue', 'PaymentMethodRefName',
        'BillAddrLine1', 'BillAddrLine2',
        'BillAddrCity', 'BillAddrCountrySubDivisionCode', 'BillAddrPostalCode', 'BillAddrCountry',
        'ShipAddrLine1', 'ShipAddrLine2',
        'ShipAddrCity', 'ShipAddrCountrySubDivisionCode', 'ShipAddrPostalCode', 'ShipAddrCountry',
        'OpenBalanceDate', 'MetaDataCreateTime', 'MetaDataLastUpdatedTime',
        'PrimaryEmailAddr', 'PrimaryPhone', 'Mobile', 'AlternatePhone', 'Fax', 'WebAddr',
        'Balance', 'BalanceWithJobs', 'TaxExemptionReasonId',
            'BillWithParent', 'Job', 'Taxable', 'Active', 'IsProject']:
        if field in customer_data:
            mcp_object[field] = customer_data[field]

    # Contact information - flatten structured objects
    if 'PrimaryEmailAddr' in customer_data:
        addr = customer_data['PrimaryEmailAddr']
        if isinstance(addr, dict) and 'Address' in addr:
            mcp_object['PrimaryEmailAddr'] = addr['Address']
    for phone_field in ['PrimaryPhone', 'Mobile', 'AlternatePhone', 'Fax']:
        if phone_field in customer_data:
            phone = customer_data[phone_field]
            if isinstance(phone, dict) and 'FreeFormNumber' in phone:
                mcp_object[phone_field] = phone['FreeFormNumber']
    if 'WebAddr' in customer_data:
        web = customer_data['WebAddr']
        if isinstance(web, dict) and 'URI' in web:
            mcp_object['WebAddr'] = web['URI']

    # Reference objects - flatten to separate value and name fields
    if 'ARAccountRef' in customer_data:
        ref = customer_data['ARAccountRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['ARAccountRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['ARAccountRefName'] = ref['name']
    if 'DefaultTaxCodeRef' in customer_data:
        ref = customer_data['DefaultTaxCodeRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['DefaultTaxCodeRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['DefaultTaxCodeRefName'] = ref['name']
    if 'SalesTermRef' in customer_data:
        ref = customer_data['SalesTermRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['SalesTermRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['SalesTermRefName'] = ref['name']
    if 'CurrencyRef' in customer_data:
        ref = customer_data['CurrencyRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['CurrencyRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['CurrencyRefName'] = ref['name']
    if 'CustomerTypeRef' in customer_data:
        ref = customer_data['CustomerTypeRef']
        if isinstance(ref, dict) and 'value' in ref:
            mcp_object['CustomerTypeRef'] = ref['value']
    if 'ParentRef' in customer_data:
        ref = customer_data['ParentRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['ParentRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['ParentRefName'] = ref['name']
    if 'PaymentMethodRef' in customer_data:
        ref = customer_data['PaymentMethodRef']
        if isinstance(ref, dict):
            if 'value' in ref:
                mcp_object['PaymentMethodRefValue'] = ref['value']
            if 'name' in ref:
                mcp_object['PaymentMethodRefName'] = ref['name']

    # Address fields - flatten structured objects
    if 'BillAddr' in customer_data:
        addr = customer_data['BillAddr']
        if isinstance(addr, dict):
            for field in ['Line1', 'Line2', 'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']:
                if field in addr:
                    mcp_object[f'BillAddr{field}'] = addr[field]
    if 'ShipAddr' in customer_data:
        addr = customer_data['ShipAddr']
        if isinstance(addr, dict):
            for field in ['Line1', 'Line2', 'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']:
                if field in addr:
                    mcp_object[f'ShipAddr{field}'] = addr[field]

    # Metadata fields - flatten structured object
    if 'MetaData' in customer_data:
        metadata = customer_data['MetaData']
        if isinstance(metadata, dict):
            if 'CreateTime' in metadata:
                mcp_object['MetaDataCreateTime'] = metadata['CreateTime']
            if 'LastUpdatedTime' in metadata:
                mcp_object['MetaDataLastUpdatedTime'] = metadata['LastUpdatedTime']
    return mcp_object


class CustomerManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_customer(self, **kwargs) -> Dict[str, Any]:

        # Validate we have DisplayName or at least one name component
        display_name_provided = 'DisplayName' in kwargs
        name_components_provided = any([
            'GivenName' in kwargs,
            'FamilyName' in kwargs,
            'MiddleName' in kwargs,
        ])

        if not display_name_provided and not name_components_provided:
            raise ValueError(
                "At least one of: DisplayName, GivenName, FamilyName, MiddleName must be provided.")

        customer_data = mcp_object_to_customer_data(**kwargs)
        response = await self.client._post('customer', customer_data)

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def get_customer(self, Id: str) -> Dict[str, Any]:
        response = await self.client._get(f"customer/{Id}")

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def list_customers(self, MaxResults: int = 100, ActiveOnly: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Customer"
        if ActiveOnly:
            query += " WHERE Active = true"
        query += f" STARTPOSITION 1 MAXRESULTS {MaxResults}"
        response = await self.client._get('query', params={'query': query})

        # Convert response back to MCP format
        customers = response['QueryResponse']['Customer']
        return [customer_data_to_mcp_object(customer) for customer in customers]

    async def update_customer(self, **kwargs) -> Dict[str, Any]:
        customer_id = kwargs.get('Id')
        if not customer_id:
            raise ValueError("Id is required for updating a customer")

        # Auto-fetch current sync token
        current_customer_response = await self.client._get(f"customer/{customer_id}")
        sync_token = current_customer_response.get(
            'Customer', {}).get('SyncToken', '0')

        # Use the mcp_object_to_customer_data function to convert the input
        customer_data = mcp_object_to_customer_data(**kwargs)

        # Add required fields for update
        customer_data.update({
            "Id": customer_id,
            "SyncToken": sync_token,
            "sparse": True
        })

        response = await self.client._post('customer', customer_data)

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def deactivate_customer(self, Id: str) -> Dict[str, Any]:
        # First get the current customer to obtain the SyncToken
        current_customer_response = await self.client._get(f"customer/{Id}")
        current_data = current_customer_response.get('Customer', {})

        # Set Active to false for deactivation
        customer_data = {
            "Id": str(current_data.get('Id')),
            "SyncToken": str(current_data.get('SyncToken')),
            "Active": False,
            "sparse": True
        }

        response = await self.client._post('customer', customer_data)

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def activate_customer(self, Id: str) -> Dict[str, Any]:
        # First get the current customer to obtain the SyncToken
        current_customer_response = await self.client._get(f"customer/{Id}")
        current_data = current_customer_response.get('Customer', {})

        # Set Active to true for activation
        customer_data = {
            "Id": str(current_data.get('Id')),
            "SyncToken": str(current_data.get('SyncToken')),
            "Active": True,
            "sparse": True
        }

        response = await self.client._post('customer', customer_data)

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def search_customers(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search customers with various filters and pagination support.

        Args:
            DisplayName: Search by customer display name (partial match)
            GivenName/FamilyName/MiddleName: Search by name components (partial match)
            CompanyName: Search by company name (partial match)
            PrimaryEmailAddr/PrimaryPhone: Search by contact info (partial match)

            # Status filters
            Active: Filter by active status
            Job: Filter by job status (sub-customers)
            BillWithParent: Filter by bill with parent status
            Taxable: Filter by taxable status

            # Identification filters
            ResaleNum/BusinessNumber/GSTIN: Search by identification numbers
            PrimaryTaxIdentifier/SecondaryTaxIdentifier: Search by tax identifiers

            # Address filters (billing and shipping)
            BillAddrCity/ShipAddrCity: Search by city
            BillAddrCountrySubDivisionCode/ShipAddrCountrySubDivisionCode: Search by state/province
            BillAddrPostalCode/ShipAddrPostalCode: Search by postal code
            BillAddrCountry/ShipAddrCountry: Search by country
            BillAddrLine1/ShipAddrLine1: Search by address line 1 (partial match)

            # Balance filters
            MinBalance/MaxBalance: Filter by balance range
            MinBalanceWithJobs/MaxBalanceWithJobs: Filter by balance with jobs range

            # Reference filters
            ParentRefValue: Filter by parent customer ID
            ParentRefName: Search by parent customer name (partial match)
            CurrencyRefValue: Filter by currency code
            CurrencyRefName: Search by currency name (partial match)
            SalesTermRefValue: Filter by sales term ID
            PaymentMethodRefValue: Filter by payment method ID
            DefaultTaxCodeRefValue: Filter by default tax code ID

            # Date filters
            CreateTimeFrom/CreateTimeTo: Filter by creation date range
            LastUpdatedTimeFrom/LastUpdatedTimeTo: Filter by last updated date range
            OpenBalanceDateFrom/OpenBalanceDateTo: Filter by opening balance date range

            # Other filters
            PreferredDeliveryMethod: Filter by delivery method
            GSTRegistrationType: Filter by GST registration type
            WebAddr: Search by website (partial match)
            Notes: Search by notes (partial match)

            MaxResults: Maximum number of results to return (default: 100)
            StartPosition: Starting position for pagination (default: 1)

        Returns:
            List of customers matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters with exact matches
        if kwargs.get('Active') is not None:
            conditions.append(f"Active = {str(kwargs['Active']).lower()}")

        if kwargs.get('Job') is not None:
            conditions.append(f"Job = {str(kwargs['Job']).lower()}")

        if kwargs.get('BillWithParent') is not None:
            conditions.append(
                f"BillWithParent = {str(kwargs['BillWithParent']).lower()}")

        if kwargs.get('Taxable') is not None:
            conditions.append(f"Taxable = {str(kwargs['Taxable']).lower()}")

        # Reference filters
        if kwargs.get('ParentRefValue'):
            conditions.append(
                f"ParentRef.value = '{kwargs['ParentRefValue']}'")

        if kwargs.get('CurrencyRefValue'):
            conditions.append(
                f"CurrencyRef.value = '{kwargs['CurrencyRefValue']}'")

        if kwargs.get('SalesTermRefValue'):
            conditions.append(
                f"SalesTermRef.value = '{kwargs['SalesTermRefValue']}'")

        if kwargs.get('PaymentMethodRefValue'):
            conditions.append(
                f"PaymentMethodRef.value = '{kwargs['PaymentMethodRefValue']}'")

        if kwargs.get('DefaultTaxCodeRefValue'):
            conditions.append(
                f"DefaultTaxCodeRef.value = '{kwargs['DefaultTaxCodeRefValue']}'")

        # Exact match filters for structured data
        if kwargs.get('ResaleNum'):
            conditions.append(f"ResaleNum = '{kwargs['ResaleNum']}'")

        if kwargs.get('BusinessNumber'):
            conditions.append(f"BusinessNumber = '{kwargs['BusinessNumber']}'")

        if kwargs.get('GSTIN'):
            conditions.append(f"GSTIN = '{kwargs['GSTIN']}'")

        if kwargs.get('PreferredDeliveryMethod'):
            conditions.append(
                f"PreferredDeliveryMethod = '{kwargs['PreferredDeliveryMethod']}'")

        if kwargs.get('GSTRegistrationType'):
            conditions.append(
                f"GSTRegistrationType = '{kwargs['GSTRegistrationType']}'")

        # Address filters - exact matches for structured fields
        address_exact_fields = {
            'BillAddrCity': 'BillAddr.City',
            'BillAddrCountrySubDivisionCode': 'BillAddr.CountrySubDivisionCode',
            'BillAddrPostalCode': 'BillAddr.PostalCode',
            'BillAddrCountry': 'BillAddr.Country',
            'ShipAddrCity': 'ShipAddr.City',
            'ShipAddrCountrySubDivisionCode': 'ShipAddr.CountrySubDivisionCode',
            'ShipAddrPostalCode': 'ShipAddr.PostalCode',
            'ShipAddrCountry': 'ShipAddr.Country'
        }

        for field, qb_field in address_exact_fields.items():
            if kwargs.get(field):
                conditions.append(f"{qb_field} = '{kwargs[field]}'")

        # Balance range filters
        if kwargs.get('MinBalance') is not None:
            conditions.append(f"Balance >= {kwargs['MinBalance']}")
        if kwargs.get('MaxBalance') is not None:
            conditions.append(f"Balance <= {kwargs['MaxBalance']}")

        if kwargs.get('MinBalanceWithJobs') is not None:
            conditions.append(
                f"BalanceWithJobs >= {kwargs['MinBalanceWithJobs']}")
        if kwargs.get('MaxBalanceWithJobs') is not None:
            conditions.append(
                f"BalanceWithJobs <= {kwargs['MaxBalanceWithJobs']}")

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

        if kwargs.get('OpenBalanceDateFrom'):
            conditions.append(
                f"OpenBalanceDate >= '{kwargs['OpenBalanceDateFrom']}'")
        if kwargs.get('OpenBalanceDateTo'):
            conditions.append(
                f"OpenBalanceDate <= '{kwargs['OpenBalanceDateTo']}'")

        # Partial match filters - we'll post-filter these due to QB API limitations
        partial_match_filters = {}

        partial_fields = [
            'DisplayName', 'GivenName', 'FamilyName', 'MiddleName', 'CompanyName',
            'PrimaryEmailAddr', 'PrimaryPhone', 'WebAddr', 'Notes',
            'BillAddrLine1', 'ShipAddrLine1', 'PrimaryTaxIdentifier', 'SecondaryTaxIdentifier'
        ]

        for field in partial_fields:
            if kwargs.get(field):
                partial_match_filters[field] = kwargs[field].lower()

        # Reference name searches (requires subqueries or post-filtering)
        if kwargs.get('ParentRefName'):
            parent_name = kwargs['ParentRefName'].replace(
                "'", "''")  # Escape single quotes
            conditions.append(
                f"ParentRef.value IN (SELECT Id FROM Customer WHERE DisplayName LIKE '%{parent_name}%')")

        reference_name_fields = [
            'CurrencyRefName', 'SalesTermRefName', 'PaymentMethodRefName', 'DefaultTaxCodeRefName']
        for field in reference_name_fields:
            if kwargs.get(field):
                partial_match_filters[field] = kwargs[field].lower()

        # Build the query
        query = "SELECT * FROM Customer"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add pagination
        max_results = kwargs.get('MaxResults', 100)
        start_position = kwargs.get('StartPosition', 1)

        query += f" STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no customers are returned
        if 'Customer' not in response['QueryResponse']:
            return []

        customers = response['QueryResponse']['Customer']

        # Apply post-filtering for partial matches
        if partial_match_filters:
            filtered_customers = []
            for customer in customers:
                should_include = True

                for field, search_value in partial_match_filters.items():
                    if field in ['DisplayName', 'GivenName', 'FamilyName', 'MiddleName', 'CompanyName', 'ResaleNum', 'WebAddr', 'Notes']:
                        if field in customer and search_value not in customer[field].lower():
                            should_include = False
                            break
                    elif field in ['PrimaryEmailAddr', 'PrimaryPhone']:
                        if field in customer and search_value not in customer[field].lower():
                            should_include = False
                            break
                    elif field in ['PrimaryTaxIdentifier', 'SecondaryTaxIdentifier']:
                        if field in customer and search_value not in customer[field].lower():
                            should_include = False
                            break
                    elif field == 'BillAddrLine1' and 'BillAddr' in customer and isinstance(customer['BillAddr'], dict):
                        addr_line = customer['BillAddr'].get(
                            'Line1', '').lower()
                        if search_value not in addr_line:
                            should_include = False
                            break
                    elif field == 'ShipAddrLine1' and 'ShipAddr' in customer and isinstance(customer['ShipAddr'], dict):
                        addr_line = customer['ShipAddr'].get(
                            'Line1', '').lower()
                        if search_value not in addr_line:
                            should_include = False
                            break
                    elif field == 'CurrencyRefName' and 'CurrencyRef' in customer and isinstance(customer['CurrencyRef'], dict):
                        currency_name = customer['CurrencyRef'].get(
                            'name', '').lower()
                        if search_value not in currency_name:
                            should_include = False
                            break
                    elif field == 'SalesTermRefName' and 'SalesTermRef' in customer and isinstance(customer['SalesTermRef'], dict):
                        term_name = customer['SalesTermRef'].get(
                            'name', '').lower()
                        if search_value not in term_name:
                            should_include = False
                            break
                    elif field == 'PaymentMethodRefName' and 'PaymentMethodRef' in customer and isinstance(customer['PaymentMethodRef'], dict):
                        method_name = customer['PaymentMethodRef'].get(
                            'name', '').lower()
                        if search_value not in method_name:
                            should_include = False
                            break
                    elif field == 'DefaultTaxCodeRefName' and 'DefaultTaxCodeRef' in customer and isinstance(customer['DefaultTaxCodeRef'], dict):
                        tax_name = customer['DefaultTaxCodeRef'].get(
                            'name', '').lower()
                        if search_value not in tax_name:
                            should_include = False
                            break

                if should_include:
                    filtered_customers.append(customer)

            customers = filtered_customers

        return [customer_data_to_mcp_object(customer) for customer in customers]


# Export tools
tools = [create_customer_tool, get_customer_tool, list_customers_tool,
         update_customer_tool, deactivate_customer_tool, activate_customer_tool, search_customers_tool]
