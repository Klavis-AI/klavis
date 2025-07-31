from typing import Any, Dict, List

from mcp.types import Tool
from .http_client import QuickBooksHTTPClient

# MCP Tool definitions
create_invoice_tool = Tool(
    name="create_invoice",
    description="Create a new invoice in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID for the invoice"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Line item description"},
                        "amount": {"type": "number", "description": "Line total amount"},
                        "detail_type": {"type": "string", "description": "Line detail type", "default": "SalesItemLineDetail"},
                        "item_id": {"type": "string", "description": "Reference to the inventory item", "default": "1"}
                    },
                    "required": ["amount"]
                }
            }
        },
        "required": ["customer_id", "line_items"]
    }
)

get_invoice_tool = Tool(
    name="get_invoice",
    description="Get a specific invoice by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "description": "The QuickBooks invoice ID"}
        },
        "required": ["invoice_id"]
    }
)

list_invoices_tool = Tool(
    name="list_invoices",
    description="List all invoices from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100}
        }
    }
)

update_invoice_tool = Tool(
    name="update_invoice",
    description="Update an existing invoice in QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "description": "The QuickBooks invoice ID to update"},
            "sync_token": {"type": "string", "description": "The sync token for the invoice"},
            "line_items": {"type": "array", "items": {"type": "object"}},
            "customer_id": {"type": "string"}
        },
        "required": ["invoice_id", "sync_token"]
    }
)

delete_invoice_tool = Tool(
    name="delete_invoice",
    description="Delete an invoice from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "description": "The QuickBooks invoice ID to delete"},
            "sync_token": {"type": "string", "description": "The sync token for the invoice"}
        },
        "required": ["invoice_id", "sync_token"]
    }
)

class InvoiceManager:
    def __init__(self, client: QuickBooksHTTPClient):
        self.client = client

    async def create_invoice(self, customer_id: str, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        line = []
        for item in line_items:
            line.append({
                "Amount": item["amount"],
                "DetailType": item.get("detail_type", "SalesItemLineDetail"),
                "Description": item.get('description'),
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": item.get('item_id', '1')
                    }
                }
            })

        invoice_data = {
            "Line": line,
            "CustomerRef": {
                "value": customer_id
            }
        }
        return await self.client._post('invoice', invoice_data)

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        return await self.client._get(f"invoice/{invoice_id}")

    async def list_invoices(self, max_results: int = 100) -> List[Dict[str, Any]]:
        query = f"select * from Invoice STARTPOSITION 1 MAXRESULTS {max_results}"
        return await self.client._get('query', params={'query': query})

    async def update_invoice(self, invoice_id: str, sync_token: str, **kwargs) -> Dict[str, Any]:
        invoice_data = {
            "Id": invoice_id,
            "SyncToken": sync_token,
            "sparse": True
        }
        if 'line_items' in kwargs:
            lines = []
            for item in kwargs['line_items']:
                lines.append({
                    "Amount": item["amount"],
                    "DetailType": item.get("detail_type", "SalesItemLineDetail"),
                    "Description": item.get('description'),
                    "SalesItemLineDetail": {
                        "ItemRef": {
                            "value": item.get('item_id')
                        }
                    }
                })
            invoice_data['Line'] = lines

        if 'customer_id' in kwargs:
            invoice_data['CustomerRef'] = {'value': kwargs['customer_id']}
        return await self.client._post('invoice', invoice_data)

    async def delete_invoice(self, invoice_id: str, sync_token: str) -> Dict[str, Any]:
        invoice_data = {
            "Id": invoice_id,
            "SyncToken": sync_token
        }
        return await self.client._post('invoice?operation=delete', invoice_data)

# Export tools
tools = [create_invoice_tool, get_invoice_tool, list_invoices_tool, update_invoice_tool, delete_invoice_tool]