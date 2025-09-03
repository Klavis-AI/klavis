import logging
import os
from contextvars import ContextVar
from twilio.rest import Client
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Context variable to store the auth token for each request
auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    """Get the authentication token from context."""
    try:
        token = auth_token_context.get()
        if not token:
            # Fallback to environment variable if no token in context
            token = os.getenv("TWILIO_AUTH_TOKEN")
            if not token:
                raise RuntimeError("No authentication token available")
        return token
    except LookupError:
        token = os.getenv("TWILIO_AUTH_TOKEN")
        if not token:
            raise RuntimeError("Authentication token not found in request context or environment")
        return token

def get_account_sid() -> str:
    """Get the Twilio Account SID from environment."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    if not account_sid:
        raise RuntimeError("TWILIO_ACCOUNT_SID not found in environment variables")
    return account_sid

def get_twilio_client() -> Optional[Client]:
    """Create and return a Twilio client instance."""
    try:
        account_sid = get_account_sid()
        auth_token = get_auth_token()
        
        logger.debug(f"Creating Twilio client with Account SID: {account_sid}")
        client = Client(account_sid, auth_token)
        return client
    except Exception as e:
        logger.error(f"Failed to create Twilio client: {e}")
        raise e

def validate_phone_number(phone_number: str) -> str:
    """Validate and format phone number to E.164 format."""
    if not phone_number:
        raise ValueError("Phone number cannot be empty")
    
    # Remove spaces, dashes, parentheses
    cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Add + prefix if not present and number starts with country code
    if not cleaned.startswith('+'):
        if cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = '+' + cleaned
        elif len(cleaned) == 10:
            cleaned = '+1' + cleaned
        else:
            raise ValueError(f"Invalid phone number format: {phone_number}")
    
    return cleaned