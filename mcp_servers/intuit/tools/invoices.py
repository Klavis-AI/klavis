from typing import Any, Dict, List

from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

# Minimal properties for invoice creation (required by QuickBooks)
invoice_properties_minimal = {
    "CustomerRefValue": {
        "type": "string",
        "description": "Customer ID for the invoice"
    },
    "CustomerRefName": {
        "type": "string",
        "description": "Name of the customer associated with the invoice"
    },
    "LineItems": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "LineId": {"type": "string", "description": "Unique ID for this line item. Required for updates, ignored for creates"},
                "Amount": {"type": "number", "description": "Line total amount"},
                "Description": {"type": "string", "description": "Line item description"},
                "DetailType": {"type": "string", "description": "Line detail type: SalesItemLineDetail, GroupLine, DescriptionOnlyLine, DiscountLine, SubTotalLine", "default": "SalesItemLineDetail"},
                "LineNum": {"type": "number", "description": "Position of the line in the collection"},

                # SalesItemLineDetail fields
                "ItemId": {"type": "string", "description": "Reference to the inventory item"},
                "ItemName": {"type": "string", "description": "Name of the inventory item"},
                "Quantity": {"type": "number", "description": "Quantity of the item"},
                "UnitPrice": {"type": "number", "description": "Unit price of the item"},
                "DiscountRate": {"type": "number", "description": "Discount rate applied to this line as a percentage"},
                "DiscountAmount": {"type": "number", "description": "Discount amount applied to this line"},
                "ServiceDate": {"type": "string", "description": "Date when the service is performed (YYYY-MM-DD format)"},

                # GroupLineDetail fields
                "GroupItemId": {"type": "string", "description": "Reference to the group item for bundle lines"},
                "GroupItemName": {"type": "string", "description": "Name of the group item"},
                "GroupQuantity": {"type": "number", "description": "Quantity of the group item"},

                # DescriptionOnlyLine fields
                "IsSubtotal": {"type": "boolean", "description": "Set to true for subtotal lines"},

                # DiscountLineDetail fields
                "DiscountPercent": {"type": "number", "description": "Percentage discount as a number (10 for 10%)"},
                "DiscountAccountId": {"type": "string", "description": "Income account used to track discounts"},
                "DiscountAccountName": {"type": "string", "description": "Name of the discount account"},
                "IsPercentBased": {"type": "boolean", "description": "True if the discount is a percentage"},

                # References for any line type
                "ClassId": {"type": "string", "description": "Reference to the Class for the line item"},
                "ClassName": {"type": "string", "description": "Name of the Class"},
                "TaxCodeId": {"type": "string", "description": "Reference to the TaxCode for this item"},
                "TaxCodeName": {"type": "string", "description": "Name of the TaxCode"},

                # Nested lines for GroupLine
                "GroupLines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ItemId": {"type": "string"},
                            "Quantity": {"type": "number"},
                            "UnitPrice": {"type": "number"},
                            "DiscountRate": {"type": "number"},
                            "ClassId": {"type": "string"},
                            "TaxCodeId": {"type": "string"}
                        }
                    },
                    "description": "Individual item lines that comprise a bundle (for GroupLineDetail)"
                }
            },
            "required": ["Amount"]
        }
    },
}

# Invoice properties mapping (based on QuickBooks API documentation)
invoice_properties_user_define = {
    **invoice_properties_minimal,
    "DocNumber": {
        "type": "string",
        "description": "Reference number for the transaction. If not explicitly provided at create time, this field is populated based on the setting of Preferences:CustomTxnNumber"
    },
    "TxnDate": {
        "type": "string",
        "description": "The date entered by the user when this transaction occurred. Format: yyyy/MM/dd"
    },
    "ShipDate": {
        "type": "string",
        "description": "Date for delivery of goods or services. Format: yyyy/MM/dd"
    },
    "DueDate": {
        "type": "string",
        "description": "Date when the payment of the transaction is due. If date is not provided, the number of days specified in SalesTermRef added the transaction date will be used. Format: yyyy/MM/dd"
    },
    "CustomerMemo": {
        "type": "string",
        "description": "User-entered message to the customer; this message is visible to end user on their transactions"
    },
    "PrivateNote": {
        "type": "string",
        "description": "User entered, organization-private note about the transaction"
    },
    "BillEmail": {
        "type": "string",
        "description": "Identifies the e-mail address where the invoice is sent"
    },
    "BillEmailCc": {
        "type": "string",
        "description": "Identifies the carbon copy e-mail address where the invoice is sent"
    },
    "BillEmailBcc": {
        "type": "string",
        "description": "Identifies the blind carbon copy e-mail address where the invoice is sent"
    },
    "ShipFromAddrLine1": {
        "type": "string",
        "description": "First line of the address where goods are shipped from"
    },
    "ShipFromAddrLine2": {
        "type": "string",
        "description": "Second line of the address where goods are shipped from"
    },
    "ShipFromAddrLine3": {
        "type": "string",
        "description": "Third line of the address where goods are shipped from"
    },
    "ShipFromAddrLine4": {
        "type": "string",
        "description": "Fourth line of the address where goods are shipped from"
    },
    "ShipFromAddrLine5": {
        "type": "string",
        "description": "Fifth line of the address where goods are shipped from"
    },
    "ShipFromAddrCity": {
        "type": "string",
        "description": "City name for the shipping address where goods are shipped from"
    },
    "ShipFromAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the shipping address where goods are shipped from"
    },
    "ShipFromAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the shipping address where goods are shipped from"
    },
    "ShipFromAddrCountry": {
        "type": "string",
        "description": "Country name for the shipping address where goods are shipped from"
    },
    "ShipAddrLine1": {
        "type": "string",
        "description": "First line of the shipping address where goods must be shipped"
    },
    "ShipAddrLine2": {
        "type": "string",
        "description": "Second line of the shipping address"
    },
    "ShipAddrLine3": {
        "type": "string",
        "description": "Third line of the shipping address"
    },
    "ShipAddrLine4": {
        "type": "string",
        "description": "Fourth line of the shipping address"
    },
    "ShipAddrLine5": {
        "type": "string",
        "description": "Fifth line of the shipping address"
    },
    "ShipAddrCity": {
        "type": "string",
        "description": "City name for the shipping address"
    },
    "ShipAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the shipping address"
    },
    "ShipAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the shipping address"
    },
    "ShipAddrCountry": {
        "type": "string",
        "description": "Country name for the shipping address"
    },
    "BillAddrLine1": {
        "type": "string",
        "description": "First line of the billing address"
    },
    "BillAddrLine2": {
        "type": "string",
        "description": "Second line of the billing address"
    },
    "BillAddrLine3": {
        "type": "string",
        "description": "Third line of the billing address"
    },
    "BillAddrLine4": {
        "type": "string",
        "description": "Fourth line of the billing address"
    },
    "BillAddrLine5": {
        "type": "string",
        "description": "Fifth line of the billing address"
    },
    "BillAddrCity": {
        "type": "string",
        "description": "City name for the billing address"
    },
    "BillAddrCountrySubDivisionCode": {
        "type": "string",
        "description": "Region within a country for the billing address"
    },
    "BillAddrPostalCode": {
        "type": "string",
        "description": "Postal code for the billing address"
    },
    "BillAddrCountry": {
        "type": "string",
        "description": "Country name for the billing address"
    },
    "SalesTermRefValue": {
        "type": "string",
        "description": "Reference to the sales term associated with the transaction"
    },
    "SalesTermRefName": {
        "type": "string",
        "description": "Name of the sales term associated with the transaction"
    },
    "ClassRefValue": {
        "type": "string",
        "description": "Reference to the Class associated with the transaction"
    },
    "ClassRefName": {
        "type": "string",
        "description": "Name of the Class associated with the transaction"
    },
    "DepartmentRefValue": {
        "type": "string",
        "description": "Reference to a Department object specifying the location of the transaction"
    },
    "DepartmentRefName": {
        "type": "string",
        "description": "Name of the Department associated with the transaction"
    },
    "ShipMethodRefValue": {
        "type": "string",
        "description": "Reference to the ShipMethod associated with the transaction"
    },
    "ShipMethodRefName": {
        "type": "string",
        "description": "Name of the ShipMethod associated with the transaction"
    },
    "CurrencyRefValue": {
        "type": "string",
        "description": "Three letter ISO code representing the currency"
    },
    "CurrencyRefName": {
        "type": "string",
        "description": "Full name of the currency"
    },
    "ExchangeRate": {
        "type": "number",
        "description": "The exchange rate between the transaction currency and the home currency"
    },
    "GlobalTaxCalculation": {
        "type": "string",
        "description": "Method in which tax is applied. Allowed values are: TaxExcluded, TaxInclusive, and NotApplicable"
    },
    "ApplyTaxAfterDiscount": {
        "type": "boolean",
        "description": "If true, subtract the discount first and then calculate the sales tax"
    },
    "PrintStatus": {
        "type": "string",
        "description": "Printing status of the invoice. Valid values: NotSet, NeedToPrint, PrintComplete"
    },
    "EmailStatus": {
        "type": "string",
        "description": "Email status of the invoice. Valid values: NotSet, NeedToSend, EmailSent"
    },
    "TrackingNum": {
        "type": "string",
        "description": "Shipping provider's tracking number for the delivery of the goods"
    },
    "AllowOnlineACHPayment": {
        "type": "boolean",
        "description": "Specifies if this invoice can be paid with online bank transfers"
    },
    "AllowOnlineCreditCardPayment": {
        "type": "boolean",
        "description": "Specifies if online credit card payments are allowed for this invoice"
    },
    "Deposit": {
        "type": "number",
        "description": "The deposit made towards this invoice"
    },
    "DepositToAccountRefValue": {
        "type": "string",
        "description": "Account to which money is deposited"
    },
    "DepositToAccountRefName": {
        "type": "string",
        "description": "Name of the account to which money is deposited"
    }
}

invoice_properties = {
    **invoice_properties_user_define,
    "Id": {
        "type": "string",
        "description": "The unique QuickBooks invoice ID"
    },
    "SyncToken": {
        "type": "string",
        "description": "Version number of the object for concurrent updates"
    }
}

invoice_properties_full = {
    **invoice_properties,
    "TotalAmt": {
        "type": "number",
        "description": "Indicates the total amount of the transaction (read-only)"
    },
    "Balance": {
        "type": "number",
        "description": "The balance reflecting any payments made against the transaction (read-only)"
    },
    "HomeTotalAmt": {
        "type": "number",
        "description": "Total amount of the transaction in the home currency (read-only)"
    },
    "HomeBalance": {
        "type": "number",
        "description": "Convenience field containing amount in Balance expressed in home currency (read-only)"
    },
    "InvoiceLink": {
        "type": "string",
        "description": "Sharable link for the invoice sent to external customers (read-only)"
    },
    "RecurDataRefValue": {
        "type": "string",
        "description": "Reference to the Recurring Transaction template this Invoice was created from (read-only)"
    },
    "RecurDataRefName": {
        "type": "string",
        "description": "Name of the Recurring Transaction template (read-only)"
    }
}

# MCP Tool definitions
create_invoice_tool = Tool(
    name="create_invoice",
    title="Create Invoice",
    description="Create New Invoice - Create a new invoice in QuickBooks. Requires CustomerRef and at least one valid line (SalesItemLine, GroupLine, or DescriptionOnlyLine).",
    inputSchema={
        "type": "object",
        "properties": invoice_properties_minimal,
        "required": ["CustomerRefValue", "LineItems"]
    }
)

get_invoice_tool = Tool(
    name="get_invoice",
    title="Get Invoice",
    description="Get Single Invoice - Retrieve a specific invoice by ID from QuickBooks with all its details including line items, amounts, and status",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks invoice ID"}
        },
        "required": ["Id"]
    }
)

list_invoices_tool = Tool(
    name="list_invoices",
    title="List Invoices",
    description="List All Invoices - Retrieve all invoices from QuickBooks with pagination support. Use for browsing or getting overview of invoices",
    inputSchema={
        "type": "object",
        "properties": {
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1},
        },
        "required": [],
    }
)

search_invoices_tool = Tool(
    name="search_invoices",
    title="Search Invoices",
    description="Advanced Invoice Search - Search invoices with powerful filters including dates, amounts, addresses, customer info, and status. Perfect for finding specific invoices based on criteria",
    inputSchema={
        "type": "object",
        "properties": {
            "DocNumber": {"type": "string", "description": "Search by document/invoice number"},
            "CustomerRefValue": {"type": "string", "description": "Search by customer ID"},
            "CustomerName": {"type": "string", "description": "Search by customer name (partial match)"},

            # Date filters
            "TxnDateFrom": {"type": "string", "description": "Search invoices from this transaction date (YYYY-MM-DD format)"},
            "TxnDateTo": {"type": "string", "description": "Search invoices to this transaction date (YYYY-MM-DD format)"},
            "DueDateFrom": {"type": "string", "description": "Search invoices from this due date (YYYY-MM-DD format)"},
            "DueDateTo": {"type": "string", "description": "Search invoices to this due date (YYYY-MM-DD format)"},
            "ShipDateFrom": {"type": "string", "description": "Search invoices from this ship date (YYYY-MM-DD format)"},
            "ShipDateTo": {"type": "string", "description": "Search invoices to this ship date (YYYY-MM-DD format)"},

            # Amount filters
            "MinAmount": {"type": "number", "description": "Minimum total amount"},
            "MaxAmount": {"type": "number", "description": "Maximum total amount"},
            "MinBalance": {"type": "number", "description": "Minimum balance amount"},
            "MaxBalance": {"type": "number", "description": "Maximum balance amount"},

            # Status filters
            "EmailStatus": {"type": "string", "description": "Email status: NotSet, NeedToSend, EmailSent"},
            "PrintStatus": {"type": "string", "description": "Print status: NotSet, NeedToPrint, PrintComplete"},

            # Address filters - Billing Address
            "BillAddrCity": {"type": "string", "description": "Search by billing address city"},
            "BillAddrState": {"type": "string", "description": "Search by billing address state/province"},
            "BillAddrPostalCode": {"type": "string", "description": "Search by billing address postal code"},
            "BillAddrCountry": {"type": "string", "description": "Search by billing address country"},
            "BillAddrLine1": {"type": "string", "description": "Search by billing address line 1 (partial match)"},

            # Address filters - Shipping Address
            "ShipAddrCity": {"type": "string", "description": "Search by shipping address city"},
            "ShipAddrState": {"type": "string", "description": "Search by shipping address state/province"},
            "ShipAddrPostalCode": {"type": "string", "description": "Search by shipping address postal code"},
            "ShipAddrCountry": {"type": "string", "description": "Search by shipping address country"},
            "ShipAddrLine1": {"type": "string", "description": "Search by shipping address line 1 (partial match)"},

            # Address filters - Ship From Address
            "ShipFromAddrCity": {"type": "string", "description": "Search by ship from address city"},
            "ShipFromAddrState": {"type": "string", "description": "Search by ship from address state/province"},
            "ShipFromAddrPostalCode": {"type": "string", "description": "Search by ship from address postal code"},
            "ShipFromAddrCountry": {"type": "string", "description": "Search by ship from address country"},
            "ShipFromAddrLine1": {"type": "string", "description": "Search by ship from address line 1 (partial match)"},

            # Pagination
            "MaxResults": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "StartPosition": {"type": "integer", "description": "Starting position for pagination (1-based)", "default": 1}
        },
        "required": [],
    }
)

update_invoice_tool = Tool(
    name="update_invoice",
    title="Update Invoice",
    description="Update Existing Invoice - Modify an existing invoice in QuickBooks. Automatically handles sync tokens for safe concurrent updates",
    inputSchema={
        "type": "object",
        "properties": invoice_properties_user_define,
        "required": ["Id"]
    }
)

delete_invoice_tool = Tool(
    name="delete_invoice",
    title="Delete Invoice",
    description="️Delete Invoice - Permanently delete an invoice from QuickBooks. Use with caution as this action cannot be undone",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {"type": "string", "description": "The QuickBooks invoice ID to delete"}
        },
        "required": ["Id"]
    }
)

send_invoice_tool = Tool(
    name="send_invoice",
    title="Send Invoice",
    description="Send Invoice via Email - Send an invoice to customer via email with delivery tracking. Updates email status and delivery info automatically",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {
                "type": "string",
                "description": "The QuickBooks invoice ID to send"
            },
            "SendTo": {
                "type": "string",
                "description": "Optional email address to send the invoice to. If not provided, uses the invoice's BillEmail address",
            }
        },
        "required": ["Id"]
    }
)

void_invoice_tool = Tool(
    name="void_invoice",
    title="Void Invoice",
    description="Void Invoice - Void an existing invoice in QuickBooks. Sets all amounts to zero and marks as 'Voided' while keeping the record for audit trail",
    inputSchema={
        "type": "object",
        "properties": {
            "Id": {
                "type": "string",
                "description": "The QuickBooks invoice ID to void"
            }
        },
        "required": ["Id"]
    }
)


def mcp_object_to_invoice_data(**kwargs) -> Dict[str, Any]:
    """
    Convert MCP object format to QuickBooks invoice data format.
    This function transforms the flat MCP structure to the nested format expected by QuickBooks API.
    """
    invoice_data = {}

    # Basic invoice information - direct copy
    for field in ['DocNumber', 'TxnDate', 'ShipDate', 'DueDate',
                  'PrivateNote', 'PrintStatus', 'EmailStatus', 'TrackingNum']:
        if field in kwargs:
            invoice_data[field] = kwargs[field]

    # CustomerMemo needs to be in object format
    if 'CustomerMemo' in kwargs:
        invoice_data['CustomerMemo'] = {'value': kwargs['CustomerMemo']}

    # Boolean fields
    for field in ['AllowOnlineACHPayment', 'AllowOnlineCreditCardPayment',
                  'ApplyTaxAfterDiscount']:
        if field in kwargs:
            invoice_data[field] = kwargs[field]

    # Numeric fields
    for field in ['Deposit', 'ExchangeRate', 'GlobalTaxCalculation']:
        if field in kwargs:
            invoice_data[field] = kwargs[field]

    # Email addresses - convert to structured objects
    for email_field in ['BillEmail', 'BillEmailCc', 'BillEmailBcc']:
        if email_field in kwargs:
            invoice_data[email_field] = {'Address': kwargs[email_field]}

    # Line items - handle the LineItems parameter with all detail types
    if 'LineItems' in kwargs:
        lines = []
        for item in kwargs['LineItems']:
            line = {
                "Amount": item["Amount"],
                "DetailType": item.get("DetailType", "SalesItemLineDetail"),
                "Description": item.get("Description")
            }

            if item.get("LineId"):
                line["Id"] = item["LineId"]
            if item.get("LineNum"):
                line["LineNum"] = item["LineNum"]

            detail_type = item.get("DetailType", "SalesItemLineDetail")

            if detail_type == "SalesItemLineDetail":
                sales_detail = {}
                if item.get("ItemId"):
                    sales_detail["ItemRef"] = {"value": item["ItemId"]}
                    if item.get("ItemName"):
                        sales_detail["ItemRef"]["name"] = item["ItemName"]
                if item.get("Quantity"):
                    sales_detail["Qty"] = item["Quantity"]
                if item.get("UnitPrice"):
                    sales_detail["UnitPrice"] = item["UnitPrice"]
                if item.get("DiscountRate"):
                    sales_detail["DiscountRate"] = item["DiscountRate"]
                if item.get("DiscountAmount"):
                    sales_detail["DiscountAmt"] = item["DiscountAmount"]
                if item.get("ServiceDate"):
                    sales_detail["ServiceDate"] = item["ServiceDate"]
                if item.get("ClassId"):
                    sales_detail["ClassRef"] = {"value": item["ClassId"]}
                    if item.get("ClassName"):
                        sales_detail["ClassRef"]["name"] = item["ClassName"]
                if item.get("TaxCodeId"):
                    sales_detail["TaxCodeRef"] = {"value": item["TaxCodeId"]}
                    if item.get("TaxCodeName"):
                        sales_detail["TaxCodeRef"]["name"] = item["TaxCodeName"]

                if sales_detail:
                    line["SalesItemLineDetail"] = sales_detail

            elif detail_type == "GroupLineDetail":
                group_detail = {}
                if item.get("GroupItemId"):
                    group_detail["GroupItemRef"] = {
                        "value": item["GroupItemId"]}
                    if item.get("GroupItemName"):
                        group_detail["GroupItemRef"]["name"] = item["GroupItemName"]
                if item.get("GroupQuantity"):
                    group_detail["Quantity"] = item["GroupQuantity"]

                # Handle nested lines for GroupLine
                if item.get("GroupLines") and isinstance(item["GroupLines"], list):
                    group_lines = []
                    for group_item in item["GroupLines"]:
                        group_line = {
                            "Amount": group_item.get("Amount", 0),
                            "DetailType": "SalesItemLineDetail"
                        }
                        group_sales_detail = {}
                        if group_item.get("ItemId"):
                            group_sales_detail["ItemRef"] = {
                                "value": group_item["ItemId"]}
                        if group_item.get("Quantity"):
                            group_sales_detail["Qty"] = group_item["Quantity"]
                        if group_item.get("UnitPrice"):
                            group_sales_detail["UnitPrice"] = group_item["UnitPrice"]
                        if group_item.get("DiscountRate"):
                            group_sales_detail["DiscountRate"] = group_item["DiscountRate"]
                        if group_item.get("ClassId"):
                            group_sales_detail["ClassRef"] = {
                                "value": group_item["ClassId"]}
                        if group_item.get("TaxCodeId"):
                            group_sales_detail["TaxCodeRef"] = {
                                "value": group_item["TaxCodeId"]}

                        if group_sales_detail:
                            group_line["SalesItemLineDetail"] = group_sales_detail
                        group_lines.append(group_line)

                    group_detail["Line"] = group_lines

                line["GroupLineDetail"] = group_detail

            elif detail_type == "DescriptionOnlyLine":
                description_detail = {}
                if item.get("ServiceDate"):
                    description_detail["ServiceDate"] = item["ServiceDate"]
                if item.get("TaxCodeId"):
                    description_detail["TaxCodeRef"] = {
                        "value": item["TaxCodeId"]}
                    if item.get("TaxCodeName"):
                        description_detail["TaxCodeRef"]["name"] = item["TaxCodeName"]

                line["DescriptionLineDetail"] = description_detail

            elif detail_type == "DiscountLineDetail":
                discount_detail = {}
                if item.get("IsPercentBased") is not None:
                    discount_detail["PercentBased"] = item["IsPercentBased"]
                if item.get("DiscountPercent"):
                    discount_detail["DiscountPercent"] = item["DiscountPercent"]
                if item.get("DiscountAccountId"):
                    discount_detail["DiscountAccountRef"] = {
                        "value": item["DiscountAccountId"]}
                    if item.get("DiscountAccountName"):
                        discount_detail["DiscountAccountRef"]["name"] = item["DiscountAccountName"]
                if item.get("ClassId"):
                    discount_detail["ClassRef"] = {
                        "value": item["ClassId"], "name": item.get("ClassName", "")}
                if item.get("TaxCodeId"):
                    discount_detail["TaxCodeRef"] = {
                        "value": item["TaxCodeId"], "name": item.get("TaxCodeName", "")}

                line["DiscountLineDetail"] = discount_detail

            elif detail_type == "SubTotalLineDetail":
                subtotal_detail = {}
                if item.get("ItemId"):
                    subtotal_detail["ItemRef"] = {
                        "value": item["ItemId"], "name": item.get("ItemName", "")}

                line["SubTotalLineDetail"] = subtotal_detail

            lines.append(line)
        invoice_data['Line'] = lines

    # Reference objects - convert separate value/name fields to structured objects
    ref_mappings = [
        ('CustomerRef', 'CustomerRefValue', 'CustomerRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('SalesTermRef', 'SalesTermRefValue', 'SalesTermRefName'),
        ('ClassRef', 'ClassRefValue', 'ClassRefName'),
        ('DepartmentRef', 'DepartmentRefValue', 'DepartmentRefName'),
        ('ShipMethodRef', 'ShipMethodRefValue', 'ShipMethodRefName'),
        ('DepositToAccountRef', 'DepositToAccountRefValue', 'DepositToAccountRefName')
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if value_field in kwargs:
            ref_obj = {'value': kwargs[value_field]}
            if name_field in kwargs:
                ref_obj['name'] = kwargs[name_field]
            invoice_data[ref_name] = ref_obj

    # Address fields - convert flattened fields to structured objects
    for addr_type in ['BillAddr', 'ShipAddr', 'ShipFromAddr']:
        address_fields = ['Line1', 'Line2', 'Line3', 'Line4', 'Line5',
                          'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']

        has_address = any(kwargs.get(f'{addr_type}{field}')
                          for field in address_fields)
        if has_address:
            addr_obj = {}
            for field in address_fields:
                if kwargs.get(f'{addr_type}{field}'):
                    addr_obj[field] = kwargs[f'{addr_type}{field}']
            invoice_data[addr_type] = addr_obj

    return invoice_data


def invoice_data_to_mcp_object(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert QuickBooks invoice data format to MCP object format.
    This function flattens the nested QuickBooks structure to the flat format expected by MCP tools.
    """
    mcp_object = {}

    # Copy basic fields if present
    for field in [
        'Id', 'DocNumber', 'TxnDate', 'ShipDate', 'DueDate',
        'PrivateNote', 'PrintStatus', 'EmailStatus', 'TrackingNum',
        'AllowOnlineACHPayment', 'AllowOnlineCreditCardPayment',
        'ApplyTaxAfterDiscount', 'Deposit', 'ExchangeRate', 'GlobalTaxCalculation'
    ]:
        if field in invoice_data:
            mcp_object[field] = invoice_data[field]

    # Handle CustomerMemo which might be in object format
    if 'CustomerMemo' in invoice_data:
        memo = invoice_data['CustomerMemo']
        if isinstance(memo, dict) and 'value' in memo:
            mcp_object['CustomerMemo'] = memo['value']
        else:
            mcp_object['CustomerMemo'] = memo

    # Handle read-only fields
    for field in ['TotalAmt', 'Balance', 'HomeTotalAmt', 'HomeBalance', 'InvoiceLink']:
        if field in invoice_data:
            mcp_object[field] = invoice_data[field]

    # Email addresses - flatten structured objects
    for email_field in ['BillEmail', 'BillEmailCc', 'BillEmailBcc']:
        if email_field in invoice_data:
            addr = invoice_data[email_field]
            if isinstance(addr, dict) and 'Address' in addr:
                mcp_object[email_field] = addr['Address']

    # Line items - flatten all line types to LineItems
    if 'Line' in invoice_data and isinstance(invoice_data['Line'], list):
        line_items = []
        for line in invoice_data['Line']:
            if isinstance(line, dict) and 'Amount' in line:
                item = {
                    'Amount': line['Amount'],
                    'Description': line.get('Description'),
                    'LineId': line.get('Id'),
                    'LineNum': line.get('LineNum'),
                    'DetailType': line.get('DetailType', 'SalesItemLineDetail')
                }

                detail_type = line.get('DetailType', 'SalesItemLineDetail')

                # Handle different detail types
                if detail_type == 'SalesItemLineDetail' and 'SalesItemLineDetail' in line:
                    detail = line['SalesItemLineDetail']
                    if 'ItemRef' in detail:
                        item['ItemId'] = detail['ItemRef'].get('value')
                        item['ItemName'] = detail['ItemRef'].get('name')
                    if 'Qty' in detail:
                        item['Quantity'] = detail['Qty']
                    if 'UnitPrice' in detail:
                        item['UnitPrice'] = detail['UnitPrice']
                    if 'DiscountRate' in detail:
                        item['DiscountRate'] = detail['DiscountRate']
                    if 'DiscountAmt' in detail:
                        item['DiscountAmount'] = detail['DiscountAmt']
                    if 'ServiceDate' in detail:
                        item['ServiceDate'] = detail['ServiceDate']
                    if 'ClassRef' in detail:
                        item['ClassId'] = detail['ClassRef'].get('value')
                        item['ClassName'] = detail['ClassRef'].get('name')
                    if 'TaxCodeRef' in detail:
                        item['TaxCodeId'] = detail['TaxCodeRef'].get('value')
                        item['TaxCodeName'] = detail['TaxCodeRef'].get(
                            'name')

                elif detail_type == 'GroupLineDetail' and 'GroupLineDetail' in line:
                    detail = line['GroupLineDetail']
                    if 'GroupItemRef' in detail:
                        item['GroupItemId'] = detail['GroupItemRef'].get(
                            'value')
                        item['GroupItemName'] = detail['GroupItemRef'].get(
                            'name')
                    if 'Quantity' in detail:
                        item['GroupQuantity'] = detail['Quantity']

                    # Handle nested group lines
                    if 'Line' in detail and isinstance(detail['Line'], list):
                        group_lines = []
                        for group_line in detail['Line']:
                            if isinstance(group_line, dict) and 'SalesItemLineDetail' in group_line:
                                group_detail = group_line['SalesItemLineDetail']
                                group_item = {
                                    'ItemId': group_detail.get('ItemRef', {}).get('value'),
                                    'Quantity': group_detail.get('Qty'),
                                    'UnitPrice': group_detail.get('UnitPrice'),
                                    'DiscountRate': group_detail.get('DiscountRate'),
                                    'ClassId': group_detail.get('ClassRef', {}).get('value'),
                                    'TaxCodeId': group_detail.get('TaxCodeRef', {}).get('value')
                                }
                                group_lines.append(group_item)
                        item['GroupLines'] = group_lines

                elif detail_type == 'DescriptionOnlyLine' and 'DescriptionLineDetail' in line:
                    detail = line['DescriptionLineDetail']
                    if 'ServiceDate' in detail:
                        item['ServiceDate'] = detail['ServiceDate']
                    if 'TaxCodeRef' in detail:
                        item['TaxCodeId'] = detail['TaxCodeRef'].get('value')
                        item['TaxCodeName'] = detail['TaxCodeRef'].get(
                            'name')
                    # Check if this is a subtotal line
                    description = line.get('Description', '')
                    if description and description.startswith('Subtotal:'):
                        item['IsSubtotal'] = True

                elif detail_type == 'DiscountLineDetail' and 'DiscountLineDetail' in line:
                    detail = line['DiscountLineDetail']
                    if 'DiscountPercent' in detail:
                        item['DiscountPercent'] = detail['DiscountPercent']
                    if 'PercentBased' in detail:
                        item['IsPercentBased'] = detail['PercentBased']
                    if 'DiscountAccountRef' in detail:
                        item['DiscountAccountId'] = detail['DiscountAccountRef'].get(
                            'value')
                        item['DiscountAccountName'] = detail['DiscountAccountRef'].get(
                            'name')
                    if 'ClassRef' in detail:
                        item['ClassId'] = detail['ClassRef'].get('value')
                        item['ClassName'] = detail['ClassRef'].get('name')
                    if 'TaxCodeRef' in detail:
                        item['TaxCodeId'] = detail['TaxCodeRef'].get('value')
                        item['TaxCodeName'] = detail['TaxCodeRef'].get(
                            'name')

                elif detail_type == 'SubTotalLineDetail' and 'SubTotalLineDetail' in line:
                    detail = line['SubTotalLineDetail']
                    if 'ItemRef' in detail:
                        item['ItemId'] = detail['ItemRef'].get('value')
                        item['ItemName'] = detail['ItemRef'].get('name')

                line_items.append(item)
        mcp_object['LineItems'] = line_items

    # Reference objects - flatten to separate value and name fields
    ref_mappings = [
        ('CustomerRef', 'CustomerRefValue', 'CustomerRefName'),
        ('CurrencyRef', 'CurrencyRefValue', 'CurrencyRefName'),
        ('SalesTermRef', 'SalesTermRefValue', 'SalesTermRefName'),
        ('ClassRef', 'ClassRefValue', 'ClassRefName'),
        ('DepartmentRef', 'DepartmentRefValue', 'DepartmentRefName'),
        ('ShipMethodRef', 'ShipMethodRefValue', 'ShipMethodRefName'),
        ('DepositToAccountRef', 'DepositToAccountRefValue', 'DepositToAccountRefName'),
        ('RecurDataRef', 'RecurDataRefValue', 'RecurDataRefName'),
        ('SyncToken', 'SyncToken', None)
    ]

    for ref_name, value_field, name_field in ref_mappings:
        if ref_name in invoice_data:
            ref = invoice_data[ref_name]
            if isinstance(ref, dict):
                if 'value' in ref:
                    mcp_object[value_field] = ref['value']
                if name_field and 'name' in ref:
                    mcp_object[name_field] = ref['name']
            else:
                # Handle cases where SyncToken might be directly in invoice_data
                mcp_object[value_field] = ref

    # Address fields - flatten structured objects
    address_mappings = [
        ('BillAddr', 'BillAddr'),
        ('ShipAddr', 'ShipAddr'),
        ('ShipFromAddr', 'ShipFromAddr')
    ]

    for addr_type, prefix in address_mappings:
        if addr_type in invoice_data and isinstance(invoice_data[addr_type], dict):
            addr = invoice_data[addr_type]
            for field in ['Line1', 'Line2', 'Line3', 'Line4', 'Line5',
                          'City', 'CountrySubDivisionCode', 'PostalCode', 'Country']:
                if field in addr:
                    mcp_object[f'{prefix}{field}'] = addr[field]

    return mcp_object


class InvoiceManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_invoice(self, **kwargs) -> Dict[str, Any]:
        """Create a new invoice with comprehensive property support."""
        invoice_data = mcp_object_to_invoice_data(**kwargs)

        # Ensure CustomerRef is included
        if 'CustomerRef' not in invoice_data and 'CustomerRefValue' in kwargs:
            invoice_data['CustomerRef'] = {'value': kwargs['CustomerRefValue']}
            if 'CustomerRefName' in kwargs:
                invoice_data['CustomerRef']['name'] = kwargs['CustomerRefName']

        response = await self.client._post('invoice', invoice_data)
        return invoice_data_to_mcp_object(response['Invoice'])

    async def get_invoice(self, Id: str) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        response = await self.client._get(f"invoice/{Id}")
        return invoice_data_to_mcp_object(response['Invoice'])

    async def list_invoices(self, MaxResults: int = 100, StartPosition: int = 1) -> List[Dict[str, Any]]:
        """List all invoices with comprehensive properties and pagination support."""
        query = f"select * from Invoice STARTPOSITION {StartPosition} MAXRESULTS {MaxResults}"
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
            DocNumber: Search by document/invoice number
            CustomerRefValue: Search by customer ID
            CustomerName: Search by customer name (partial match)

            # Date filters
            TxnDateFrom/TxnDateTo: Search by transaction date range
            DueDateFrom/DueDateTo: Search by due date range  
            ShipDateFrom/ShipDateTo: Search by ship date range

            # Amount filters
            MinAmount/MaxAmount: Search by total amount range
            MinBalance/MaxBalance: Search by balance amount range

            # Status filters
            EmailStatus: Email status filter
            PrintStatus: Print status filter

            # Address filters (billing, shipping, ship-from)
            BillAddrCity, ShipAddrCity, ShipFromAddrCity: Search by city
            BillAddrState, ShipAddrState, ShipFromAddrState: Search by state/province
            BillAddrPostalCode, ShipAddrPostalCode, ShipFromAddrPostalCode: Search by postal code
            BillAddrCountry, ShipAddrCountry, ShipFromAddrCountry: Search by country
            BillAddrLine1, ShipAddrLine1, ShipFromAddrLine1: Search by address line 1 (partial match)

            MaxResults: Maximum number of results to return (default: 100)
            StartPosition: Starting position for pagination (default: 1)

        Returns:
            List of invoices matching the search criteria
        """
        # Build WHERE clause conditions
        conditions = []

        # Basic filters
        if kwargs.get('DocNumber'):
            conditions.append(f"DocNumber = '{kwargs['DocNumber']}'")

        if kwargs.get('CustomerRefValue'):
            conditions.append(f"CustomerRef = '{kwargs['CustomerRefValue']}'")

        if kwargs.get('CustomerName'):
            # For customer name search, we need to use LIKE operator
            customer_name = kwargs['CustomerName'].replace(
                "'", "''")  # Escape single quotes
            conditions.append(
                f"CustomerRef IN (SELECT Id FROM Customer WHERE Name LIKE '%{customer_name}%')")

        # Date range filters
        if kwargs.get('TxnDateFrom'):
            conditions.append(f"TxnDate >= '{kwargs['TxnDateFrom']}'")
        if kwargs.get('TxnDateTo'):
            conditions.append(f"TxnDate <= '{kwargs['TxnDateTo']}'")

        if kwargs.get('DueDateFrom'):
            conditions.append(f"DueDate >= '{kwargs['DueDateFrom']}'")
        if kwargs.get('DueDateTo'):
            conditions.append(f"DueDate <= '{kwargs['DueDateTo']}'")

        if kwargs.get('ShipDateFrom'):
            conditions.append(f"ShipDate >= '{kwargs['ShipDateFrom']}'")
        if kwargs.get('ShipDateTo'):
            conditions.append(f"ShipDate <= '{kwargs['ShipDateTo']}'")

        # Amount range filters
        if kwargs.get('MinAmount'):
            conditions.append(f"TotalAmt >= {kwargs['MinAmount']}")
        if kwargs.get('MaxAmount'):
            conditions.append(f"TotalAmt <= {kwargs['MaxAmount']}")

        if kwargs.get('MinBalance'):
            conditions.append(f"Balance >= {kwargs['MinBalance']}")
        if kwargs.get('MaxBalance'):
            conditions.append(f"Balance <= {kwargs['MaxBalance']}")

        # Status filters
        if kwargs.get('EmailStatus'):
            conditions.append(f"EmailStatus = '{kwargs['EmailStatus']}'")
        if kwargs.get('PrintStatus'):
            conditions.append(f"PrintStatus = '{kwargs['PrintStatus']}'")

        # Address filters - Note: QuickBooks API has limited support for nested object queries
        # For address searches, we'll need to use more complex queries or post-filter results
        address_filters = {}

        # Billing Address filters
        for field in ['BillAddrCity', 'BillAddrState', 'BillAddrPostalCode', 'BillAddrCountry']:
            if kwargs.get(field):
                # Map the field name to QB API format
                qb_field = field.replace('BillAddr', 'BillAddr.').replace(
                    'State', 'CountrySubDivisionCode')
                if field.endswith('Line1'):
                    # For partial match on address lines, we'll post-filter
                    address_filters[field] = kwargs[field]
                else:
                    conditions.append(f"{qb_field} = '{kwargs[field]}'")

        if kwargs.get('BillAddrLine1'):
            address_filters['BillAddrLine1'] = kwargs['BillAddrLine1']

        # Shipping Address filters
        for field in ['ShipAddrCity', 'ShipAddrState', 'ShipAddrPostalCode', 'ShipAddrCountry']:
            if kwargs.get(field):
                qb_field = field.replace('ShipAddr', 'ShipAddr.').replace(
                    'State', 'CountrySubDivisionCode')
                if field.endswith('Line1'):
                    address_filters[field] = kwargs[field]
                else:
                    conditions.append(f"{qb_field} = '{kwargs[field]}'")

        if kwargs.get('ShipAddrLine1'):
            address_filters['ShipAddrLine1'] = kwargs['ShipAddrLine1']

        # Ship From Address filters
        for field in ['ShipFromAddrCity', 'ShipFromAddrState', 'ShipFromAddrPostalCode', 'ShipFromAddrCountry']:
            if kwargs.get(field):
                qb_field = field.replace('ShipFromAddr', 'ShipFromAddr.').replace(
                    'State', 'CountrySubDivisionCode')
                if field.endswith('Line1'):
                    address_filters[field] = kwargs[field]
                else:
                    conditions.append(f"{qb_field} = '{kwargs[field]}'")

        if kwargs.get('ShipFromAddrLine1'):
            address_filters['ShipFromAddrLine1'] = kwargs['ShipFromAddrLine1']

        # Build the complete query
        base_query = "SELECT * FROM Invoice"

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            base_query += where_clause

        # Add pagination
        start_position = kwargs.get('StartPosition', 1)
        max_results = kwargs.get('MaxResults', 100)

        query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {max_results}"

        response = await self.client._get('query', params={'query': query})

        # Handle case when no invoices are returned
        if 'Invoice' not in response['QueryResponse']:
            return []

        invoices = response['QueryResponse']['Invoice']
        results = [invoice_data_to_mcp_object(invoice) for invoice in invoices]

        # Post-filter for address line fields (partial matching)
        if address_filters:
            filtered_results = []
            for invoice in results:
                match = True

                # Check BillAddrLine1
                if address_filters.get('BillAddrLine1'):
                    bill_line1 = invoice.get('BillAddrLine1', '').lower()
                    search_term = address_filters['BillAddrLine1'].lower()
                    if search_term not in bill_line1:
                        match = False

                # Check ShipAddrLine1
                if address_filters.get('ShipAddrLine1'):
                    ship_line1 = invoice.get('ShipAddrLine1', '').lower()
                    search_term = address_filters['ShipAddrLine1'].lower()
                    if search_term not in ship_line1:
                        match = False

                # Check ShipFromAddrLine1
                if address_filters.get('ShipFromAddrLine1'):
                    ship_from_line1 = invoice.get(
                        'ShipFromAddrLine1', '').lower()
                    search_term = address_filters['ShipFromAddrLine1'].lower()
                    if search_term not in ship_from_line1:
                        match = False

                if match:
                    filtered_results.append(invoice)

            return filtered_results

        return results

    async def update_invoice(self, **kwargs) -> Dict[str, Any]:
        """Update an existing invoice with comprehensive property support."""
        Id = kwargs.get('Id')
        if not Id:
            raise ValueError("Id is required for updating an invoice")

        # Auto-fetch current sync token
        current_invoice_response = await self.client._get(f"invoice/{Id}")
        sync_token = current_invoice_response.get(
            'Invoice', {}).get('SyncToken', '0')

        invoice_data = mcp_object_to_invoice_data(**kwargs)
        invoice_data.update({
            "Id": Id,
            "SyncToken": sync_token,
            "sparse": True,
        })

        response = await self.client._post('invoice', invoice_data)
        return invoice_data_to_mcp_object(response['Invoice'])

    async def delete_invoice(self, Id: str) -> Dict[str, Any]:
        """Delete an invoice."""
        # Auto-fetch current sync token
        current_invoice_response = await self.client._get(f"invoice/{Id}")
        current_invoice = current_invoice_response.get('Invoice', {})

        if not current_invoice:
            raise ValueError(f"Invoice with ID {Id} not found")

        sync_token = current_invoice.get('SyncToken', '0')

        # For delete operation, wrap in Invoice object
        delete_data = {
            "Id": Id,
            "SyncToken": sync_token,
        }
        return await self.client._post("invoice", delete_data, params={'operation': 'delete'})

    async def send_invoice(self, Id: str, SendTo: str = None) -> Dict[str, Any]:
        """
        Send an invoice via email with delivery info and email status updates.

        The Invoice.EmailStatus parameter is set to EmailSent.
        The Invoice.DeliveryInfo element is populated with sending information.
        The Invoice.BillEmail.Address parameter is updated to the address specified
        with the value of the sendTo query parameter, if specified.

        Args:
            Id: The QuickBooks invoice ID to send
            sendTo: Optional email address to send the invoice to. If not provided,
                   uses the invoice's BillEmail address.

        Returns:
            The invoice response body with updated email status and delivery info.
        """
        # Construct the endpoint URL
        endpoint = f"invoice/{Id}/send"

        # Build query parameters
        params = {}
        if SendTo:
            params['sendTo'] = SendTo

        # Send request with POST method (empty body as per API spec)
        response = await self.client._make_request('POST', endpoint, params=params)

        # The response should contain the updated invoice data
        if 'Invoice' in response:
            return invoice_data_to_mcp_object(response['Invoice'])

        return response

    async def void_invoice(self, Id: str) -> Dict[str, Any]:
        """
        Void an existing invoice in QuickBooks.

        The transaction remains active but all amounts and quantities are zeroed 
        and the string "Voided" is injected into Invoice.PrivateNote, prepended 
        to existing text if present.

        Args:
            Id: The QuickBooks invoice ID to void

        Returns:
            The invoice response body with voided status.
        """
        # Auto-fetch current sync token
        current_invoice_response = await self.client._get(f"invoice/{Id}")
        current_invoice = current_invoice_response.get('Invoice', {})

        if not current_invoice:
            raise ValueError(f"Invoice with ID {Id} not found")

        sync_token = current_invoice.get('SyncToken', '0')

        # For void operation, wrap in Invoice object
        void_data = {
            "Id": Id,
            "SyncToken": sync_token,
        }

        response = await self.client._post("invoice", void_data, params={'operation': 'void'})

        # The response should contain the voided invoice data
        if 'Invoice' in response:
            return invoice_data_to_mcp_object(response['Invoice'])

        return response


# Export tools
tools = [create_invoice_tool, get_invoice_tool, list_invoices_tool, search_invoices_tool,
         update_invoice_tool, delete_invoice_tool, send_invoice_tool, void_invoice_tool]
