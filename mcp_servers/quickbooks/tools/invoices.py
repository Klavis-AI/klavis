from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Minimal properties for invoice creation (required by QuickBooks)
invoice_properties_minimal = {
    "customer_id": {
        "type": "string",
        "description": "Customer ID for the invoice"
    },
    "line_items": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "line_id": {"type": "string", "description": "Unique ID for this line item (required for updates)"},
                "amount": {"type": "number", "description": "Line total amount"},
                "description": {"type": "string", "description": "Line item description"},
                "type": {"type": "string", "description": "Line type: sales_item, description_only, discount, subtotal", "default": "sales_item"},

                # Sales item fields
                "item_id": {"type": "string", "description": "Inventory item ID"},
                "item_name": {"type": "string", "description": "Inventory item name"},
                "quantity": {"type": "number", "description": "Quantity"},
                "unit_price": {"type": "number", "description": "Unit price"},
                "discount_rate": {"type": "number", "description": "Discount rate percentage"},
                "discount_amount": {"type": "number", "description": "Discount amount"},
                "service_date": {"type": "string", "description": "Service date (YYYY-MM-DD)"},

                # Discount fields
                "discount_percent": {"type": "number", "description": "Discount percentage (10 for 10%)"},
                "is_percent": {"type": "boolean", "description": "True if discount is percentage-based"},

                "tax_code_id": {"type": "string", "description": "Tax code ID"}
            },
            "required": ["amount"]
        }
    },
}

# Invoice properties mapping (based on QuickBooks API documentation)
invoice_properties_user_define = {
    **invoice_properties_minimal,
    "invoice_number": {
        "type": "string",
        "description": "Invoice/document number"
    },
    "date": {
        "type": "string",
        "description": "Transaction date (YYYY-MM-DD)"
    },
    "ship_date": {
        "type": "string",
        "description": "Ship date (YYYY-MM-DD)"
    },
    "due_date": {
        "type": "string",
        "description": "Due date (YYYY-MM-DD)"
    },
    "customer_memo": {
        "type": "string",
        "description": "Message to the customer"
    },
    "bill_email": {
        "type": "string",
        "description": "Email address to send invoice"
    },
    "bill_email_cc": {
        "type": "string",
        "description": "CC email address"
    },
    "currency": {
        "type": "string",
        "description": "Currency code (e.g., USD)"
    },
    "tracking_number": {
        "type": "string",
        "description": "Shipping tracking number"
    },
    "deposit": {
        "type": "number",
        "description": "Deposit amount"
    },
    "ship_method_id": {
        "type": "string",
        "description": "Shipping method ID"
    },
    # Billing address
    "billing_street": {
        "type": "string",
        "description": "Billing address street"
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
        "description": "Billing address state"
    },
    "billing_postal_code": {
        "type": "string",
        "description": "Billing address postal code"
    },
    "billing_country": {
        "type": "string",
        "description": "Billing address country"
    },
    # Shipping address
    "shipping_street": {
        "type": "string",
        "description": "Shipping address street"
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
        "description": "Shipping address state"
    },
    "shipping_postal_code": {
        "type": "string",
        "description": "Shipping address postal code"
    },
    "shipping_country": {
        "type": "string",
        "description": "Shipping address country"
    }
}

invoice_properties = {
    **invoice_properties_user_define,
    "id": {
        "type": "string",
        "description": "The invoice ID"
    }
}

# MCP Tool definitions
create_invoice_tool = Tool(
    name="quickbooks_create_invoice",
    title="Create Invoice",
    description="Create a new invoice in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": invoice_properties_minimal,
        "required": ["customer_id", "line_items"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE"})
)

get_invoice_tool = Tool(
    name="quickbooks_get_invoice",
    title="Get Invoice",
    description="Get a specific invoice by ID",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The invoice ID"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE", "readOnlyHint": True})
)

list_invoices_tool = Tool(
    name="quickbooks_list_invoices",
    title="List Invoices",
    description="List all invoices with pagination support",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum results to return", "default": 100},
            "start_position": {"type": "integer", "description": "Starting position (1-based)", "default": 1},
        }
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE", "readOnlyHint": True})
)

search_invoices_tool = Tool(
    name="quickbooks_search_invoices",
    title="Search Invoices",
    description="Search invoices with filters for dates, amounts, customer, and addresses",
    inputSchema={
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string", "description": "Search by invoice number"},
            "customer_id": {"type": "string", "description": "Search by customer ID"},
            "customer_name": {"type": "string", "description": "Search by customer name (partial match)"},

            # Date filters
            "date_from": {"type": "string", "description": "Transaction date from (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "Transaction date to (YYYY-MM-DD)"},
            "due_date_from": {"type": "string", "description": "Due date from (YYYY-MM-DD)"},
            "due_date_to": {"type": "string", "description": "Due date to (YYYY-MM-DD)"},

            # Amount filters
            "min_amount": {"type": "number", "description": "Minimum total amount"},
            "max_amount": {"type": "number", "description": "Maximum total amount"},
            "min_balance": {"type": "number", "description": "Minimum balance due"},
            "max_balance": {"type": "number", "description": "Maximum balance due"},

            # Address filters
            "billing_city": {"type": "string", "description": "Filter by billing city"},
            "billing_state": {"type": "string", "description": "Filter by billing state"},
            "shipping_city": {"type": "string", "description": "Filter by shipping city"},
            "shipping_state": {"type": "string", "description": "Filter by shipping state"},

            # Pagination
            "max_results": {"type": "integer", "description": "Maximum results to return", "default": 100},
            "start_position": {"type": "integer", "description": "Starting position (1-based)", "default": 1}
        }
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE", "readOnlyHint": True})
)

update_invoice_tool = Tool(
    name="quickbooks_update_invoice",
    title="Update Invoice",
    description="Update an existing invoice",
    inputSchema={
        "type": "object",
        "properties": invoice_properties,
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE"})
)

delete_invoice_tool = Tool(
    name="quickbooks_delete_invoice",
    title="Delete Invoice",
    description="Permanently delete an invoice (cannot be undone)",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The invoice ID to delete"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE"})
)

send_invoice_tool = Tool(
    name="quickbooks_send_invoice",
    title="Send Invoice",
    description="Send invoice via email to customer",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The invoice ID to send"},
            "send_to": {"type": "string", "description": "Email address (uses invoice's bill_email if not provided)"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE"})
)

void_invoice_tool = Tool(
    name="quickbooks_void_invoice",
    title="Void Invoice",
    description="Void an invoice (zeroes amounts, marks as voided)",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The invoice ID to void"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_INVOICE"})
)


def mcp_object_to_invoice_data(**kwargs) -> Dict[str, Any]:
    """
    Convert simplified MCP object format to QuickBooks invoice data format.
    Maps user-friendly snake_case fields to QuickBooks API structure.
    """
    invoice_data = {}

    # Basic invoice information - map simplified names to QB names
    if 'invoice_number' in kwargs:
        invoice_data['DocNumber'] = kwargs['invoice_number']
    if 'date' in kwargs:
        invoice_data['TxnDate'] = kwargs['date']
    if 'ship_date' in kwargs:
        invoice_data['ShipDate'] = kwargs['ship_date']
    if 'due_date' in kwargs:
        invoice_data['DueDate'] = kwargs['due_date']
    if 'tracking_number' in kwargs:
        invoice_data['TrackingNum'] = kwargs['tracking_number']
    if 'deposit' in kwargs:
        invoice_data['Deposit'] = kwargs['deposit']

    # CustomerMemo needs to be in object format
    if 'customer_memo' in kwargs:
        invoice_data['CustomerMemo'] = {'value': kwargs['customer_memo']}

    # Email addresses - convert to structured objects
    if 'bill_email' in kwargs:
        invoice_data['BillEmail'] = {'Address': kwargs['bill_email']}
    if 'bill_email_cc' in kwargs:
        invoice_data['BillEmailCc'] = {'Address': kwargs['bill_email_cc']}

    # Customer reference
    if 'customer_id' in kwargs:
        invoice_data['CustomerRef'] = {'value': kwargs['customer_id']}

    # Currency reference
    if 'currency' in kwargs:
        invoice_data['CurrencyRef'] = {'value': kwargs['currency']}

    # Ship method reference
    if 'ship_method_id' in kwargs:
        invoice_data['ShipMethodRef'] = {'value': kwargs['ship_method_id']}

    # Line items - handle the line_items parameter
    if 'line_items' in kwargs:
        lines = []
        for item in kwargs['line_items']:
            # Map simplified type to QuickBooks DetailType
            type_mapping = {
                'sales_item': 'SalesItemLineDetail',
                'description_only': 'DescriptionOnlyLine',
                'discount': 'DiscountLineDetail',
                'subtotal': 'SubTotalLineDetail',
            }
            detail_type = type_mapping.get(item.get('type', 'sales_item'), 'SalesItemLineDetail')

            line = {
                "Amount": item["amount"],
                "DetailType": detail_type,
            }

            if item.get("description"):
                line["Description"] = item["description"]
            if item.get("line_id"):
                line["Id"] = item["line_id"]

            if detail_type == "SalesItemLineDetail":
                sales_detail = {}
                if item.get("item_id"):
                    sales_detail["ItemRef"] = {"value": item["item_id"]}
                    if item.get("item_name"):
                        sales_detail["ItemRef"]["name"] = item["item_name"]
                if item.get("quantity"):
                    sales_detail["Qty"] = item["quantity"]
                if item.get("unit_price"):
                    sales_detail["UnitPrice"] = item["unit_price"]
                if item.get("discount_rate"):
                    sales_detail["DiscountRate"] = item["discount_rate"]
                if item.get("discount_amount"):
                    sales_detail["DiscountAmt"] = item["discount_amount"]
                if item.get("service_date"):
                    sales_detail["ServiceDate"] = item["service_date"]
                if item.get("tax_code_id"):
                    sales_detail["TaxCodeRef"] = {"value": item["tax_code_id"]}

                if sales_detail:
                    line["SalesItemLineDetail"] = sales_detail

            elif detail_type == "DiscountLineDetail":
                discount_detail = {}
                if item.get("is_percent") is not None:
                    discount_detail["PercentBased"] = item["is_percent"]
                if item.get("discount_percent"):
                    discount_detail["DiscountPercent"] = item["discount_percent"]
                line["DiscountLineDetail"] = discount_detail

            lines.append(line)
        invoice_data['Line'] = lines

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
        invoice_data['BillAddr'] = billing_addr

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
        invoice_data['ShipAddr'] = shipping_addr

    return invoice_data


def invoice_data_to_mcp_object(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks invoice data format to simplified MCP object format.
    Uses cleaner, more intuitive field names for better usability.
    """
    result = {}

    # Core identification
    if 'Id' in invoice_data:
        result['id'] = invoice_data['Id']
    if 'DocNumber' in invoice_data:
        result['invoice_number'] = invoice_data['DocNumber']

    # Customer info
    if 'CustomerRef' in invoice_data and isinstance(invoice_data['CustomerRef'], dict):
        result['customer_id'] = invoice_data['CustomerRef'].get('value')
        result['customer_name'] = invoice_data['CustomerRef'].get('name')

    # Dates
    if 'TxnDate' in invoice_data:
        result['date'] = invoice_data['TxnDate']
    if 'DueDate' in invoice_data:
        result['due_date'] = invoice_data['DueDate']
    if 'ShipDate' in invoice_data:
        result['ship_date'] = invoice_data['ShipDate']

    # Financial amounts
    if 'TotalAmt' in invoice_data:
        result['total'] = invoice_data['TotalAmt']
    if 'Balance' in invoice_data:
        result['balance_due'] = invoice_data['Balance']
    if 'Deposit' in invoice_data:
        result['deposit'] = invoice_data['Deposit']

    # Status
    if 'EmailStatus' in invoice_data:
        result['email_status'] = invoice_data['EmailStatus']
    if 'PrintStatus' in invoice_data:
        result['print_status'] = invoice_data['PrintStatus']

    # Notes/memos
    if 'CustomerMemo' in invoice_data:
        memo = invoice_data['CustomerMemo']
        result['customer_memo'] = memo.get('value') if isinstance(memo, dict) else memo
    if 'PrivateNote' in invoice_data:
        result['private_note'] = invoice_data['PrivateNote']

    # Shipping info
    if 'TrackingNum' in invoice_data:
        result['tracking_number'] = invoice_data['TrackingNum']
    if 'ShipMethodRef' in invoice_data and isinstance(invoice_data['ShipMethodRef'], dict):
        result['ship_method'] = invoice_data['ShipMethodRef'].get('name') or invoice_data['ShipMethodRef'].get('value')

    # Currency
    if 'CurrencyRef' in invoice_data and isinstance(invoice_data['CurrencyRef'], dict):
        result['currency'] = invoice_data['CurrencyRef'].get('value')
    if 'ExchangeRate' in invoice_data:
        result['exchange_rate'] = invoice_data['ExchangeRate']

    # Link
    if 'InvoiceLink' in invoice_data:
        result['link'] = invoice_data['InvoiceLink']

    # Billing address (simplified)
    if 'BillAddr' in invoice_data and isinstance(invoice_data['BillAddr'], dict):
        addr = invoice_data['BillAddr']
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

    # Shipping address (simplified)
    if 'ShipAddr' in invoice_data and isinstance(invoice_data['ShipAddr'], dict):
        addr = invoice_data['ShipAddr']
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

    # Line items (simplified structure)
    if 'Line' in invoice_data and isinstance(invoice_data['Line'], list):
        items = []
        for line in invoice_data['Line']:
            if isinstance(line, dict) and 'Amount' in line:
                detail_type = line.get('DetailType', 'SalesItemLineDetail')
                
                # Skip SubTotalLine as it's just a computed summary
                if detail_type == 'SubTotalLine':
                    continue

                item = {
                    'amount': line['Amount'],
                    'type': detail_type.replace('LineDetail', '').replace('Line', '').lower()
                }

                if line.get('Description'):
                    item['description'] = line['Description']

                # Handle SalesItemLineDetail
                if detail_type == 'SalesItemLineDetail' and 'SalesItemLineDetail' in line:
                    detail = line['SalesItemLineDetail']
                    if 'ItemRef' in detail:
                        item['item_id'] = detail['ItemRef'].get('value')
                        item['item_name'] = detail['ItemRef'].get('name')
                    if 'Qty' in detail:
                        item['quantity'] = detail['Qty']
                    if 'UnitPrice' in detail:
                        item['unit_price'] = detail['UnitPrice']
                    if 'ServiceDate' in detail:
                        item['service_date'] = detail['ServiceDate']

                # Handle DiscountLineDetail
                elif detail_type == 'DiscountLineDetail' and 'DiscountLineDetail' in line:
                    detail = line['DiscountLineDetail']
                    if 'DiscountPercent' in detail:
                        item['discount_percent'] = detail['DiscountPercent']
                    if 'PercentBased' in detail:
                        item['is_percent'] = detail['PercentBased']

                items.append(item)

        if items:
            result['line_items'] = items

    # Timestamps
    if 'MetaData' in invoice_data and isinstance(invoice_data['MetaData'], dict):
        metadata = invoice_data['MetaData']
        if 'CreateTime' in metadata:
            result['created_at'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            result['updated_at'] = metadata['LastUpdatedTime']

    return result


class InvoiceManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_invoice(self, **kwargs) -> Dict[str, Any]:
        """Create a new invoice."""
        invoice_data = mcp_object_to_invoice_data(**kwargs)
        response = await self.client._post('invoice', invoice_data)
        return invoice_data_to_mcp_object(response['Invoice'])

    async def get_invoice(self, id: str) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        response = await self.client._get(f"invoice/{id}")
        return invoice_data_to_mcp_object(response['Invoice'])

    async def list_invoices(self, max_results: int = 100, start_position: int = 1) -> List[Dict[str, Any]]:
        """List all invoices with pagination support."""
        query = f"select * from Invoice STARTPOSITION {start_position} MAXRESULTS {max_results}"
        response = await self.client._get('query', params={'query': query})

        # Handle case when no invoices are returned
        if 'Invoice' not in response['QueryResponse']:
            return []

        invoices = response['QueryResponse']['Invoice']
        return [invoice_data_to_mcp_object(invoice) for invoice in invoices]

    async def search_invoices(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search invoices with various filters and pagination support.

        Args:
            invoice_number: Search by invoice number
            customer_id: Search by customer ID
            customer_name: Search by customer name (partial match)
            date_from/date_to: Search by transaction date range
            due_date_from/due_date_to: Search by due date range
            min_amount/max_amount: Search by total amount range
            min_balance/max_balance: Search by balance range
            billing_city/billing_state: Filter by billing address
            shipping_city/shipping_state: Filter by shipping address
            max_results: Maximum results (default: 100)
            start_position: Starting position (default: 1)

        Returns:
            List of invoices matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters
        if kwargs.get('invoice_number'):
            conditions.append(f"DocNumber = '{kwargs['invoice_number']}'")

        if kwargs.get('customer_id'):
            conditions.append(f"CustomerRef = '{kwargs['customer_id']}'")

        if kwargs.get('customer_name'):
            customer_name = kwargs['customer_name'].replace("'", "''")
            conditions.append(
                f"CustomerRef IN (SELECT Id FROM Customer WHERE Name LIKE '%{customer_name}%')")

        # Date range filters
        if kwargs.get('date_from'):
            conditions.append(f"TxnDate >= '{kwargs['date_from']}'")
        if kwargs.get('date_to'):
            conditions.append(f"TxnDate <= '{kwargs['date_to']}'")

        if kwargs.get('due_date_from'):
            conditions.append(f"DueDate >= '{kwargs['due_date_from']}'")
        if kwargs.get('due_date_to'):
            conditions.append(f"DueDate <= '{kwargs['due_date_to']}'")

        # Amount range filters
        if kwargs.get('min_amount') is not None:
            conditions.append(f"TotalAmt >= {kwargs['min_amount']}")
        if kwargs.get('max_amount') is not None:
            conditions.append(f"TotalAmt <= {kwargs['max_amount']}")

        if kwargs.get('min_balance') is not None:
            conditions.append(f"Balance >= {kwargs['min_balance']}")
        if kwargs.get('max_balance') is not None:
            conditions.append(f"Balance <= {kwargs['max_balance']}")

        # Address filters
        address_field_mappings = {
            'billing_city': 'BillAddr.City',
            'billing_state': 'BillAddr.CountrySubDivisionCode',
            'shipping_city': 'ShipAddr.City',
            'shipping_state': 'ShipAddr.CountrySubDivisionCode',
        }

        for simple_name, qb_field in address_field_mappings.items():
            if kwargs.get(simple_name):
                conditions.append(f"{qb_field} = '{kwargs[simple_name]}'")

        # Build the complete query
        base_query = "SELECT * FROM Invoice"

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        # Add pagination
        start_position = kwargs.get('start_position', 1)
        max_results = kwargs.get('max_results', 100)

        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no invoices are returned
        if 'Invoice' not in response['QueryResponse']:
            return []

        invoices = response['QueryResponse']['Invoice']
        return [invoice_data_to_mcp_object(invoice) for invoice in invoices]

    async def update_invoice(self, **kwargs) -> Dict[str, Any]:
        """Update an existing invoice."""
        invoice_id = kwargs.get('id')
        if not invoice_id:
            raise ValueError("id is required for updating an invoice")

        # Auto-fetch current sync token
        current_invoice_response = await self.client._get(f"invoice/{invoice_id}")
        sync_token = current_invoice_response.get(
            'Invoice', {}).get('SyncToken', '0')

        invoice_data = mcp_object_to_invoice_data(**kwargs)
        invoice_data.update({
            "Id": invoice_id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('invoice', invoice_data)
        return invoice_data_to_mcp_object(response['Invoice'])

    async def delete_invoice(self, id: str) -> Dict[str, Any]:
        """Delete an invoice."""
        # Auto-fetch current sync token
        current_invoice_response = await self.client._get(f"invoice/{id}")
        current_invoice = current_invoice_response.get('Invoice', {})

        if not current_invoice:
            raise ValueError(f"Invoice with ID {id} not found")

        sync_token = current_invoice.get('SyncToken', '0')

        delete_data = {
            "Id": id,
            "SyncToken": sync_token,
        }
        return await self.client._post("invoice", delete_data, params={'operation': 'delete'})

    async def send_invoice(self, id: str, send_to: str = None) -> Dict[str, Any]:
        """
        Send an invoice via email.

        Args:
            id: The invoice ID to send
            send_to: Optional email address (uses invoice's bill_email if not provided)

        Returns:
            The invoice with updated email status and delivery info.
        """
        endpoint = f"invoice/{id}/send"
        params = {}
        if send_to:
            params['sendTo'] = send_to

        response = await self.client._make_request('POST', endpoint, params=params)

        if 'Invoice' in response:
            return invoice_data_to_mcp_object(response['Invoice'])

        return response

    async def void_invoice(self, id: str) -> Dict[str, Any]:
        """
        Void an existing invoice. Amounts are zeroed and "Voided" is added to notes.

        Args:
            id: The invoice ID to void

        Returns:
            The voided invoice.
        """
        current_invoice_response = await self.client._get(f"invoice/{id}")
        current_invoice = current_invoice_response.get('Invoice', {})

        if not current_invoice:
            raise ValueError(f"Invoice with ID {id} not found")

        sync_token = current_invoice.get('SyncToken', '0')

        void_data = {
            "Id": id,
            "SyncToken": sync_token,
        }

        response = await self.client._post("invoice", void_data, params={'operation': 'void'})

        if 'Invoice' in response:
            return invoice_data_to_mcp_object(response['Invoice'])

        return response


# Export tools
tools = [create_invoice_tool, get_invoice_tool, list_invoices_tool, search_invoices_tool,
         update_invoice_tool, delete_invoice_tool, send_invoice_tool, void_invoice_tool]
