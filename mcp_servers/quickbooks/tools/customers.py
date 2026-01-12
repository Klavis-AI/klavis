from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

customer_properties_user_define = {
    "display_name": {
        "type": "string",
        "description": "The display name (must be unique across all customers, vendors, employees)"
    },
    "first_name": {
        "type": "string",
        "description": "First/given name"
    },
    "middle_name": {
        "type": "string",
        "description": "Middle name"
    },
    "last_name": {
        "type": "string",
        "description": "Last/family name"
    },
    "company": {
        "type": "string",
        "description": "Company name"
    },
    "email": {
        "type": "string",
        "description": "Primary email address"
    },
    "phone": {
        "type": "string",
        "description": "Primary phone number"
    },
    "website": {
        "type": "string",
        "description": "Website URL"
    },
    "notes": {
        "type": "string",
        "description": "Notes or description"
    },
    "is_taxable": {
        "type": "boolean",
        "description": "Whether transactions for this customer are taxable"
    },
    "bill_with_parent": {
        "type": "boolean",
        "description": "Whether to bill this customer with its parent (for sub-customers)"
    },
    "currency": {
        "type": "string",
        "description": "Currency code (e.g., USD, EUR)"
    },
    "payment_method_id": {
        "type": "string",
        "description": "Payment method ID"
    },
    "tax_code_id": {
        "type": "string",
        "description": "Default tax code ID"
    },
    "balance": {
        "type": "number",
        "description": "Opening balance amount (write-on-create only)"
    },
    "open_balance_date": {
        "type": "string",
        "description": "Date of the opening balance (YYYY-MM-DD, write-on-create only)"
    },
    "billing_street": {
        "type": "string",
        "description": "Billing address street line 1"
    },
    "billing_street2": {
        "type": "string",
        "description": "Billing address street line 2"
    },
    "billing_city": {
        "type": "string",
        "description": "Billing address city"
    },
    "billing_state": {
        "type": "string",
        "description": "Billing address state/province"
    },
    "billing_postal_code": {
        "type": "string",
        "description": "Billing address postal/zip code"
    },
    "billing_country": {
        "type": "string",
        "description": "Billing address country"
    },
    "shipping_street": {
        "type": "string",
        "description": "Shipping address street line 1"
    },
    "shipping_street2": {
        "type": "string",
        "description": "Shipping address street line 2"
    },
    "shipping_city": {
        "type": "string",
        "description": "Shipping address city"
    },
    "shipping_state": {
        "type": "string",
        "description": "Shipping address state/province"
    },
    "shipping_postal_code": {
        "type": "string",
        "description": "Shipping address postal/zip code"
    },
    "shipping_country": {
        "type": "string",
        "description": "Shipping address country"
    }
}

customer_properties = {
    **customer_properties_user_define,
    "id": {
        "type": "string",
        "description": "The unique customer ID"
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
            "id": {"type": "string", "description": "The customer ID"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER", "readOnlyHint": True}),
)

list_customers_tool = Tool(
    name="quickbooks_list_customers",
    description="List all customers from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "active_only": {"type": "boolean", "description": "Return only active customers", "default": True}
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
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

deactivate_customer_tool = Tool(
    name="quickbooks_deactivate_customer",
    description="Deactivate a customer from QuickBooks (set Active to false)",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The customer ID to deactivate"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

activate_customer_tool = Tool(
    name="quickbooks_activate_customer",
    description="Activate a customer in QuickBooks (set Active to true)",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The customer ID to activate"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER"}),
)

search_customers_tool = Tool(
    name="quickbooks_search_customers",
    title="Search Customers",
    description="Search customers with filters including name, contact info, address, balance, and status",
    inputSchema={
        "type": "object",
        "properties": {
            # Name filters
            "display_name": {"type": "string", "description": "Search by display name (partial match)"},
            "first_name": {"type": "string", "description": "Search by first name (partial match)"},
            "last_name": {"type": "string", "description": "Search by last name (partial match)"},
            "company": {"type": "string", "description": "Search by company name (partial match)"},

            # Contact filters
            "email": {"type": "string", "description": "Search by email (partial match)"},
            "phone": {"type": "string", "description": "Search by phone (partial match)"},

            # Status filters
            "is_active": {"type": "boolean", "description": "Filter by active status"},
            "is_taxable": {"type": "boolean", "description": "Filter by taxable status"},

            # Address filters - Billing
            "billing_city": {"type": "string", "description": "Filter by billing city"},
            "billing_state": {"type": "string", "description": "Filter by billing state/province"},
            "billing_postal_code": {"type": "string", "description": "Filter by billing postal code"},
            "billing_country": {"type": "string", "description": "Filter by billing country"},

            # Address filters - Shipping
            "shipping_city": {"type": "string", "description": "Filter by shipping city"},
            "shipping_state": {"type": "string", "description": "Filter by shipping state/province"},
            "shipping_postal_code": {"type": "string", "description": "Filter by shipping postal code"},
            "shipping_country": {"type": "string", "description": "Filter by shipping country"},

            # Balance filters
            "min_balance": {"type": "number", "description": "Minimum balance amount"},
            "max_balance": {"type": "number", "description": "Maximum balance amount"},

            # Other filters
            "currency": {"type": "string", "description": "Filter by currency code"},

            # Pagination
            "max_results": {"type": "integer", "description": "Maximum results to return", "default": 100},
            "start_position": {"type": "integer", "description": "Starting position (1-based)", "default": 1}
        }
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_CUSTOMER", "readOnlyHint": True})
)


def mcp_object_to_customer_data(**kwargs) -> Dict[str, Any]:
    """
    Convert simplified MCP object format to QuickBooks customer data format.
    Maps user-friendly snake_case fields to QuickBooks API structure.
    """
    customer_data = {}

    # Field mappings: simplified_name -> QuickBooks_name
    simple_field_mappings = {
        'display_name': 'DisplayName',
        'first_name': 'GivenName',
        'middle_name': 'MiddleName',
        'last_name': 'FamilyName',
        'company': 'CompanyName',
        'notes': 'Notes',
    }

    for simple_name, qb_name in simple_field_mappings.items():
        if simple_name in kwargs:
            customer_data[qb_name] = kwargs[simple_name]

    # Contact information - convert to structured objects
    if 'email' in kwargs:
        customer_data['PrimaryEmailAddr'] = {'Address': kwargs['email']}

    if 'phone' in kwargs:
        customer_data['PrimaryPhone'] = {'FreeFormNumber': kwargs['phone']}

    if 'website' in kwargs:
        customer_data['WebAddr'] = {'URI': kwargs['website']}

    # Reference objects
    if 'currency' in kwargs:
        customer_data['CurrencyRef'] = {'value': kwargs['currency']}

    if 'payment_method_id' in kwargs:
        customer_data['PaymentMethodRef'] = {'value': kwargs['payment_method_id']}

    if 'tax_code_id' in kwargs:
        customer_data['DefaultTaxCodeRef'] = {'value': kwargs['tax_code_id']}

    # Billing address
    billing_field_mappings = {
        'billing_street': 'Line1',
        'billing_street2': 'Line2',
        'billing_city': 'City',
        'billing_state': 'CountrySubDivisionCode',
        'billing_postal_code': 'PostalCode',
        'billing_country': 'Country',
    }
    billing_addr = {}
    for simple_name, qb_name in billing_field_mappings.items():
        if simple_name in kwargs:
            billing_addr[qb_name] = kwargs[simple_name]
    if billing_addr:
        customer_data['BillAddr'] = billing_addr

    # Shipping address
    shipping_field_mappings = {
        'shipping_street': 'Line1',
        'shipping_street2': 'Line2',
        'shipping_city': 'City',
        'shipping_state': 'CountrySubDivisionCode',
        'shipping_postal_code': 'PostalCode',
        'shipping_country': 'Country',
    }
    shipping_addr = {}
    for simple_name, qb_name in shipping_field_mappings.items():
        if simple_name in kwargs:
            shipping_addr[qb_name] = kwargs[simple_name]
    if shipping_addr:
        customer_data['ShipAddr'] = shipping_addr

    # Boolean fields
    if 'is_taxable' in kwargs:
        customer_data['Taxable'] = kwargs['is_taxable']
    if 'bill_with_parent' in kwargs:
        customer_data['BillWithParent'] = kwargs['bill_with_parent']

    # Numeric fields
    if 'balance' in kwargs:
        customer_data['Balance'] = kwargs['balance']

    # Date fields
    if 'open_balance_date' in kwargs:
        customer_data['OpenBalanceDate'] = kwargs['open_balance_date']

    return customer_data


def customer_data_to_mcp_object(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks customer data format to simplified MCP object format.
    Uses cleaner, more intuitive field names for better usability.
    """
    result = {}

    # Core identification
    if 'Id' in customer_data:
        result['id'] = customer_data['Id']
    if 'DisplayName' in customer_data:
        result['display_name'] = customer_data['DisplayName']
    if 'CompanyName' in customer_data:
        result['company'] = customer_data['CompanyName']
    if 'FullyQualifiedName' in customer_data:
        result['full_name'] = customer_data['FullyQualifiedName']

    # Personal name fields
    name_parts = {}
    if 'GivenName' in customer_data:
        name_parts['first'] = customer_data['GivenName']
    if 'MiddleName' in customer_data:
        name_parts['middle'] = customer_data['MiddleName']
    if 'FamilyName' in customer_data:
        name_parts['last'] = customer_data['FamilyName']
    if 'Title' in customer_data:
        name_parts['title'] = customer_data['Title']
    if 'Suffix' in customer_data:
        name_parts['suffix'] = customer_data['Suffix']
    if name_parts:
        result['name'] = name_parts

    # Contact information
    contact = {}
    if 'PrimaryEmailAddr' in customer_data:
        addr = customer_data['PrimaryEmailAddr']
        contact['email'] = addr['Address'] if isinstance(addr, dict) else addr
    if 'PrimaryPhone' in customer_data:
        phone = customer_data['PrimaryPhone']
        contact['phone'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'Mobile' in customer_data:
        phone = customer_data['Mobile']
        contact['mobile'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'Fax' in customer_data:
        phone = customer_data['Fax']
        contact['fax'] = phone.get('FreeFormNumber') if isinstance(phone, dict) else phone
    if 'WebAddr' in customer_data:
        web = customer_data['WebAddr']
        contact['website'] = web.get('URI') if isinstance(web, dict) else web
    if contact:
        result['contact'] = contact

    # Billing address (simplified structure)
    if 'BillAddr' in customer_data and isinstance(customer_data['BillAddr'], dict):
        addr = customer_data['BillAddr']
        billing = {}
        if 'Line1' in addr:
            billing['street'] = addr['Line1']
        if 'Line2' in addr:
            billing['street2'] = addr['Line2']
        if 'City' in addr:
            billing['city'] = addr['City']
        if 'CountrySubDivisionCode' in addr:
            billing['state'] = addr['CountrySubDivisionCode']
        if 'PostalCode' in addr:
            billing['postal_code'] = addr['PostalCode']
        if 'Country' in addr:
            billing['country'] = addr['Country']
        if billing:
            result['billing_address'] = billing

    # Shipping address (simplified structure)
    if 'ShipAddr' in customer_data and isinstance(customer_data['ShipAddr'], dict):
        addr = customer_data['ShipAddr']
        shipping = {}
        if 'Line1' in addr:
            shipping['street'] = addr['Line1']
        if 'Line2' in addr:
            shipping['street2'] = addr['Line2']
        if 'City' in addr:
            shipping['city'] = addr['City']
        if 'CountrySubDivisionCode' in addr:
            shipping['state'] = addr['CountrySubDivisionCode']
        if 'PostalCode' in addr:
            shipping['postal_code'] = addr['PostalCode']
        if 'Country' in addr:
            shipping['country'] = addr['Country']
        if shipping:
            result['shipping_address'] = shipping

    # Financial info
    if 'Balance' in customer_data:
        result['balance'] = customer_data['Balance']
    if 'BalanceWithJobs' in customer_data:
        result['balance_with_jobs'] = customer_data['BalanceWithJobs']
    if 'OpenBalanceDate' in customer_data:
        result['open_balance_date'] = customer_data['OpenBalanceDate']

    # Status flags
    if 'Active' in customer_data:
        result['is_active'] = customer_data['Active']
    if 'Taxable' in customer_data:
        result['is_taxable'] = customer_data['Taxable']
    if 'Job' in customer_data:
        result['is_job'] = customer_data['Job']
    if 'IsProject' in customer_data:
        result['is_project'] = customer_data['IsProject']
    if 'BillWithParent' in customer_data:
        result['bill_with_parent'] = customer_data['BillWithParent']

    # Currency and payment
    if 'CurrencyRef' in customer_data and isinstance(customer_data['CurrencyRef'], dict):
        result['currency'] = customer_data['CurrencyRef'].get('value')
    if 'PaymentMethodRef' in customer_data and isinstance(customer_data['PaymentMethodRef'], dict):
        result['payment_method'] = customer_data['PaymentMethodRef'].get('name') or customer_data['PaymentMethodRef'].get('value')

    # Additional info
    if 'Notes' in customer_data:
        result['notes'] = customer_data['Notes']

    # Parent customer (for sub-customers/jobs)
    if 'ParentRef' in customer_data and isinstance(customer_data['ParentRef'], dict):
        result['parent_id'] = customer_data['ParentRef'].get('value')
        result['parent_name'] = customer_data['ParentRef'].get('name')

    # Timestamps
    if 'MetaData' in customer_data and isinstance(customer_data['MetaData'], dict):
        metadata = customer_data['MetaData']
        if 'CreateTime' in metadata:
            result['created_at'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            result['updated_at'] = metadata['LastUpdatedTime']

    return result


class CustomerManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_customer(self, **kwargs) -> Dict[str, Any]:
        # Validate we have display_name or at least one name component
        display_name_provided = 'display_name' in kwargs
        name_components_provided = any([
            'first_name' in kwargs,
            'last_name' in kwargs,
            'middle_name' in kwargs,
        ])

        if not display_name_provided and not name_components_provided:
            raise ValueError(
                "At least one of: display_name, first_name, last_name, middle_name must be provided.")

        customer_data = mcp_object_to_customer_data(**kwargs)
        response = await self.client._post('customer', customer_data)

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def get_customer(self, id: str) -> Dict[str, Any]:
        response = await self.client._get(f"customer/{id}")

        # Convert response back to MCP format
        return customer_data_to_mcp_object(response['Customer'])

    async def list_customers(self, max_results: int = 100, active_only: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Customer"
        if active_only:
            query += " WHERE Active = true"
        query += f" STARTPOSITION 1 MAXRESULTS {max_results}"
        response = await self.client._get('query', params={'query': query})

        # Convert response back to MCP format
        customers = response['QueryResponse']['Customer']
        return [customer_data_to_mcp_object(customer) for customer in customers]

    async def update_customer(self, **kwargs) -> Dict[str, Any]:
        customer_id = kwargs.get('id')
        if not customer_id:
            raise ValueError("id is required for updating a customer")

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

    async def deactivate_customer(self, id: str) -> Dict[str, Any]:
        # First get the current customer to obtain the SyncToken
        current_customer_response = await self.client._get(f"customer/{id}")
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

    async def activate_customer(self, id: str) -> Dict[str, Any]:
        # First get the current customer to obtain the SyncToken
        current_customer_response = await self.client._get(f"customer/{id}")
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
            display_name: Search by display name (partial match)
            first_name/last_name/company: Search by name (partial match)
            email/phone: Search by contact info (partial match)
            is_active/is_taxable: Filter by status
            billing_city/billing_state/billing_postal_code/billing_country: Filter by billing address
            shipping_city/shipping_state/shipping_postal_code/shipping_country: Filter by shipping address
            min_balance/max_balance: Filter by balance range
            currency: Filter by currency code
            max_results: Maximum results (default: 100)
            start_position: Starting position (default: 1)

        Returns:
            List of customers matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Status filters
        if kwargs.get('is_active') is not None:
            conditions.append(f"Active = {str(kwargs['is_active']).lower()}")

        if kwargs.get('is_taxable') is not None:
            conditions.append(f"Taxable = {str(kwargs['is_taxable']).lower()}")

        # Currency filter
        if kwargs.get('currency'):
            conditions.append(f"CurrencyRef.value = '{kwargs['currency']}'")

        # Address filters - exact matches for structured fields
        address_exact_fields = {
            'billing_city': 'BillAddr.City',
            'billing_state': 'BillAddr.CountrySubDivisionCode',
            'billing_postal_code': 'BillAddr.PostalCode',
            'billing_country': 'BillAddr.Country',
            'shipping_city': 'ShipAddr.City',
            'shipping_state': 'ShipAddr.CountrySubDivisionCode',
            'shipping_postal_code': 'ShipAddr.PostalCode',
            'shipping_country': 'ShipAddr.Country'
        }

        for field, qb_field in address_exact_fields.items():
            if kwargs.get(field):
                conditions.append(f"{qb_field} = '{kwargs[field]}'")

        # Balance range filters
        if kwargs.get('min_balance') is not None:
            conditions.append(f"Balance >= {kwargs['min_balance']}")
        if kwargs.get('max_balance') is not None:
            conditions.append(f"Balance <= {kwargs['max_balance']}")

        # Partial match filters - we'll post-filter these due to QB API limitations
        partial_match_filters = {}

        # Map simplified field names to QuickBooks field names
        partial_field_mappings = {
            'display_name': 'DisplayName',
            'first_name': 'GivenName',
            'last_name': 'FamilyName',
            'company': 'CompanyName',
            'email': 'PrimaryEmailAddr',
            'phone': 'PrimaryPhone',
        }

        for simple_name, qb_name in partial_field_mappings.items():
            if kwargs.get(simple_name):
                partial_match_filters[qb_name] = kwargs[simple_name].lower()

        # Build the query
        query = "SELECT * FROM Customer"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add pagination
        max_results = kwargs.get('max_results', 100)
        start_position = kwargs.get('start_position', 1)

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
                    if field in ['DisplayName', 'GivenName', 'FamilyName', 'CompanyName']:
                        if field in customer and search_value not in customer[field].lower():
                            should_include = False
                            break
                    elif field == 'PrimaryEmailAddr' and 'PrimaryEmailAddr' in customer:
                        email_data = customer['PrimaryEmailAddr']
                        email_str = email_data.get('Address', '') if isinstance(email_data, dict) else str(email_data)
                        if search_value not in email_str.lower():
                            should_include = False
                            break
                    elif field == 'PrimaryPhone' and 'PrimaryPhone' in customer:
                        phone_data = customer['PrimaryPhone']
                        phone_str = phone_data.get('FreeFormNumber', '') if isinstance(phone_data, dict) else str(phone_data)
                        if search_value not in phone_str.lower():
                            should_include = False
                            break

                if should_include:
                    filtered_customers.append(customer)

            customers = filtered_customers

        return [customer_data_to_mcp_object(customer) for customer in customers]


# Export tools
tools = [create_customer_tool, get_customer_tool, list_customers_tool,
         update_customer_tool, deactivate_customer_tool, activate_customer_tool, search_customers_tool]
