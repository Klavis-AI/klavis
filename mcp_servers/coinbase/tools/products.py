import logging
import os

from typing import Any, Dict, Optional

from .base import make_coinbase_request
from utils.rate_limiter import rate_limited

# Configure logging
logger = logging.getLogger(__name__)

EXCHANGE_URL = os.getenv("COINBASE_EXCHANGE_URL")


@rate_limited(api_type="products")
async def coinbase_get_product_details(product_id: str) -> Dict[str, Any]:
    """
    Get detailed product information.
    Uses moderate rate limits for product information endpoints.

    Args:
        product_id (str): The product ID (e.g., 'BTC-USD').
    Returns:
        dict: JSON response with detailed product information.
    """
    try:
        # Check if exchange URL is configured
        if not EXCHANGE_URL:
            return {"error": "Exchange URL not configured"}

        # Use centralized request function with custom base URL (no auth required)
        result = await make_coinbase_request(
            method="GET",
            endpoint=f"/products/{product_id}",
            require_auth=False,
            base_url=EXCHANGE_URL
        )

        return result

    except Exception as e:
        logger.error(f"Coinbase product details request failed: {e}")
        return {
            "error": f"Could not get Coinbase product details for {product_id}: {str(e)}"
        }


@rate_limited(api_type="products")
async def coinbase_get_historical_prices(
    symbol: str,
    start: str,
    end: str,
    granularity: Optional[int] = 3600
) -> Dict[str, Any]:
    """
    Get historical price data for cryptocurrencies.
    Uses moderate rate limits for product information endpoints.

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC-USD').
        start (str): Start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z').
        end (str): End time in ISO 8601 format (e.g., '2024-12-31T23:59:59Z').
        granularity (int): Candle granularity in seconds. Options: 60, 300, 900, 3600, 21600, 86400.
    Returns:
        dict: JSON response with historical price data.
    """
    try:
        # Check if exchange URL is configured
        if not EXCHANGE_URL:
            return {"error": "Exchange URL not configured"}

        # Build query parameters
        params = [
            f"start={start}",
            f"end={end}",
            f"granularity={granularity}"
        ]

        # Use centralized request function with custom base URL (no auth required)
        result = await make_coinbase_request(
            method="GET",
            endpoint=f"/products/{symbol}/candles",
            query_params=params,
            require_auth=False,
            base_url=EXCHANGE_URL
        )

        return result

    except Exception as e:
        logger.error(f"Coinbase historical prices request failed: {e}")
        return {
            "error": f"Could not get Coinbase historical prices for {symbol}: {str(e)}"
        }
