import logging
import os

from contextvars import ContextVar
from typing import Any, Dict, List, Optional

import aiohttp

from coinbase import jwt_generator
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

logger = logging.getLogger(__name__)


class CoinbaseValidationError(Exception):
    """Custom exception for Airtable 422 validation errors."""

    pass


# Context variable to store the auth token per request
auth_token_context: ContextVar[str] = ContextVar('auth_token')


def get_auth_token() -> str:
    """
    Get the Coinbase API token from context or fallback to env.
    """
    try:
        token = auth_token_context.get()

        if not token:
            # Fallback to environment variable
            token = os.getenv("COINBASE_API_KEY")

            if not token:
                raise RuntimeError(
                    "No Coinbase auth token found in context or environment"
                )

        return token
    except LookupError:
        # Context variable not set at all
        token = os.getenv("COINBASE_API_KEY")

        if not token:
            raise RuntimeError(
                "No Coinbase auth token found in context or environment"
            )

        return token


def generate_jwt_token(request_method: str, request_path: str) -> str:
    """
    Generate JWT token for Coinbase API authentication using coinbase-advanced-py.
    JWT tokens expire after 2 minutes and must be generated for each unique API request.
    """
    try:
        api_key = get_auth_token()
        api_secret = os.getenv("COINBASE_API_SECRET")

        if not api_secret:
            raise RuntimeError("No Coinbase API secret found")

        # Generate JWT token using coinbase-advanced-py library
        jwt_uri = jwt_generator.format_jwt_uri(request_method, request_path)

        jwt_token = jwt_generator.build_rest_jwt(
            jwt_uri,
            api_key,
            api_secret
        )

        return jwt_token

    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        raise CoinbaseValidationError(
            f"Failed to generate JWT token: {e}. Check your API key signature algorithm is ECDSA."
        )


def _get_coinbase_headers(request_method: str, request_path: str) -> Dict[str, str]:
    """
    Get headers with JWT authentication for Coinbase API.
    Generates a fresh JWT token for each request as required by Coinbase.
    """
    try:
        jwt_token = generate_jwt_token(request_method, request_path)

        return {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    except CoinbaseValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to generate authenticated headers: {e}")
        raise e


def get_coinbase_config() -> Optional[Dict[str, str]]:
    """
    Return a Coinbase client config ready to use.
    """
    try:
        base_url = os.getenv("COINBASE_API_BASE_URL")
        exchange_url = os.getenv("COINBASE_EXCHANGE_URL")

        if not base_url or not exchange_url:
            raise RuntimeError(
                "Missing Coinbase configuration: You need to set COINBASE_API_BASE_URL and COINBASE_EXCHANGE_URL environment variables."
            )

        return {
            "base_url": base_url,
            "exchange_url": exchange_url
        }
    except Exception as e:
        logger.error(f"Failed to initialize Coinbase config: {e}")
        raise RuntimeError(f"Failed to initialize Coinbase config: {e}")


async def make_coinbase_request(
    method: str,
    endpoint: str,
    require_auth: bool = True,
    query_params: Optional[List[str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make a centralized Coinbase API request with proper authentication and error handling.
    Rate limiting is automatically applied via decorator.

    Args:
        method (str): HTTP method (GET, POST, PUT, DELETE)
        endpoint (str): API endpoint path (e.g., "/v2/accounts") - used for JWT generation
        require_auth (bool): Whether to include JWT authentication (default: True)
        query_params (Optional[List[str]]): List of query parameter strings (e.g., ["limit=5", "before=cursor"])
        json_data (Optional[Dict]): JSON data for POST/PUT requests
        base_url (Optional[str]): Custom base URL to use instead of default (default: None)

    Returns:
        Dict[str, Any]: API response or error dict
    """
    try:
        config = get_coinbase_config()

        # Set up headers based on authentication requirement
        if require_auth:
            # Generate authenticated headers using the base endpoint
            headers = _get_coinbase_headers(method, endpoint)
        else:
            # Public endpoint - no authentication needed
            headers = {"Content-Type": "application/json"}

        # Build full URL
        if query_params:
            endpoint += "?" + "&".join(query_params)

        # Choose the appropriate base URL
        if base_url:
            # Use custom base URL
            url = f"{base_url}{endpoint}"
        else:
            # Use default base URL from config
            url = f"{config['base_url']}{endpoint}"

        logger.info(f"Request: {method} {url}")

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.request(method, url, json=json_data) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                logger.error(
                    f"Coinbase API request failed: {e.status} {e.message} for {method} {url}"
                )
                return {"error": f"API request failed: {str(e)}"}
            except Exception as e:
                logger.error(
                    f"Unexpected error occurred during Coinbase API request: {e}"
                )
                return {"error": f"Unexpected error: {str(e)}"}
    except CoinbaseValidationError as e:
        raise e
    except aiohttp.ClientResponseError as e:
        logger.error(
            f"Coinbase API request failed: {e.status} {e.message} for {method} {url}"
        )
        raise RuntimeError(
            f"Coinbase API Error ({e.status}): {e.message}"
        ) from e
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during Coinbase API request: {e}"
        )
        raise RuntimeError(
            f"Unexpected error during API call to {method} {url}"
        ) from e
