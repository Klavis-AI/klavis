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


async def cal_request_email_verification_code(email: str) -> dict:
    """
    Request email verification code from Cal.com API.

    Args:
        email (str): Email address to verify

    Returns:
        dict: API response or error message
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/emails/verification-code/request"
    payload = {"email": email}

    logger.info(f"Requesting email verification code for {email}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully requested email verification code")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Email verification request failed: {e}")
        return {"error": f"Email verification request failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}


async def cal_verify_email_code(email: str, code: int) -> dict:
    """
    Verify email with received code.

    Args:
        email (str): Email address to verify
        code (int): Verification code received

    Returns:
        dict: API response or error message
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/emails/verification-code/verify"
    payload = {
        "email": str(email),
        "code": str(code)
    }

    logger.info(f"Verifying email {email} with code")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully verified email")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Email verification failed: {e}")
        return {"error": f"Email verification failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_get_verified_emails() -> dict:
    """
    Retrieve all verified emails from Cal.com API.

    Returns:
        dict: On success → parsed JSON response containing verified emails.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        logger.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/emails"
    logger.info("Requesting list of verified emails from Cal.com")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises exception for HTTP errors
        logger.info("Successfully retrieved verified emails")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get verified emails: {e}")
        return {"error": f"Failed to get verified emails: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error when fetching verified emails: {e}")
        return {"error": "Unexpected error occurred"}
async def cal_get_verified_email_by_id(email_id: int) -> dict:
    """
    Retrieve a specific verified email by its ID from Cal.com API.

    Args:
        email_id (int): The ID of the verified email to retrieve

    Returns:
        dict: On success → parsed JSON response containing the email details.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        logger.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    url = f"https://api.cal.com/v2/verified-resources/emails/{email_id}"
    logger.info(f"Requesting verified email with ID: {email_id}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully retrieved verified email ID {email_id}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logger.error(f"Verified email not found with ID: {email_id}")
            return {"error": f"Verified email not found with ID: {email_id}"}
        logger.error(f"HTTP error getting verified email: {e}")
        return {"error": f"HTTP error getting verified email: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for verified email ID {email_id}: {e}")
        return {"error": f"Request failed: {str(e)}"}
    except ValueError as e:
        logger.error(f"Invalid JSON response for email ID {email_id}: {e}")
        return {"error": "Invalid response format from server"}
    except Exception as e:
        logger.exception(f"Unexpected error getting email ID {email_id}: {e}")
        return {"error": "Unexpected error occurred"}



#Phone No. Not Working even on Main site, Maybe problem with Indian No, Don't know!
async def cal_request_phone_verification_code(phone: str) -> dict:
    """
    Request phone verification code from Cal.com API.

    Args:
        phone (str): Phone number to verify

    Returns:
        dict: API response or error message
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/phones/verification-code/request"
    payload = {"phone": str(phone)}

    logger.info(f"Requesting phone verification code for {phone}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully requested phone verification code")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Phone verification request failed: {e}")
        return {"error": f"Phone verification request failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}


async def cal_verify_phone_code(phone: str, code: int) -> dict:
    """
    Verify phone with received code.

    Args:
        phone (str): Phone number to verify
        code (int): Verification code received

    Returns:
        dict: API response or error message
    """
    headers = header()
    if not headers:
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/phones/verification-code/verify"
    payload = {"phone": str(phone), "code": str(code)}

    logger.info(f"Verifying phone {phone} with code")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully verified phone")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Phone verification failed: {e}")
        return {"error": f"Phone verification failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"error": "Unexpected error occurred"}


async def cal_get_verified_phones(take: int = 250, skip: int = None) -> dict:
    """
    Retrieve verified phone numbers from Cal.com API with pagination support.

    Args:
        take (int): Number of records to return (default: 250, max: 250)
        skip (int): Number of records to skip for pagination (optional)

    Returns:
        dict: On success → parsed JSON response containing verified phones.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        logger.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/verified-resources/phones"
    params = {"take": take}

    if skip is not None:
        params["skip"] = skip

    logger.info(f"Requesting verified phones (take: {take}, skip: {skip})")

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        logger.info(f"Successfully retrieved {take} verified phone records")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get verified phones: {e}")
        return {"error": f"Failed to get verified phones: {str(e)}"}
    except ValueError as e:
        logger.error(f"Invalid response format: {e}")
        return {"error": "Invalid response format from server"}
    except Exception as e:
        logger.exception(f"Unexpected error when fetching verified phones: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_get_verified_phone_by_id(phone_id: int) -> dict:
    """
    Retrieve a specific verified phone number by its ID from Cal.com API.

    Args:
        phone_id (int): The ID of the verified phone number to retrieve

    Returns:
        dict: On success → parsed JSON response containing the phone details.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        logger.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    url = f"https://api.cal.com/v2/verified-resources/phones/{phone_id}"
    logger.info(f"Requesting verified phone with ID: {phone_id}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Successfully retrieved verified phone ID {phone_id}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logger.error(f"Verified phone not found with ID: {phone_id}")
            return {"error": f"Verified phone not found with ID: {phone_id}"}
        logger.error(f"HTTP error getting verified phone: {e}")
        return {"error": f"HTTP error getting verified phone: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for verified phone ID {phone_id}: {e}")
        return {"error": f"Request failed: {str(e)}"}
    except ValueError as e:
        logger.error(f"Invalid JSON response for phone ID {phone_id}: {e}")
        return {"error": "Invalid response format from server"}
    except Exception as e:
        logger.exception(f"Unexpected error getting phone ID {phone_id}: {e}")
        return {"error": "Unexpected error occurred"}