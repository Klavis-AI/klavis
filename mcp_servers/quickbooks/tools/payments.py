from typing import Any, Dict, List

from mcp.types import Tool
import mcp.types as types
from .http_client import QuickBooksHTTPClient

# Minimal properties for payment creation (required by QuickBooks)
payment_properties_minimal = {
    "amount": {
        "type": "number",
        "description": "Total payment amount"
    },
    "customer_id": {
        "type": "string",
        "description": "Customer ID for the payment"
    }
}

# Payment properties mapping
payment_properties_user_define = {
    **payment_properties_minimal,
    "date": {
        "type": "string",
        "description": "Payment date (YYYY-MM-DD)"
    },
    "reference_number": {
        "type": "string",
        "description": "Reference number (e.g., check number)"
    },
    "payment_method_id": {
        "type": "string",
        "description": "Payment method ID"
    },
    "deposit_account_id": {
        "type": "string",
        "description": "Account ID to deposit funds (defaults to Undeposited Funds)"
    },
    "currency": {
        "type": "string",
        "description": "Currency code (e.g., USD, EUR)"
    },
    "exchange_rate": {
        "type": "number",
        "description": "Exchange rate for multicurrency"
    },
    "private_note": {
        "type": "string",
        "description": "Private note for internal use"
    }
}

payment_properties = {
    **payment_properties_user_define,
    "id": {
        "type": "string",
        "description": "Payment ID"
    }
}

# MCP Tool definitions
create_payment_tool = Tool(
    name="quickbooks_create_payment",
    title="Create Payment",
    description="Create a new payment in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": payment_properties_minimal,
        "required": ["amount", "customer_id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT"})
)

get_payment_tool = Tool(
    name="quickbooks_get_payment",
    title="Get Payment",
    description="Get a payment by ID",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Payment ID"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT", "readOnlyHint": True})
)

list_payments_tool = Tool(
    name="quickbooks_list_payments",
    title="List Payments",
    description="List all payments with pagination",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum results (default: 100)"},
            "start_position": {"type": "integer", "description": "Starting position (default: 1)"}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT", "readOnlyHint": True})
)

search_payments_tool = Tool(
    name="quickbooks_search_payments",
    title="Search Payments",
    description="Search payments with filters",
    inputSchema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Filter by customer ID"},
            "customer_name": {"type": "string", "description": "Filter by customer name (partial match)"},
            "reference_number": {"type": "string", "description": "Filter by reference number"},
            "date_from": {"type": "string", "description": "From date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "To date (YYYY-MM-DD)"},
            "min_amount": {"type": "number", "description": "Minimum amount"},
            "max_amount": {"type": "number", "description": "Maximum amount"},
            "min_unapplied": {"type": "number", "description": "Minimum unapplied amount"},
            "max_unapplied": {"type": "number", "description": "Maximum unapplied amount"},
            "payment_method_id": {"type": "string", "description": "Filter by payment method ID"},
            "deposit_account_id": {"type": "string", "description": "Filter by deposit account ID"},
            "max_results": {"type": "integer", "description": "Maximum results (default: 100)"},
            "start_position": {"type": "integer", "description": "Starting position (default: 1)"}
        },
        "required": []
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT", "readOnlyHint": True})
)

update_payment_tool = Tool(
    name="quickbooks_update_payment",
    title="Update Payment",
    description="Update an existing payment",
    inputSchema={
        "type": "object",
        "properties": payment_properties,
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT"})
)

delete_payment_tool = Tool(
    name="quickbooks_delete_payment",
    title="Delete Payment",
    description="Delete a payment",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Payment ID to delete"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT"})
)

send_payment_tool = Tool(
    name="quickbooks_send_payment",
    title="Send Payment",
    description="Send payment receipt via email",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Payment ID to send"},
            "send_to": {"type": "string", "description": "Email address to send receipt to"}
        },
        "required": ["id", "send_to"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT"})
)

void_payment_tool = Tool(
    name="quickbooks_void_payment",
    title="Void Payment",
    description="Void a payment (zeroes amounts, keeps record for audit)",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Payment ID to void"}
        },
        "required": ["id"]
    },
    annotations=types.ToolAnnotations(**{"category": "QUICKBOOKS_PAYMENT"})
)


def mcp_object_to_payment_data(**kwargs) -> Dict[str, Any]:
    """
    Convert simplified MCP input format to QuickBooks payment data format.
    """
    payment_data = {}

    # Field mappings: simplified name -> QB field name
    direct_mappings = {
        'amount': 'TotalAmt',
        'reference_number': 'PaymentRefNum',
        'exchange_rate': 'ExchangeRate',
        'date': 'TxnDate',
        'private_note': 'PrivateNote',
    }

    for simple_name, qb_name in direct_mappings.items():
        if simple_name in kwargs and kwargs[simple_name] is not None:
            payment_data[qb_name] = kwargs[simple_name]

    # Reference fields: simplified -> QB ref object
    if kwargs.get('customer_id'):
        payment_data['CustomerRef'] = {'value': kwargs['customer_id']}

    if kwargs.get('payment_method_id'):
        payment_data['PaymentMethodRef'] = {'value': kwargs['payment_method_id']}

    if kwargs.get('deposit_account_id'):
        payment_data['DepositToAccountRef'] = {'value': kwargs['deposit_account_id']}

    if kwargs.get('currency'):
        payment_data['CurrencyRef'] = {'value': kwargs['currency']}

    return payment_data


def payment_data_to_mcp_object(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks payment data format to simplified MCP object format.
    Uses cleaner, more intuitive field names for better usability.
    """
    result = {}

    # Core identification
    if 'Id' in payment_data:
        result['id'] = payment_data['Id']
    if 'PaymentRefNum' in payment_data:
        result['reference_number'] = payment_data['PaymentRefNum']

    # Customer info
    if 'CustomerRef' in payment_data and isinstance(payment_data['CustomerRef'], dict):
        result['customer_id'] = payment_data['CustomerRef'].get('value')
        result['customer_name'] = payment_data['CustomerRef'].get('name')

    # Date
    if 'TxnDate' in payment_data:
        result['date'] = payment_data['TxnDate']

    # Amounts
    if 'TotalAmt' in payment_data:
        result['amount'] = payment_data['TotalAmt']
    if 'UnappliedAmt' in payment_data:
        result['unapplied_amount'] = payment_data['UnappliedAmt']

    # Payment method
    if 'PaymentMethodRef' in payment_data and isinstance(payment_data['PaymentMethodRef'], dict):
        result['payment_method'] = payment_data['PaymentMethodRef'].get('name') or payment_data['PaymentMethodRef'].get('value')

    # Deposit account
    if 'DepositToAccountRef' in payment_data and isinstance(payment_data['DepositToAccountRef'], dict):
        result['deposit_account'] = payment_data['DepositToAccountRef'].get('name') or payment_data['DepositToAccountRef'].get('value')

    # Currency
    if 'CurrencyRef' in payment_data and isinstance(payment_data['CurrencyRef'], dict):
        result['currency'] = payment_data['CurrencyRef'].get('value')
    if 'ExchangeRate' in payment_data:
        result['exchange_rate'] = payment_data['ExchangeRate']

    # Notes
    if 'PrivateNote' in payment_data:
        result['private_note'] = payment_data['PrivateNote']

    # Linked transactions (invoices/credit memos this payment applies to)
    if 'Line' in payment_data and isinstance(payment_data['Line'], list):
        applied_to = []
        for line in payment_data['Line']:
            if isinstance(line, dict) and 'LinkedTxn' in line:
                for linked in line.get('LinkedTxn', []):
                    if isinstance(linked, dict):
                        txn = {
                            'amount': line.get('Amount'),
                            'transaction_id': linked.get('TxnId'),
                            'transaction_type': linked.get('TxnType')
                        }
                        applied_to.append(txn)
        if applied_to:
            result['applied_to'] = applied_to

    # Credit card info (simplified - only include essential fields)
    if 'CreditCardPayment' in payment_data and isinstance(payment_data['CreditCardPayment'], dict):
        cc_payment = payment_data['CreditCardPayment']
        cc_info = {}
        
        if 'CreditChargeInfo' in cc_payment and isinstance(cc_payment['CreditChargeInfo'], dict):
            info = cc_payment['CreditChargeInfo']
            if 'Type' in info:
                cc_info['card_type'] = info['Type']
            if 'NameOnAcct' in info:
                cc_info['cardholder_name'] = info['NameOnAcct']
        
        if 'CreditChargeResponse' in cc_payment and isinstance(cc_payment['CreditChargeResponse'], dict):
            response = cc_payment['CreditChargeResponse']
            if 'Status' in response:
                cc_info['status'] = response['Status']
            if 'AuthCode' in response:
                cc_info['auth_code'] = response['AuthCode']
            if 'CCTransId' in response:
                cc_info['transaction_id'] = response['CCTransId']
        
        if cc_info:
            result['credit_card'] = cc_info

    # Timestamps
    if 'MetaData' in payment_data and isinstance(payment_data['MetaData'], dict):
        metadata = payment_data['MetaData']
        if 'CreateTime' in metadata:
            result['created_at'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            result['updated_at'] = metadata['LastUpdatedTime']

    return result


class PaymentManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_payment(self, **kwargs) -> Dict[str, Any]:
        """Create a new payment."""
        payment_data = mcp_object_to_payment_data(**kwargs)
        response = await self.client._post('payment', payment_data)
        return payment_data_to_mcp_object(response['Payment'])

    async def get_payment(self, id: str) -> Dict[str, Any]:
        """Get a payment by ID."""
        response = await self.client._get(f"payment/{id}")
        return payment_data_to_mcp_object(response['Payment'])

    async def list_payments(self, max_results: int = 100, start_position: int = 1) -> List[Dict[str, Any]]:
        """List all payments with pagination."""
        query = f"select * from Payment STARTPOSITION {start_position} MAXRESULTS {max_results}"
        response = await self.client._get('query', params={'query': query})

        if 'Payment' not in response['QueryResponse']:
            return []

        payments = response['QueryResponse']['Payment']
        return [payment_data_to_mcp_object(payment) for payment in payments]

    async def search_payments(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search payments with filters.

        Args:
            customer_id: Filter by customer ID
            customer_name: Filter by customer name (partial match)
            reference_number: Filter by reference number
            date_from/date_to: Date range filter
            min_amount/max_amount: Amount range filter
            min_unapplied/max_unapplied: Unapplied amount range
            payment_method_id: Filter by payment method
            deposit_account_id: Filter by deposit account
            max_results/start_position: Pagination
        """
        conditions = []

        if kwargs.get('customer_id'):
            conditions.append(f"CustomerRef = '{kwargs['customer_id']}'")

        if kwargs.get('reference_number'):
            conditions.append(f"PaymentRefNum = '{kwargs['reference_number']}'")

        if kwargs.get('customer_name'):
            customer_name = kwargs['customer_name'].replace("'", "''")
            conditions.append(
                f"CustomerRef IN (SELECT Id FROM Customer WHERE Name LIKE '%{customer_name}%')")

        if kwargs.get('date_from'):
            conditions.append(f"TxnDate >= '{kwargs['date_from']}'")
        if kwargs.get('date_to'):
            conditions.append(f"TxnDate <= '{kwargs['date_to']}'")

        if kwargs.get('min_amount') is not None:
            conditions.append(f"TotalAmt >= {kwargs['min_amount']}")
        if kwargs.get('max_amount') is not None:
            conditions.append(f"TotalAmt <= {kwargs['max_amount']}")

        if kwargs.get('min_unapplied') is not None:
            conditions.append(f"UnappliedAmt >= {kwargs['min_unapplied']}")
        if kwargs.get('max_unapplied') is not None:
            conditions.append(f"UnappliedAmt <= {kwargs['max_unapplied']}")

        if kwargs.get('payment_method_id'):
            conditions.append(f"PaymentMethodRef = '{kwargs['payment_method_id']}'")
        if kwargs.get('deposit_account_id'):
            conditions.append(f"DepositToAccountRef = '{kwargs['deposit_account_id']}'")

        base_query = "SELECT * FROM Payment"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        start_position = kwargs.get('start_position', 1)
        max_results = kwargs.get('max_results', 100)
        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        if 'Payment' not in response['QueryResponse']:
            return []

        payments = response['QueryResponse']['Payment']
        return [payment_data_to_mcp_object(payment) for payment in payments]

    async def update_payment(self, **kwargs) -> Dict[str, Any]:
        """Update an existing payment."""
        payment_id = kwargs.get('id')
        if not payment_id:
            raise ValueError("id is required for updating a payment")

        current_payment_response = await self.client._get(f"payment/{payment_id}")
        sync_token = current_payment_response.get('Payment', {}).get('SyncToken', '0')

        payment_data = mcp_object_to_payment_data(**kwargs)
        payment_data.update({
            "Id": payment_id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('payment', payment_data)
        return payment_data_to_mcp_object(response['Payment'])

    async def delete_payment(self, id: str) -> Dict[str, Any]:
        """Delete a payment."""
        current_payment_response = await self.client._get(f"payment/{id}")
        current_payment = current_payment_response.get('Payment', {})

        if not current_payment:
            raise ValueError(f"Payment with ID {id} not found")

        sync_token = current_payment.get('SyncToken', '0')
        delete_data = {
            "Id": id,
            "SyncToken": sync_token,
        }
        return await self.client._post("payment", delete_data, params={'operation': 'delete'})

    async def send_payment(self, id: str, send_to: str) -> Dict[str, Any]:
        """Send a payment receipt via email."""
        endpoint = f"payment/{id}/send"
        params = {'sendTo': send_to}
        response = await self.client._make_request('POST', endpoint, params=params)

        if 'Payment' in response:
            return payment_data_to_mcp_object(response['Payment'])
        return response

    async def void_payment(self, id: str) -> Dict[str, Any]:
        """Void a payment (zeroes amounts, keeps record for audit)."""
        current_payment_response = await self.client._get(f"payment/{id}")
        current_payment = current_payment_response.get('Payment', {})

        if not current_payment:
            raise ValueError(f"Payment with ID {id} not found")

        sync_token = current_payment.get('SyncToken', '0')
        void_data = {
            "Id": id,
            "SyncToken": sync_token,
            "sparse": True,
        }

        response = await self.client._post("payment", void_data, params={'operation': 'void'})

        if 'Payment' in response:
            return payment_data_to_mcp_object(response['Payment'])
        return response


# Export tools
tools = [create_payment_tool, get_payment_tool, list_payments_tool, search_payments_tool,
         update_payment_tool, delete_payment_tool, send_payment_tool, void_payment_tool]
