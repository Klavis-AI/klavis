import requests
import logging
from .base import get_calcom_client

# Configure logging
logger = logging.getLogger(__name__)

def header():
    """Retrieve authentication headers for Cal.com API"""
    client = get_calcom_client()
    if not client:
        logger.error("Could not get Cal.com client")
        return None
    return {
        "Authorization": client
    }

async def cal_get_stripe_connect_url() -> dict:
    """
    Retrieve Stripe Connect URL from Cal.com API.

    Returns:
        dict: On success → parsed JSON response.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/stripe/connect"
    logger.info(f"Requesting Stripe Connect URL from {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info("Successfully retrieved Stripe Connect URL")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_save_stripe_credentials(state: str, code: str) -> dict:
    """
    Save Stripe credentials in Cal.com.

    Args:
        state (str): OAuth state parameter
        code (str): OAuth authorization code

    Returns:
        dict: On success → parsed JSON response.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/stripe/save"
    params = {"state": state, "code": code}
    logger.info(f"Saving Stripe credentials with state: {state}")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        logger.info("Successfully saved Stripe credentials")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to save credentials: {e}")
        return {"error": f"Failed to save credentials: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_check_stripe_connection() -> dict:
    """
    Check Stripe connection status in Cal.com.

    Returns:
        dict: On success → parsed JSON response.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/stripe/check"
    logger.info("Checking Stripe connection status")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info("Successfully checked Stripe connection")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection check failed: {e}")
        return {"error": f"Connection check failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}
