from typing import Any, Dict, List
from datetime import datetime

from mcp.types import Tool
from quickbooks.objects import Payment

# MCP Tool definitions
list_payments_tool = Tool(
    name="list_payments",
    description="List all payments from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 100},
            "customer_id": {"type": "string", "description": "Filter payments by customer ID"}
        },
        "additionalProperties": False
    }
)

get_payment_tool = Tool(
    name="get_payment",
    description="Get a specific payment by ID from QuickBooks",
    inputSchema={
        "type": "object",
        "properties": {
            "payment_id": {"type": "string", "description": "The QuickBooks payment ID"}
        },
        "required": ["payment_id"],
        "additionalProperties": False
    }
)

# Tool implementations
async def list_payments(max_results: int = 100, customer_id: str = None, client=None) -> List[Dict[str, Any]]:
    """List payments from QuickBooks."""
    if not client or not client.is_configured():
        raise ValueError("QuickBooks client not configured")
    
    try:
        payments = Payment.all(qb=client.client, max_results=max_results)
        
        if customer_id:
            payments = [p for p in payments if p.CustomerRef.get("value") == customer_id]
        
        return [
            {
                "id": payment.Id,
                "total_amount": float(payment.TotalAmt or 0.0),
                "customer_id": payment.CustomerRef.get("value") if payment.CustomerRef else None,
                "customer_name": payment.CustomerRef.get("name") if payment.CustomerRef else None,
                "payment_date": payment.TxnDate,
                "payment_method": payment.PaymentMethodRef.get("value") if payment.PaymentMethodRef else None,
                "memo": payment.PrivateNote,
                "status": payment.PaymentStatus
            }
            for payment in payments
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list payments: {str(e)}")

async def get_payment(payment_id: str, client=None) -> Dict[str, Any]:
    """Get a specific payment from QuickBooks."""
    if not client or not client.is_configured():
        raise ValueError("QuickBooks client not configured")
    
    try:
        payment = Payment.get(payment_id, qb=client.client)
        
        return {
            "id": payment.Id,
            "total_amount": float(payment.TotalAmt or 0.0),
            "customer_id": payment.CustomerRef.get("value") if payment.CustomerRef else None,
            "customer_name": payment.CustomerRef.get("name") if payment.CustomerRef else None,
            "payment_date": payment.TxnDate,
            "payment_method": payment.PaymentMethodRef.get("value") if payment.PaymentMethodRef else None,
            "memo": payment.PrivateNote,
            "status": payment.PaymentStatus,
            "unapplied_amount": float(payment.UnappliedAmt or 0.0)
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get payment {payment_id}: {str(e)}")

# Export tools and implementations
tools = [list_payments_tool, get_payment_tool]
tool_map = {
    "list_payments": list_payments,
    "get_payment": get_payment
}