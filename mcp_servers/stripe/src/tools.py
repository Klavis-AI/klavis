# stripe_server/tools.py
from mcp.types import Tool

def get_stripe_tools() -> list[Tool]:
    return [
        Tool(
            name="customer_create",
            description="Create a new customer in Stripe",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["email"]
            }
        ),
        Tool(
            name="customer_retrieve",
            description="Retrieve a customer's details",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="customer_update",
            description="Update customer information",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "update_fields": {
                        "type": "object",
                        "description": "Fields to update (email, name, metadata, etc.)"
                    }
                },
                "required": ["customer_id", "update_fields"]
            }
        ),
        Tool(
            name="payment_intent_create",
            description="Create a payment intent for processing payments",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "integer", "description": "Amount in cents"},
                    "currency": {"type": "string", "default": "usd"},
                    "payment_method_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["card"]
                    },
                    "customer": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["amount", "currency"]
            }
        ),
        Tool(
            name="charge_list",
            description="List recent charges",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "maximum": 100, "default": 10},
                    "customer_id": {"type": "string"}
                }
            }
        ),
        Tool(
            name="refund_create",
            description="Create a refund for a charge",
            inputSchema={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string"},
                    "amount": {"type": "integer", "description": "Amount in cents to refund"},
                    "reason": {
                        "type": "string",
                        "enum": ["duplicate", "fraudulent", "requested_by_customer"]
                    }
                },
                "required": ["charge_id"]
            }
        )
    ]