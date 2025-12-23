import contextvars
import os

auth_token_context = contextvars.ContextVar('auth_token', default='')

def get_serpapi_key() -> str:
    """
    Get SerpApi key from environment or context.
    
    Returns:
        str: The API key or empty string if not found
    """
    # First try to get from context (for request-specific auth)
    token = auth_token_context.get('')
    if token:
        return token
    
    # Fall back to environment variable
    return os.getenv('SERPAPI_API_KEY', '')