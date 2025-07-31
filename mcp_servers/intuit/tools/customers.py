from typing import Any, Dict, List, Optional

from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

# MCP Tool definitions
create_customer_tool = Tool(
    name="create_customer",
    description="Create a new customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "display_name": {"type": "string", "description": "The name of the customer as displayed"},
            "given_name": {"type": "string", "description": "First name of the customer"},
            "family_name": {"type": "string", "description": "Last name of the customer"},
            "company_name": {"type": "string", "description": "Company name if applicable"},
            "email": {"type": "string", "description": "Customer email address"},
            "phone": {"type": "string", "description": "Primary phone number"},
            "mobile": {"type": "string", "description": "Mobile phone number"},
            "fax": {"type": "string", "description": "Fax number"},
            "web_site": {"type": "string", "description": "Customer website"},
            "bill_line1": {"type": "string", "description": "Billing address line 1"},
            "bill_line2": {"type": "string", "description": "Billing address line 2"},
            "bill_city": {"type": "string", "description": "Billing city"},
            "bill_state": {"type": "string", "description": "Billing state/province"},
            "bill_postal_code": {"type": "string", "description": "Billing postal/zip code"},
            "bill_country": {"type": "string", "description": "Billing country"},
            "ship_line1": {"type": "string", "description": "Shipping address line 1"},
            "ship_line2": {"type": "string", "description": "Shipping address line 2"},
            "ship_city": {"type": "string", "description": "Shipping city"},
            "ship_state": {"type": "string", "description": "Shipping state/province"},
            "ship_postal_code": {"type": "string", "description": "Shipping postal/zip code"},
            "ship_country": {"type": "string", "description": "Shipping country"}
        },
        "required": ["display_name"]
    }
)

get_customer_tool = Tool(
    name="get_customer",
    description="Get a specific customer by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "The QuickBooks customer ID"}
        },
        "required": ["customer_id"]
    }
)

list_customers_tool = Tool(
    name="list_customers",
    description="List all customers from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "active_only": {"type": "boolean", "description": "Return only active customers", "default": True}
        }
    }
)

update_customer_tool = Tool(
    name="update_customer",
    description="Update an existing customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "The QuickBooks customer ID"},
            "display_name": {"type": "string", "description": "Updated display name"},
            "given_name": {"type": "string", "description": "Updated first name"},
            "family_name": {"type": "string", "description": "Updated last name"},
            "company_name": {"type": "string", "description": "Updated company name"},
            "email": {"type": "string", "description": "Updated email address"},
            "phone": {"type": "string", "description": "Updated phone number"},
            "web_site": {"type": "string", "description": "Updated website"},
            "bill_line1": {"type": "string", "description": "Updated billing address line 1"},
            "bill_line2": {"type": "string", "description": "Updated billing address line 2"},
            "bill_city": {"type": "string", "description": "Updated billing city"},
            "bill_state": {"type": "string", "description": "Updated billing state"},
            "bill_postal_code": {"type": "string", "description": "Updated billing postal code"},
            "ship_line1": {"type": "string", "description": "Updated shipping address line 1"},
            "ship_line2": {"type": "string", "description": "Updated shipping address line 2"},
            "ship_city": {"type": "string", "description": "Updated shipping city"},
            "ship_state": {"type": "string", "description": "Updated shipping state"},
            "ship_postal_code": {"type": "string", "description": "Updated shipping postal code"}
        },
        "required": ["customer_id"]
    }
)

delete_customer_tool = Tool(
    name="delete_customer",
    description="Delete a customer from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "The QuickBooks customer ID to delete"}
        },
        "required": ["customer_id"]
    }
)

class CustomerManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_customer(self, **kwargs) -> Dict[str, Any]:
        customer_data = {}
        
        if 'display_name' in kwargs:
            customer_data['DisplayName'] = kwargs['display_name']
        if 'given_name' in kwargs:
            customer_data['GivenName'] = kwargs['given_name']
        if 'family_name' in kwargs:
            customer_data['FamilyName'] = kwargs['family_name']
        if 'company_name' in kwargs:
            customer_data['CompanyName'] = kwargs['company_name']
            # When company_name is provided, PrimaryEmailAddr might be required
            if 'email' not in kwargs:
                kwargs['email'] = f"{kwargs['company_name'].replace(' ', '').lower()}@example.com"
        
        # Contact info
        contact_info = {}
        if 'email' in kwargs:
            contact_info['EmailAddr'] = {'Address': kwargs['email']}
        if 'phone' in kwargs:
            contact_info['PrimaryPhone'] = {'FreeFormNumber': kwargs['phone']}
        if 'mobile' in kwargs:
            contact_info['Mobile'] = {'FreeFormNumber': kwargs['mobile']}
        if 'fax' in kwargs:
            contact_info['Fax'] = {'FreeFormNumber': kwargs['fax']}
        if 'web_site' in kwargs:
            contact_info['WebAddr'] = {'URI': kwargs['web_site']}
        
        if contact_info:
            customer_data.update(contact_info)

        # Billing address
        has_billing = any(kwargs.get(f'bill_{k}') for k in ['line1', 'city', 'state', 'postal_code', 'country'])
        if has_billing:
            billing_addr = {}
            if kwargs.get('bill_line1'):
                billing_addr['Line1'] = kwargs['bill_line1']
            if kwargs.get('bill_line2'):
                billing_addr['Line2'] = kwargs['bill_line2']
            if kwargs.get('bill_city'):
                billing_addr['City'] = kwargs['bill_city']
            if kwargs.get('bill_state'):
                billing_addr['CountrySubDivisionCode'] = kwargs['bill_state']
            if kwargs.get('bill_postal_code'):
                billing_addr['PostalCode'] = kwargs['bill_postal_code']
            if kwargs.get('bill_country'):
                billing_addr['Country'] = kwargs['bill_country']
            customer_data['BillAddr'] = billing_addr

        # Shipping address
        has_shipping = any(kwargs.get(f'ship_{k}') for k in ['line1', 'city', 'state', 'postal_code', 'country'])
        if has_shipping:
            shipping_addr = {}
            if kwargs.get('ship_line1'):
                shipping_addr['Line1'] = kwargs['ship_line1']
            if kwargs.get('ship_line2'):
                shipping_addr['Line2'] = kwargs['ship_line2']
            if kwargs.get('ship_city'):
                shipping_addr['City'] = kwargs['ship_city']
            if kwargs.get('ship_state'):
                shipping_addr['CountrySubDivisionCode'] = kwargs['ship_state']
            if kwargs.get('ship_postal_code'):
                shipping_addr['PostalCode'] = kwargs['ship_postal_code']
            if kwargs.get('ship_country'):
                shipping_addr['Country'] = kwargs['ship_country']
            customer_data['ShipAddr'] = shipping_addr

        return await self.client._post('customer', customer_data)

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        return await self.client._get(f"customer/{customer_id}")

    async def list_customers(self, max_results: int = 100, active_only: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM Customer"
        if active_only:
            query += " WHERE Active = true"
        query += f" STARTPOSITION 1 MAXRESULTS {max_results}"
        return await self.client._get('query', params={'query': query})

    async def update_customer(self, customer_id: str, **kwargs) -> Dict[str, Any]:
        customer_data = {
            "Id": customer_id,
            "SyncToken": kwargs.get('sync_token', '0'),
            "sparse": True
        }

        if 'display_name' in kwargs:
            customer_data['DisplayName'] = kwargs['display_name']
        if 'given_name' in kwargs:
            customer_data['GivenName'] = kwargs['given_name']
        if 'family_name' in kwargs:
            customer_data['FamilyName'] = kwargs['family_name']
        if 'company_name' in kwargs:
            customer_data['CompanyName'] = kwargs['company_name']
            # Ensure email exists when company name is provided
            if 'email' not in kwargs and 'company_name' in kwargs:
                kwargs['email'] = f"{kwargs['company_name'].replace(' ', '').lower()}@example.com"
        if 'email' in kwargs and kwargs['email']:
            customer_data['EmailAddr'] = {'Address': kwargs['email']}
        if 'phone' in kwargs and kwargs['phone']:
            customer_data['PrimaryPhone'] = {'FreeFormNumber': kwargs['phone']}
        if 'web_site' in kwargs and kwargs['web_site']:
            customer_data['WebAddr'] = {'URI': kwargs['web_site']}

        # Billing address updates
        if any(kwargs.get(f'bill_{k}') for k in ['line1', 'city', 'state', 'postal_code']):
            billing_addr = {}
            if kwargs.get('bill_line1'):
                billing_addr['Line1'] = kwargs['bill_line1']
            if kwargs.get('bill_line2'):
                billing_addr['Line2'] = kwargs['bill_line2']
            if kwargs.get('bill_city'):
                billing_addr['City'] = kwargs['bill_city']
            if kwargs.get('bill_state'):
                billing_addr['CountrySubDivisionCode'] = kwargs['bill_state']
            if kwargs.get('bill_postal_code'):
                billing_addr['PostalCode'] = kwargs['bill_postal_code']
            if billing_addr:
                customer_data['BillAddr'] = billing_addr

        # Shipping address updates
        if any(kwargs.get(f'ship_{k}') for k in ['line1', 'city', 'state', 'postal_code']):
            shipping_addr = {}
            if kwargs.get('ship_line1'):
                shipping_addr['Line1'] = kwargs['ship_line1']
            if kwargs.get('ship_line2'):
                shipping_addr['Line2'] = kwargs['ship_line2']
            if kwargs.get('ship_city'):
                shipping_addr['City'] = kwargs['ship_city']
            if kwargs.get('ship_state'):
                shipping_addr['CountrySubDivisionCode'] = kwargs['ship_state']
            if kwargs.get('ship_postal_code'):
                shipping_addr['PostalCode'] = kwargs['ship_postal_code']
            if shipping_addr:
                customer_data['ShipAddr'] = shipping_addr

        return await self.client._post('customer', customer_data)

    async def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        customer_data = {
            "Id": customer_id
        }
        return await self.client._post('customer?operation=delete', customer_data)

# Export tools
tools = [create_customer_tool, get_customer_tool, list_customers_tool, update_customer_tool, delete_customer_tool]