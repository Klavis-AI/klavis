from typing import Dict, Any
from .base import get_twilio_client

async def send_sms(to_number: str, body: str) -> Dict[str, Any]:
    """Send an SMS message using Twilio."""
    client = get_twilio_client()
    return await client.make_request("send_sms", to=to_number, body=body)

async def send_mms(to_number: str, media_url: str, body: str = "") -> Dict[str, Any]:
    """Send an MMS message with media using Twilio."""
    client = get_twilio_client()
    return await client.make_request("send_mms", to=to_number, media_url=media_url, body=body)

async def list_messages(limit: int = 20) -> Dict[str, Any]:
    """List recent messages from Twilio account."""
    client = get_twilio_client()
    return await client.make_request("list_messages", limit=limit)

async def get_message_details(message_sid: str) -> Dict[str, Any]:
    """Get detailed information about a specific message."""
    client = get_twilio_client()
    return await client.make_request("get_message_details", sid=message_sid)

async def redact_message(message_sid: str) -> Dict[str, Any]:
    """Redact (clear the body of) a message in Twilio."""
    client = get_twilio_client()
    return await client.make_request("redact_message", sid=message_sid) 