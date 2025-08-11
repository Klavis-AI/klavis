import logging

from typing import Any, Dict, Optional

from .base import make_coinbase_request
from utils.rate_limiter import rate_limited

# Configure logging
logger = logging.getLogger(__name__)


@rate_limited(api_type="accounts")
async def coinbase_get_accounts() -> Dict[str, Any]:
    """
    List user's cryptocurrency accounts.
    Uses conservative rate limits for authenticated account endpoints.

    Requires Coinbase API authentication.
    Returns:
        dict: JSON response with user accounts.
    """
    endpoint = "/v2/accounts"
    return await make_coinbase_request(method="GET", endpoint=endpoint)


@rate_limited(api_type="accounts")
async def coinbase_get_account_balance(account_id: str) -> Dict[str, Any]:
    """
    Get balance for a specific account.
    Uses conservative rate limits for authenticated account endpoints.

    Args:
        account_id (str): The account ID to get balance for.
    Returns:
        dict: JSON response with account balance.
    """
    endpoint = f"/v2/accounts/{account_id}"

    return await make_coinbase_request(method="GET", endpoint=endpoint)


@rate_limited(api_type="accounts")
async def coinbase_get_transactions(
    account_id: str,
    limit: Optional[int] = 25,
    before: Optional[str] = None,
    after: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get transaction history for an account.
    Uses conservative rate limits for authenticated account endpoints.

    Args:
        account_id (str): The account ID to get transactions for.
        limit (int): Number of transactions to return (max 100, default 25).
        before (str): Optional. Return transactions before this cursor.
        after (str): Optional. Return transactions after this cursor.
    Returns:
        dict: JSON response with transaction history.
    """
    # Base endpoint for JWT token generation (without query params)
    endpoint = f"/v2/accounts/{account_id}/transactions"

    # Build query parameters list
    params = []
    if limit:
        params.append(f"limit={limit}")
    if before:
        params.append(f"before={before}")
    if after:
        params.append(f"after={after}")

    return await make_coinbase_request(
        method="GET",
        endpoint=endpoint,
        query_params=params
    )


@rate_limited(api_type="accounts")
async def coinbase_get_portfolio_value() -> Dict[str, Any]:
    """
    Get total portfolio value across all accounts.
    Uses conservative rate limits for authenticated account endpoints.

    Requires Coinbase API authentication.
    Returns:
        dict: JSON response with portfolio value.
    """
    try:
        # First get all accounts
        accounts_response = await coinbase_get_accounts()
        if "error" in accounts_response:
            return accounts_response

        accounts = accounts_response.get("data", [])
        account_values = []

        for account in accounts:
            account_id = account.get("id")

            if account_id:
                balance_response = await coinbase_get_account_balance(account_id)

                if "error" not in balance_response:
                    balance_data = balance_response.get("data", {})
                    account_values.append({
                        "account_id": account_id,
                        "currency": account.get("currency"),
                        "balance": balance_data.get("balance"),
                    })

        return {
            "data": {
                "accounts": account_values,
                "total_accounts": len(accounts)
            }
        }
    except Exception as e:
        logger.error(
            f"Unexpected error in Coinbase portfolio value request: {e}"
        )
        return {
            "error": f"Unexpected error in Coinbase portfolio value request: {str(e)}"
        }
