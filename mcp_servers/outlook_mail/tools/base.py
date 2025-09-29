import logging
import os
import json
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

auth_token_context: ContextVar[str] = ContextVar('auth_token')

def get_auth_token() -> str:
    try:
        token = auth_token_context.get()
        if token:
            return token
    except LookupError:
        pass
    
    # Fallback to AUTH_DATA environment variable
    auth_data = os.getenv("AUTH_DATA")
    if auth_data:
        try:
            auth_json = json.loads(auth_data)
            access_token = auth_json.get('access_token', '')
            if access_token:
                return access_token
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse AUTH_DATA JSON: {e}")
    
    # Legacy fallback to OUTLOOK_ACCESS_TOKEN
    token = os.getenv("OUTLOOK_ACCESS_TOKEN")
    if token:
        return token
    
    raise RuntimeError("Authentication token not found in context or environment")

def get_outlookMail_client() -> Optional[dict]:
    """
    Return a simple client dict with base_url and headers.
    """
    try:
        auth_token = get_auth_token()
        client = {
            "base_url": "https://graph.microsoft.com/v1.0",
            "headers": {'Authorization': f"Bearer {auth_token}"}
        }
        return client
    except RuntimeError as e:
        logger.warning(f"Failed to get auth token: {e}")
        return None

if __name__ == '__main__':
    print(get_outlookMail_client())