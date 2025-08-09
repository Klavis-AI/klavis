import logging

from typing import Any, Dict, List

from .base import make_coinbase_request
from utils.rate_limiter import rate_limited

# Configure logging
logger = logging.getLogger(__name__)


@rate_limited(api_type="market_data")
async def coinbase_get_prices(symbols: List[str]) -> Dict[str, Any]:
    """
    Get current prices for cryptocurrencies.
    Uses higher rate limits for market data endpoints.

    Args:
        symbols (List[str]): List of cryptocurrency symbols (e.g., ['BTC-USD', 'ETH-USD']). 
    Returns:
        dict: JSON response with current prices.
    """
    # Get prices for specific symbols
    prices_data = []

    for symbol in symbols:
        try:
            endpoint = f"/v2/prices/{symbol}/spot"

            result = await make_coinbase_request(
                method="GET",
                endpoint=endpoint,
                require_auth=False
            )

            if "error" in result:
                prices_data.append(
                    {"error": f"Could not get price for {symbol}: {result['error']}"}
                )
            else:
                prices_data.append(result)
        except Exception as e:
            logger.error(f"Coinbase price request failed for {symbol}: {e}")
            prices_data.append(
                {"error": f"Could not get price for {symbol}: {str(e)}"}
            )

    return {"data": prices_data}


@rate_limited(api_type="market_data")
async def coinbase_get_current_exchange_rate(symbols: List[str]) -> Dict[str, Any]:
    """
    Get current exchange rate for a cryptocurrencies.
    Uses higher rate limits for market data endpoints.

    Args:
        symbols (List[str]): List[str]): List of cryptocurrency symbols (e.g., ['BTC-USD', 'ETH-USD']). 
    Returns:
        dict: JSON response with current exchange rate.
    """
    # Get exchange rates for specific symbols
    exchange_rates_data = []

    for symbol in symbols:
        try:
            endpoint = "/v2/exchange-rates"
            query_params = [f"currency={symbol}"]

            result = await make_coinbase_request(
                method="GET",
                endpoint=endpoint,
                query_params=query_params,
                require_auth=False
            )

            if "error" in result:
                exchange_rates_data.append(
                    {"error": f"Could not get exchange rate for {symbol}: {result['error']}"}
                )
            else:
                exchange_rates_data.append(result)

        except Exception as e:
            logger.error(
                f"Coinbase exchange rate request failed for {symbol}: {e}"
            )
            exchange_rates_data.append(
                {"error": f"Could not get exchange rate for {symbol}: {str(e)}"}
            )

    return {"data": exchange_rates_data}
