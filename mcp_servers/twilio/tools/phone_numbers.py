from typing import Dict, Any
from .base import get_twilio_client

async def list_phone_numbers() -> Dict[str, Any]:
    """List phone numbers available in the Twilio account."""
    client = get_twilio_client()
    return await client.make_request("list_phone_numbers") 