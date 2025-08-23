import logging
import os
from typing import Any, Dict, Optional
from contextvars import ContextVar
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logger = logging.getLogger(__name__)

# Context variable to store the auth token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        return auth_token_context.get()
    except LookupError:
        raise RuntimeError("Authentication token not found in request context")

class TwilioClient:
    """Client for Twilio API using environment variables or auth token."""
    
    def __init__(self):
        """Initialize Twilio client with credentials."""
        auth_token = get_auth_token()
        
        if auth_token == "env":
            # Use environment variables
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, self.twilio_phone_number]):
                raise RuntimeError("Missing critical Twilio environment variables (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER)")
        else:
            # Parse auth token (assuming format: account_sid:auth_token:phone_number)
            try:
                parts = auth_token.split(':')
                if len(parts) != 3:
                    raise ValueError("Auth token must be in format: account_sid:auth_token:phone_number")
                
                account_sid, auth_token, self.twilio_phone_number = parts
            except ValueError as e:
                raise RuntimeError(f"Invalid auth token format: {e}")
        
        self.client = Client(account_sid, auth_token)
    
    async def make_request(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Make a request to Twilio API."""
        try:
            if operation == "send_sms":
                message = self.client.messages.create(
                    to=kwargs["to"],
                    from_=self.twilio_phone_number,
                    body=kwargs["body"]
                )
                return {"status": "Message sent successfully", "message_sid": message.sid}
            
            elif operation == "send_mms":
                message = self.client.messages.create(
                    to=kwargs["to"],
                    from_=self.twilio_phone_number,
                    body=kwargs.get("body", ""),
                    media_url=[kwargs["media_url"]]
                )
                return {"status": "MMS sent successfully", "message_sid": message.sid}
            
            elif operation == "list_messages":
                messages = self.client.messages.list(limit=kwargs.get("limit", 20))
                return {
                    "messages": [
                        {
                            "sid": msg.sid,
                            "from": msg.from_,
                            "to": msg.to,
                            "body": msg.body,
                            "status": msg.status
                        } for msg in messages
                    ]
                }
            
            elif operation == "get_message_details":
                msg = self.client.messages(kwargs["sid"]).fetch()
                return {
                    "sid": msg.sid,
                    "from": msg.from_,
                    "to": msg.to,
                    "body": msg.body,
                    "status": msg.status,
                    "error_message": msg.error_message
                }
            
            elif operation == "redact_message":
                message = self.client.messages(kwargs["sid"]).update(body="")
                return {"status": "Message redacted successfully", "message_sid": message.sid}
            
            elif operation == "list_phone_numbers":
                numbers = self.client.incoming_phone_numbers.list(limit=20)
                return {
                    "phone_numbers": [
                        {
                            "phone_number": num.phone_number,
                            "sid": num.sid,
                            "capabilities": num.capabilities
                        } for num in numbers
                    ]
                }
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except TwilioRestException as e:
            logger.error(f"Twilio API Error: {e.msg}")
            raise RuntimeError(f"Twilio API Error: {e.msg}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Unexpected error: {str(e)}") from e

# Global client instance
_twilio_client: Optional[TwilioClient] = None

def get_twilio_client() -> TwilioClient:
    """Get or create Twilio client instance."""
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = TwilioClient()
    return _twilio_client 