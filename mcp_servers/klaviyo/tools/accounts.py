from .base import _async_request



async def get_account_details() -> dict:
    """
    Retrieve details of the current authenticated Klaviyo account.

    Example natural language triggers:
    - "Show me my Klaviyo account details"
    - "Get account info"
    """
    return await _async_request("GET", "/accounts")
