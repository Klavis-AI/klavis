from typing import Any, Dict, List

from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

# Minimal properties for payment creation (required by QuickBooks)
payment_properties_minimal = {
    "TotalAmt": {
        "type": "number",
        "description": "Indicates the total amount of the transaction. This includes the total of all the charges, allowances, and taxes."
    },
    "CustomerRefValue": {
        "type": "string",
        "description": "Customer ID for the payment"
    },
    "CustomerRefName": {
        "type": "string",
        "description": "Name of the customer associated with the payment"
    }
}

# Payment properties mapping (based on QuickBooks API documentation)
payment_properties_user_define = {
    **payment_properties_minimal,
    "TransactionDate": {
        "type": "string",
        "description": "The date entered by the user when this transaction occurred. For posting transactions, this is the posting date that affects the financial statements. If the date is not supplied, the current date on the server is used. Format: yyyy/MM/dd"
    },
    "PaymentRefNum": {
        "type": "string",
        "description": "The reference number for the payment received. For example, Check # for a check, envelope # for a cash donation. Required for France locales."
    },
    "PaymentMethodRefValue": {
        "type": "string",
        "description": "Reference to a PaymentMethod associated with this transaction"
    },
    "PaymentMethodRefName": {
        "type": "string",
        "description": "Name of the PaymentMethod associated with this transaction"
    },
    "DepositToAccountRefValue": {
        "type": "string",
        "description": "Account to which money is deposited. If you do not specify this account, payment is applied to the Undeposited Funds account."
    },
    "DepositToAccountRefName": {
        "type": "string",
        "description": "Name of the account to which money is deposited"
    },
    "CurrencyRefValue": {
        "type": "string",
        "description": "A three letter string representing the ISO 4217 code for the currency. For example, USD, AUD, EUR, and so on."
    },
    "CurrencyRefName": {
        "type": "string",
        "description": "The full name of the currency"
    },
    "ExchangeRate": {
        "type": "number",
        "description": "The number of home currency units it takes to equal one unit of currency specified by CurrencyRef. Applicable if multicurrency is enabled for the company"
    },
    # Credit Card Payment fields
    "CreditCardPayment": {
        "type": "object",
        "properties": {
            "CreditChargeInfo": {
                "type": "object",
                "properties": {
                    "CcExpiryMonth": {
                        "type": "integer",
                        "description": "Expiration Month on card, expressed as a number: 1=January, 2=February, etc."
                    },
                    "CcExpiryYear": {
                        "type": "integer",
                        "description": "Expiration Year on card, expressed as a 4 digit number 1999, 2003, etc."
                    },
                    "ProcessPayment": {
                        "type": "boolean",
                        "description": "false or no value-Store credit card information only. true-Store credit card payment transaction information in CreditChargeResponse"
                    },
                    "PostalCode": {
                        "type": "string",
                        "description": "Credit card holder billing postal code. Five digits in the USA. Max 30 characters"
                    },
                    "Amount": {
                        "type": "number",
                        "description": "The amount processed using the credit card"
                    },
                    "NameOnAcct": {
                        "type": "string",
                        "description": "Account holder name, as printed on the card"
                    },
                    "Type": {
                        "type": "string",
                        "description": "Type of credit card. For example, MasterCard, Visa, Discover, American Express, and so on"
                    },
                    "BillAddrStreet": {
                        "type": "string",
                        "description": "Credit card holder billing address of record: the street address to which credit card statements are sent. Max 255 characters"
                    }
                }
            }
        },
        "description": "Information about a payment received by credit card. Inject with data only if the payment was transacted through Intuit Payments API"
    }
}

# Wont send to AI, but AI actually uses this
# Leave it here for human understanding
payment_properties = {
    **payment_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique QuickBooks payment ID"
    },
    "SyncToken": {
        "type": "string",
        "description": "Version number of the object for concurrent updates"
    }
}

# MCP Tool definitions
create_payment_tool = Tool(
    name="create_payment",
    title="Create Payment",
    description="Create New Payment - Create a new payment in QuickBooks. Requires TotalAmt and CustomerRef. Can be applied to specific invoices/credit memos or created as unapplied credit.",
    inputSchema={
        "type": "object",
        "properties": payment_properties_minimal,
        "required": ["TotalAmt", "CustomerRefValue"]
    }
)

get_payment_tool = Tool(
    name="get_payment",
    title="Get Payment",
    description="Get Single Payment - Retrieve a specific payment by ID from QuickBooks with all its details including line items, amounts, and linked transactions",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks payment ID"}
        },
        "required": ["Id"]
    }
)

list_payments_tool = Tool(
    name="list_payments",
    title="List Payments",
    description="List All Payments - Retrieve all payments from QuickBooks with pagination support. Use for browsing or getting overview of payments",
    inputSchema={
        "type": "object",
        "properties": {
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1},
        },
        "required": [],
    }
)

search_payments_tool = Tool(
    name="search_payments",
    title="Search Payments",
    description="Advanced Payment Search - Search payments with powerful filters including dates, amounts, customer info, and status. Perfect for finding specific payments based on criteria",
    inputSchema={
        "type": "object",
        "properties": {
            "CustomerRefValue": {"type": "string", "description": "Search by customer ID"},
            "CustomerName": {"type": "string", "description": "Search by customer name (partial match)"},
            "PaymentRefNum": {"type": "string", "description": "Search by payment reference number"},

            # Date filters
            "TransactionDateFrom": {"type": "string", "description": "Search payments from this transaction date (YYYY-MM-DD format)"},
            "TransactionDateTo": {"type": "string", "description": "Search payments to this transaction date (YYYY-MM-DD format)"},

            # Amount filters
            "MinAmount": {"type": "number", "description": "Minimum total amount"},
            "MaxAmount": {"type": "number", "description": "Maximum total amount"},
            "MinUnappliedAmt": {"type": "number", "description": "Minimum unapplied amount"},
            "MaxUnappliedAmt": {"type": "number", "description": "Maximum unapplied amount"},

            # Reference filters
            "PaymentMethodRefValue": {"type": "string", "description": "Search by payment method ID"},
            "DepositToAccountRefValue": {"type": "string", "description": "Search by deposit account ID"},

            # Pagination
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": [],
    }
)

update_payment_tool = Tool(
    name="update_payment",
    title="Update Payment",
    description="Update Existing Payment - Modify an existing payment in QuickBooks. Automatically handles sync tokens for safe concurrent updates",
    inputSchema={
        "type": "object",
        "properties": {**payment_properties_user_define, "Id": {"type": "string", "description": "The QuickBooks payment ID to update"}},
        "required": ["Id"]
    }
)

delete_payment_tool = Tool(
    name="delete_payment",
    title="Delete Payment",
    description="️Delete Payment - Permanently delete a payment from QuickBooks. Use with caution as this action cannot be undone",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks payment ID to delete"}
        },
        "required": ["Id"]
    }
)

send_payment_tool = Tool(
    name="send_payment",
    title="Send Payment",
    description="Send Payment via Email - Send a payment receipt to customer via email",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {
                "type": "string",
                "description": "The QuickBooks payment ID to send"
            },
            "SendTo": {
                "type": "string",
                "description": "Email address to send the payment receipt to",
            }
        },
        "required": ["Id", "SendTo"]
    }
)

void_payment_tool = Tool(
    name="void_payment",
    title="Void Payment",
    description="Void Payment - Void an existing payment in QuickBooks. Sets all amounts to zero and marks as 'Voided' while keeping the record for audit trail. If funds have been deposited, you must delete the associated deposit object before voiding the payment.",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {
                "type": "string",
                "description": "The QuickBooks payment ID to void"
            }
        },
        "required": ["Id"]
    }
)


def mcp_object_to_payment_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks payment data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    payment_data = {}

    # Basic payment information - direct copy
    for field in ['TotalAmt', 'PaymentRefNum', 'ExchangeRate']:
        if field in kwargs:
            payment_data[field] = kwargs[field]

    # Handle renamed field: TransactionDate -> TxnDate
    if 'TransactionDate' in kwargs:
        payment_data['TxnDate'] = kwargs['TransactionDate']

    # Reference objects - convert separate value/name fields to structured objects
    ref_mappings = [
        ('CustomerRef', 'CustomerRefValue', 'CustomerRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('PaymentMethodRef', 'PaymentMethodRefValue', 'PaymentMethodRefName'),
        ('DepositToAccountRef', 'DepositToAccountRefValue', 'DepositToAccountRefName'),
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if value_field in kwargs:
            ref_obj = {'value': kwargs[value_field]}
            if name_field in kwargs:
                ref_obj['name'] = kwargs[name_field]
            payment_data[ref_name] = ref_obj

    # Credit Card Payment information
    if 'CreditCardPayment' in kwargs:
        cc_payment = kwargs['CreditCardPayment']
        if isinstance(cc_payment, dict):
            payment_data['CreditCardPayment'] = cc_payment

    return payment_data


def payment_data_to_mcp_object(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks payment data format to MCP object format.
    This function flattens the nested QuickBooks structure to the flat format expected by MCP tools.
    """
    mcp_object = {}

    # Copy basic fields if present
    for field in [
        'Id', 'TotalAmt', 'PaymentRefNum',
        'ExchangeRate', 'UnappliedAmt'
    ]:
        if field in payment_data:
            mcp_object[field] = payment_data[field]

    # Handle fields that are output-only (not in input schema but preserved in output)
    for field in ['PrivateNote', 'TransactionLocationType']:
        if field in payment_data:
            mcp_object[field] = payment_data[field]

    # Handle renamed field: TxnDate -> TransactionDate
    if 'TxnDate' in payment_data:
        mcp_object['TransactionDate'] = payment_data['TxnDate']

    # Reference objects - flatten to separate value and name fields
    ref_mappings = [
        ('CustomerRef', 'CustomerRefValue', 'CustomerRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('PaymentMethodRef', 'PaymentMethodRefValue', 'PaymentMethodRefName'),
        ('DepositToAccountRef', 'DepositToAccountRefValue', 'DepositToAccountRefName'),
        ('ProjectRef', 'ProjectRefValue', 'ProjectRefName'),
        ('TaxExemptionRef', 'TaxExemptionRefValue', 'TaxExemptionRefName'),
        ('SyncToken', 'SyncToken', None)
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if ref_name in payment_data:
            ref = payment_data[ref_name]
            if isinstance(ref, dict):
                if 'value' in ref:
                    mcp_object[value_field] = ref['value']
                if name_field and 'name' in ref:
                    mcp_object[name_field] = ref['name']
            else:
                # Handle cases where SyncToken might be directly in payment_data
                mcp_object[value_field] = ref

    # Line items - flatten to Line array
    if 'Line' in payment_data and isinstance(payment_data['Line'], list):
        lines = []
        for line in payment_data['Line']:
            if isinstance(line, dict):
                line_item = {}
                if 'Amount' in line:
                    line_item['Amount'] = line['Amount']

                if 'LinkedTxn' in line and isinstance(line['LinkedTxn'], list):
                    linked_txns = []
                    for linked_txn in line['LinkedTxn']:
                        if isinstance(linked_txn, dict):
                            txn = {}
                            if 'TxnId' in linked_txn:
                                txn['TxnId'] = linked_txn['TxnId']
                            if 'TxnType' in linked_txn:
                                txn['TxnType'] = linked_txn['TxnType']
                            if 'TxnLineId' in linked_txn:
                                txn['TxnLineId'] = linked_txn['TxnLineId']
                            linked_txns.append(txn)
                    line_item['LinkedTxn'] = linked_txns

                lines.append(line_item)
        mcp_object['Line'] = lines

    # Credit Card Payment information
    if 'CreditCardPayment' in payment_data:
        mcp_object['CreditCardPayment'] = payment_data['CreditCardPayment']

    # MetaData fields
    if 'MetaData' in payment_data and isinstance(payment_data['MetaData'], dict):
        metadata = payment_data['MetaData']
        if 'CreateTime' in metadata:
            mcp_object['MetaDataCreateTime'] = metadata['CreateTime']
        if 'LastUpdatedTime' in metadata:
            mcp_object['MetaDataLastUpdatedTime'] = metadata['LastUpdatedTime']

    return mcp_object


class PaymentManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_payment(self, **kwargs) -> Dict[str, Any]:
        """Create a new payment with comprehensive property support."""
        payment_data = mcp_object_to_payment_data(**kwargs)

        # Ensure CustomerRef is included
        if 'CustomerRef' not in payment_data and 'CustomerRefValue' in kwargs:
            payment_data['CustomerRef'] = {'value': kwargs['CustomerRefValue']}
            if 'CustomerRefName' in kwargs:
                payment_data['CustomerRef']['name'] = kwargs['CustomerRefName']

        response = await self.client._post('payment', payment_data)
        return payment_data_to_mcp_object(response['Payment'])

    async def get_payment(self, Id: str) -> Dict[str, Any]:
        """Get a specific payment by ID."""
        response = await self.client._get(f"payment/{Id}")
        return payment_data_to_mcp_object(response['Payment'])

    async def list_payments(self, MaxResults: int = 100, StartPosition: int = 1) -> List[Dict[str, Any]]:
        """List all payments with comprehensive properties and pagination support."""
        query = f"select * from Payment STARTPOSITION {StartPosition} MAXRESULTS {MaxResults}"
        response = await self.client._get('query', params={'query': query})

        # Handle case when no payments are returned
        if 'Payment' not in response['QueryResponse']:
            return []

        payments = response['QueryResponse']['Payment']
        return [payment_data_to_mcp_object(payment) for payment in payments]

    async def search_payments(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Search payments with various filters and pagination support.

        Args:
            CustomerRefValue: Search by customer ID
            CustomerName: Search by customer name (partial match)
            PaymentRefNum: Search by payment reference number

            # Date filters
            TransactionDateFrom/TransactionDateTo: Search by transaction date range

            # Amount filters
            MinAmount/MaxAmount: Search by total amount range
            MinUnappliedAmt/MaxUnappliedAmt: Search by unapplied amount range

            # Reference filters
            PaymentMethodRefValue: Search by payment method ID
            DepositToAccountRefValue: Search by deposit account ID

            MaxResults: Maximum number of results to return (default: 100)
            StartPosition: Starting position for pagination (default: 1)

        Returns:
            List of payments matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters
        if kwargs.get('CustomerRefValue'):
            conditions.append(f"CustomerRef = '{kwargs['CustomerRefValue']}'")

        if kwargs.get('PaymentRefNum'):
            conditions.append(f"PaymentRefNum = '{kwargs['PaymentRefNum']}'")

        if kwargs.get('CustomerName'):
            # For customer name search, we need to use a subquery
            customer_name = kwargs['CustomerName'].replace(
                "'", "''")  # Escape single quotes
            conditions.append(
                f"CustomerRef IN (SELECT Id FROM Customer WHERE Name LIKE '%{customer_name}%')")

        # Date range filters
        if kwargs.get('TransactionDateFrom'):
            conditions.append(f"TxnDate >= '{kwargs['TransactionDateFrom']}'")
        if kwargs.get('TransactionDateTo'):
            conditions.append(f"TxnDate <= '{kwargs['TransactionDateTo']}'")

        # Amount range filters
        if kwargs.get('MinAmount'):
            conditions.append(f"TotalAmt >= {kwargs['MinAmount']}")
        if kwargs.get('MaxAmount'):
            conditions.append(f"TotalAmt <= {kwargs['MaxAmount']}")

        if kwargs.get('MinUnappliedAmt'):
            conditions.append(f"UnappliedAmt >= {kwargs['MinUnappliedAmt']}")
        if kwargs.get('MaxUnappliedAmt'):
            conditions.append(f"UnappliedAmt <= {kwargs['MaxUnappliedAmt']}")

        # Reference filters
        if kwargs.get('PaymentMethodRefValue'):
            conditions.append(
                f"PaymentMethodRef = '{kwargs['PaymentMethodRefValue']}'")
        if kwargs.get('DepositToAccountRefValue'):
            conditions.append(
                f"DepositToAccountRef = '{kwargs['DepositToAccountRefValue']}'")

        # Build the complete query
        base_query = "SELECT * FROM Payment"

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            base_query += where_clause

        # Add pagination
        start_position = kwargs.get('StartPosition', 1)
        max_results = kwargs.get('MaxResults', 100)

        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no payments are returned
        if 'Payment' not in response['QueryResponse']:
            return []

        payments = response['QueryResponse']['Payment']
        results = [payment_data_to_mcp_object(payment) for payment in payments]

        return results

    async def update_payment(self, **kwargs) -> Dict[str, Any]:
        """Update an existing payment with comprehensive property support."""
        Id = kwargs.get('Id')
        if not Id:
            raise ValueError("Id is required for updating a payment")

        # Auto-fetch current sync token
        current_payment_response = await self.client._get(f"payment/{Id}")
        sync_token = current_payment_response.get(
            'Payment', {}).get('SyncToken', '0')

        payment_data = mcp_object_to_payment_data(**kwargs)
        payment_data.update({
            "Id": Id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('payment', payment_data)
        return payment_data_to_mcp_object(response['Payment'])

    async def delete_payment(self, Id: str) -> Dict[str, Any]:
        """Delete a payment."""
        # Auto-fetch current sync token
        current_payment_response = await self.client._get(f"payment/{Id}")
        current_payment = current_payment_response.get('Payment', {})

        if not current_payment:
            raise ValueError(f"Payment with ID {Id} not found")

        sync_token = current_payment.get('SyncToken', '0')

        # For delete operation, wrap in Payment object
        delete_data = {
            "Id": Id,
            "SyncToken": sync_token,
        }
        return await self.client._post("payment", delete_data, params={'operation': 'delete'})

    async def send_payment(self, Id: str, SendTo: str) -> Dict[str, Any]:
        """
        Send a payment receipt via email.

        Args:
            Id: The QuickBooks payment ID to send
            SendTo: Email address to send the payment receipt to

        Returns:
            The payment response body.
        """
        # Construct the endpoint URL
        endpoint = f"payment/{Id}/send"

        # Build query parameters
        params = {'sendTo': SendTo}

        # Send request with POST method (empty body as per API spec)
        response = await self.client._make_request('POST', endpoint, params=params)

        # The response should contain the updated payment data
        if 'Payment' in response:
            return payment_data_to_mcp_object(response['Payment'])

        return response

    async def void_payment(self, Id: str) -> Dict[str, Any]:
        """
        Void an existing payment in QuickBooks.

        The transaction remains active but all amounts and quantities are zeroed 
        and the string "Voided" is injected into Payment.PrivateNote, prepended 
        to existing text if present. If funds for the payment have been deposited, 
        you must delete the associated deposit object before voiding the payment object.

        Args:
            Id: The QuickBooks payment ID to void

        Returns:
            The payment response body with voided status.
        """
        # Auto-fetch current sync token
        current_payment_response = await self.client._get(f"payment/{Id}")
        current_payment = current_payment_response.get('Payment', {})

        if not current_payment:
            raise ValueError(f"Payment with ID {Id} not found")

        sync_token = current_payment.get('SyncToken', '0')

        # For void operation, wrap in Payment object
        void_data = {
            "Id": Id,
            "SyncToken": sync_token,
            "sparse": True,
        }

        response = await self.client._post("payment", void_data, params={'operation': 'void'})

        # The response should contain the voided payment data
        if 'Payment' in response:
            return payment_data_to_mcp_object(response['Payment'])

        return response


# Export tools
tools = [create_payment_tool, get_payment_tool, list_payments_tool, search_payments_tool,
         update_payment_tool, delete_payment_tool, send_payment_tool, void_payment_tool]
