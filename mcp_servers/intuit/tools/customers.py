from typing import Any, Dict, List

from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

customer_properties_user_define = {
    "DisplayName": {
        "type": "string",
        "description": "The name of the person or organization as displayed. Must be unique across all Customer, Vendor, and Employee objects. Cannot be removed with sparse update."
    },
    "Title": {
        "type": "string",
        "description": "Title of the person. This tag supports i18n, all locales."
    },
    "GivenName": {
        "type": "string",
        "description": "Given name or first name of a person."
    },
    "MiddleName": {
        "type": "string",
        "description": "Middle name of the person. The person can have zero or more middle names."
    },
    "Suffix": {
        "type": "string",
        "description": "Suffix of the name. For example, Jr."
    },
    "FamilyName": {
        "type": "string",
        "description": "Family name or the last name of the person."
    },
    "PrimaryEmailAddr": {
        "type": "string",
        "description": "Primary email address. The address format must follow the RFC 822 standard."
    },
    "ResaleNum": {
        "type": "string",
        "description": "Resale number or some additional info about the customer."
    },
    "SecondaryTaxIdentifier": {
        "type": "string",
        "description": "Also called UTR No. in (UK), CST Reg No. (IN) also represents the tax registration number of the Person or Organization. This value is masked in responses, exposing only last five characters."
    },
    "ARAccountRefValue": {
        "type": "string",
        "description": "The ID for the AR account used for this customer. Each customer must have his own AR account. Applicable for France companies, only."
    },
    "ARAccountRefName": {
        "type": "string",
        "description": "The name of the AR account used for this customer."
    },
    "DefaultTaxCodeRefValue": {
        "type": "string",
        "description": "The ID for the default tax code associated with this Customer object. Valid if Customer.Taxable is set to true; otherwise, it is ignored. If automated sales tax is enabled, the default tax code is set by the system and cannot be overridden."
    },
    "DefaultTaxCodeRefName": {
        "type": "string",
        "description": "The name of the default tax code associated with this Customer object."
    },
    "PreferredDeliveryMethod": {
        "type": "string",
        "description": "Preferred delivery method. Values are Print, Email, or None."
    },
    "GSTIN": {
        "type": "string",
        "description": "GSTIN is an identification number assigned to every GST registered business."
    },
    "SalesTermRefValue": {
        "type": "string",
        "description": "The ID for the sales term associated with this Customer object."
    },
    "SalesTermRefName": {
        "type": "string",
        "description": "The name of the sales term associated with this Customer object."
    },
    "CustomerTypeRef": {
        "type": "string",
        "description": "Reference to the customer type assigned to a customer. This field is only returned if the customer is assigned a customer type."
    },
    "Fax": {
        "type": "string",
        "description": "Fax number."
    },
    "BusinessNumber": {
        "type": "string",
        "description": "Also called, PAN (in India) is a code that acts as an identification for individuals, families and corporates, especially for those who pay taxes on their income."
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
    "Mobile": {
        "type": "string",
        "description": "Mobile phone number."
    },
    "Job": {
        "type": "boolean",
        "description": "If true, this is a Job or sub-customer. If false or null, this is a top level customer, not a Job or sub-customer."
    },
    "BalanceWithJobs": {
        "type": "number",
        "description": "Cumulative open balance amount for the Customer (or Job) and all its sub-jobs. Cannot be written to QuickBooks."
    },
    "PrimaryPhone": {
        "type": "string",
        "description": "Primary phone number."
    },
    "OpenBalanceDate": {
        "type": "string",
        "description": "Date of the Open Balance for the create operation. Write-on-create."
    },
    "Taxable": {
        "type": "boolean",
        "description": "If true, transactions for this customer are taxable."
    },
    "AlternatePhone": {
        "type": "string",
        "description": "Alternate phone number."
    },
    "MetaDataCreateTime": {
        "type": "string",
        "description": "Time the entity was created in the source domain. Format: YYYY-MM-DDTHH:MM:SS."
    },
    "MetaDataLastUpdatedTime": {
        "type": "string",
        "description": "Time the entity was last updated in the source domain. Format: YYYY-MM-DDTHH:MM:SS."
    },
    "ParentRefValue": {
        "type": "string",
        "description": "The ID for the immediate parent Customer object if this is a sub-customer or Job."
    },
    "ParentRefName": {
        "type": "string",
        "description": "The name of the immediate parent Customer object if this is a sub-customer or Job."
    },
    "Notes": {
        "type": "string",
        "description": "Free form text describing the Customer."
    },
    "WebAddr": {
        "type": "string",
        "description": "Website address of the Customer."
    },
    "Active": {
        "type": "boolean",
        "description": "If true, this entity is currently enabled for use by QuickBooks. If there is an amount in Customer.Balance when setting this Customer object to inactive through the QuickBooks UI, a CreditMemo balancing transaction is created for the amount."
    },
    "CompanyName": {
        "type": "string",
        "description": "The name of the company associated with the person or organization."
    },
    "Balance": {
        "type": "number",
        "description": "Specifies the open balance amount or the amount unpaid by the customer. For the create operation, this represents the opening balance for the customer. When returned in response to the query request it represents the current open balance (unpaid amount) for that customer. Write-on-create."
    },
    "ShipAddrLine1": {
        "type": "string",
        "description": "First line of the shipping address."
    },
    "ShipAddrLine2": {
        "type": "string",
        "description": "Second line of the shipping address."
    },
    "ShipAddrLine3": {
        "type": "string",
        "description": "Third line of the shipping address."
    },
    "ShipAddrLine4": {
        "type": "string",
        "description": "Fourth line of the shipping address."
    },
    "ShipAddrLine5": {
        "type": "string",
        "description": "Fifth line of the shipping address."
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
    "IsProject": {
        "type": "boolean",
        "description": "If true, indicates this is a Project."
    },
    "Source": {
        "type": "string",
        "description": "The Source type of the transactions created by QuickBooks Commerce. Valid values include: QBCommerce"
    },
    "PrimaryTaxIdentifier": {
        "type": "string",
        "description": "Also called Tax Reg. No in (UK), (CA), (IN), (AU) represents the tax ID of the Person or Organization. This value is masked in responses, exposing only last five characters."
    },
    "GSTRegistrationType": {
        "type": "string",
        "description": "For the filing of GSTR, transactions need to be classified depending on the type of customer to whom the sale is done. Possible values are: GST_REG_REG, GST_REG_COMP, GST_UNREG, CONSUMER, OVERSEAS, SEZ, DEEMED."
    },
    "PrintOnCheckName": {
        "type": "string",
        "description": "Name of the person or organization as printed on a check. If not provided, this is populated from DisplayName. Cannot be removed with sparse update."
    },
    "BillAddrLine1": {
        "type": "string",
        "description": "First line of the billing address."
    },
    "BillAddrLine2": {
        "type": "string",
        "description": "Second line of the billing address."
    },
    "BillAddrLine3": {
        "type": "string",
        "description": "Third line of the billing address."
    },
    "BillAddrLine4": {
        "type": "string",
        "description": "Fourth line of the billing address."
    },
    "BillAddrLine5": {
        "type": "string",
        "description": "Fifth line of the billing address."
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
    },
    "PaymentMethodRefValue": {
        "type": "string",
        "description": "The ID for the payment method associated with this Customer object."
    },
    "PaymentMethodRefName": {
        "type": "string",
        "description": "The name of the payment method associated with this Customer object."
    },
    "TaxExemptionReasonId": {
        "type": "integer",
        "description": "The tax exemption reason associated with this customer object. Applicable if automated sales tax is enabled. Valid values: 1=Federal government, 2=State government, 3=Local government, 4=Tribal government, 5=Charitable organization, 6=Religious organization, 7=Educational organization, 8=Hospital, 9=Resale, 10=Direct pay permit, 11=Multiple points of use, 12=Direct mail, 13=Agricultural production, 14=Industrial production/manufacturing, 15=Foreign diplomat"
    }
}
customer_properties = {
    **customer_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique identifier for the customer in QuickBooks. Sort order is ASC by default. System generated"
    },
}

customer_properties_full = {
    **customer_properties,
    "FullyQualifiedName": {
        "type": "string",
        "description": "Fully qualified name of the object. The fully qualified name prepends the topmost parent, followed by each sub element separated by colons. Takes the form of Customer:Job:Sub-job. System generated."
    },
}

# MCP Tool definitions
create_customer_tool = Tool(
    name="create_customer",
    description="Create a new customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": customer_properties_user_define,
    },
)

get_customer_tool = Tool(
    name="get_customer",
    description="Get a specific customer by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID"}
        },
        "required": ["Id"]
    },
)

list_customers_tool = Tool(
    name="list_customers",
    description="List all customers from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "ActiveOnly": {"type": "boolean", "description": "Return only active customers", "default": True}
        }
    },
)

update_customer_tool = Tool(
    name="update_customer",
    description="Update an existing customer in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": customer_properties,
        "required": ["Id"]
    },
)

deactivate_customer_tool = Tool(
    name="deactivate_customer",
    description="Deactivate a customer from QuickBooks (set Active to false)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID to deactivate"}
        },
        "required": ["Id"]
    },
)

activate_customer_tool = Tool(
    name="activate_customer",
    description="Activate a customer in QuickBooks (set Active to true)",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks customer ID to activate"}
        },
        "required": ["Id"]
    },
)


def mcp_object_to_customer_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks customer data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    customer_data = {}

    # Basic customer information - direct copy
    for field in ['DisplayName', 'Title', 'GivenName', 'MiddleName', 'FamilyName',
                  'Suffix', 'CompanyName', 'ResaleNum', 'SecondaryTaxIdentifier',
                  'BusinessNumber', 'GSTIN', 'GSTRegistrationType', 'PrimaryTaxIdentifier',
                  'PreferredDeliveryMethod', 'Notes', 'PrintOnCheckName', 'Source']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Contact information - convert to structured objects
    if 'PrimaryEmailAddr' in kwargs:
        customer_data['PrimaryEmailAddr'] = {
            'Address': kwargs['PrimaryEmailAddr']}

    for phone_field in ['PrimaryPhone', 'Mobile', 'AlternatePhone', 'Fax']:
        if phone_field in kwargs:
            customer_data[phone_field] = {
                'FreeFormNumber': kwargs[phone_field]}

    if 'WebAddr' in kwargs:
        customer_data['WebAddr'] = {'URI': kwargs['WebAddr']}

    # Reference objects - convert separate value/name fields to structured objects
    ref_mappings = [
        ('ARAccountRef', 'ARAccountRefValue', 'ARAccountRefName'),
        ('DefaultTaxCodeRef', 'DefaultTaxCodeRefValue', 'DefaultTaxCodeRefName'),
        ('SalesTermRef', 'SalesTermRefValue', 'SalesTermRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('ParentRef', 'ParentRefValue', 'ParentRefName'),
        ('PaymentMethodRef', 'PaymentMethodRefValue', 'PaymentMethodRefName')
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if value_field in kwargs:
            ref_obj = {'value': kwargs[value_field]}
            if name_field in kwargs:
                ref_obj['name'] = kwargs[name_field]
            customer_data[ref_name] = ref_obj

    if 'CustomerTypeRef' in kwargs:
        customer_data['CustomerTypeRef'] = {'value': kwargs['CustomerTypeRef']}

    # Address fields - convert flattened fields to structured objects
    for addr_type in ['BillAddr', 'ShipAddr']:
        address_fields = ['Line1', 'Line2', 'Line3', 'Line4', 'Line5',
                          'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']

        has_address = any(kwargs.get(f'{addr_type}{field}')
                          for field in address_fields)
        if has_address:
            addr_obj = {}
            for field in address_fields:
                if kwargs.get(f'{addr_type}{field}'):
                    addr_obj[field] = kwargs[f'{addr_type}{field}']
            customer_data[addr_type] = addr_obj

    # Boolean fields
    for field in ['BillWithParent', 'Job', 'Taxable', 'Active', 'IsProject']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Numeric fields
    for field in ['Balance', 'BalanceWithJobs', 'TaxExemptionReasonId']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Date fields
    for field in ['OpenBalanceDate']:
        if field in kwargs:
            customer_data[field] = kwargs[field]

    # Metadata fields - convert to structured object
    if 'MetaDataCreateTime' in kwargs or 'MetaDataLastUpdatedTime' in kwargs:
        customer_data['MetaData'] = {}
        if 'MetaDataCreateTime' in kwargs:
            customer_data['MetaData']['CreateTime'] = kwargs['MetaDataCreateTime']
        if 'MetaDataLastUpdatedTime' in kwargs:
            customer_data['MetaData']['LastUpdatedTime'] = kwargs['MetaDataLastUpdatedTime']

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
        'PreferredDeliveryMethod', 'Notes', 'PrintOnCheckName', 'Source',
        'ARAccountRefValue', 'ARAccountRefName', 'DefaultTaxCodeRefValue', 'DefaultTaxCodeRefName',
        'SalesTermRefValue', 'SalesTermRefName', 'CurrencyRefValue', 'CurrencyRefName',
        'CustomerTypeRef', 'ParentRefValue', 'ParentRefName', 'PaymentMethodRefValue', 'PaymentMethodRefName',
        'BillAddrLine1', 'BillAddrLine2', 'BillAddrLine3', 'BillAddrLine4', 'BillAddrLine5',
        'BillAddrCity', 'BillAddrCountrySubDivisionCode', 'BillAddrPostalCode', 'BillAddrCountry',
        'ShipAddrLine1', 'ShipAddrLine2', 'ShipAddrLine3', 'ShipAddrLine4', 'ShipAddrLine5',
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
            for field in ['Line1', 'Line2', 'Line3', 'Line4', 'Line5',
                          'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']:
                if field in addr:
                    mcp_object[f'BillAddr{field}'] = addr[field]
    if 'ShipAddr' in customer_data:
        addr = customer_data['ShipAddr']
        if isinstance(addr, dict):
            for field in ['Line1', 'Line2', 'Line3', 'Line4', 'Line5',
                          'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']:
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
            'Title' in kwargs,
            'MiddleName' in kwargs,
            'Suffix' in kwargs
        ])

        if not display_name_provided and not name_components_provided:
            raise ValueError(
                "At least one of: DisplayName, GivenName, FamilyName, Title, MiddleName, Suffix must be provided.")

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


# Export tools
tools = [create_customer_tool, get_customer_tool, list_customers_tool,
         update_customer_tool, deactivate_customer_tool, activate_customer_tool]
