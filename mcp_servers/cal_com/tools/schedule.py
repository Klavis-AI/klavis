import httpx
import json
import logging
from .base import get_calcom_client


# Configure logging
logger = logging.getLogger(__name__)


def header():
    client = get_calcom_client()
    if not client:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}
    value = {
    "Authorization": client,
    "cal-api-version": "2024-06-11"
    }

    return value



async def cal_get_all_schedules() -> dict:
    """
    Retrieve all schedules from Cal.com API.

    Returns:
        dict: On success → parsed JSON response from Cal.com API.
              On failure → dict with "error" key and message.
    """
    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    url = "https://api.cal.com/v2/schedules/"
    logging.info(f"Requesting Cal.com schedules from {url}")

    try:
        # Use an async context manager to handle the client's lifecycle
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            # This checks for HTTP error statuses (e.g., 404, 500)
            response.raise_for_status()
            logging.info("Successfully retrieved Cal.com schedules")
            return response.json()
    except httpx.RequestError as e:
        logging.error(f"Could not get Cal.com schedules from {url}: {e}")
        return {"error": f"Could not get Cal.com schedules from {url}"}
    except Exception as e:
        logging.error(f"Unexpected error when fetching Cal.com schedules: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_create_a_schedule(
    name: str,
    timeZone: str,
    isDefault: bool,
    availability: list = None,
    overrides: list = None
) -> dict:
    """
    Create a new schedule in Cal.com.

    Args:
        name (str): Schedule name.
        timeZone (str): Time zone string (e.g., "America/New_York").
        isDefault (bool): Whether this should be the default schedule.
        availability (list, optional): List of availability blocks. Each block is a dict:
            {
                "days": ["Monday", "Tuesday", ...],  # Days must start with a capital letter
                "startTime": "09:00",                # Time format: "HH:mm"
                "endTime": "17:00"
            }
        overrides (list, optional): List of overrides for specific dates. Each override is a dict:
            {
                "date": "YYYY-MM-DD",
                "startTime": "10:00",                # Time format: "HH:mm"
                "endTime": "12:00"
            }

    Returns:
        dict: If successful, parsed JSON response from Cal.com.
              If failed, dict with "error" key and message.
    """

    url = "https://api.cal.com/v2/schedules/"
    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    payload = {
        "name": name,
        "timeZone": timeZone,
        "isDefault": isDefault,
    }

    if availability:
        payload["availability"] = availability
    if overrides:
        payload["overrides"] = overrides

    logging.info(f"Creating Cal.com schedule: {name}")

    try:
        # Use an async context manager for the client
        async with httpx.AsyncClient() as client:
            # The 'json' parameter works the same as in requests
            response = await client.post(url, json=payload, headers=headers)
            # Check for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()
            logging.info("Successfully created Cal.com schedule")
            return response.json()

    except httpx.RequestError as e:
        logging.error(f"Could not create Cal.com schedule: {e}")
        return {"error": f"Could not create Cal.com schedule: {e}"}
    except Exception as e:
        logging.error(f"Unexpected error when creating Cal.com schedule: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_update_a_schedule(
    schedule_id: int,
    name: str = None,
    timeZone: str = None,
    isDefault: bool = None,
    availability: list = None,
    overrides: list = None
) -> dict:
    """
    Update an existing schedule in Cal.com.

    Args:
        schedule_id (int): ID of the schedule to update (required).
        name (str, optional): New schedule name.
        timeZone (str, optional): New time zone string (e.g., "America/New_York").
        isDefault (bool, optional): Set as default schedule.
        availability (list, optional): List of availability blocks. Each block is a dict:
            {
                "days": ["Monday", "Tuesday", ...],  # Days must start with a capital letter
                "startTime": "09:00",                # Time format: "HH:mm"
                "endTime": "17:00"
            }
        overrides (list, optional): List of overrides for specific dates. Each override is a dict:
            {
                "date": "YYYY-MM-DD",
                "startTime": "10:00",                # Time format: "HH:mm"
                "endTime": "12:00"
            }

    Returns:
        dict: If successful, parsed JSON response from Cal.com.
              If failed, dict with "error" key and message.
    """

    url = "https://api.cal.com/v2/schedules/"
    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    if not schedule_id:
        logging.error("Missing required: schedule_id")
        return {"error": "Missing required: schedule_id"}

    url_new = url + str(schedule_id)
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    payload = {}

    if name is not None:
        payload["name"] = name
    if timeZone is not None:
        payload["timeZone"] = timeZone
    if isDefault is not None:
        payload["isDefault"] = isDefault
    if availability:
        payload["availability"] = availability
    if overrides:
        payload["overrides"] = overrides

    logging.info(f"Updating Cal.com schedule ID: {schedule_id}")

    try:
        # Use an async context manager for the client
        async with httpx.AsyncClient() as client:
            # Make an async PATCH request
            response = await client.patch(url_new, json=payload, headers=headers)

            # Check for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()

            logging.info("Successfully updated Cal.com schedule")
            return response.json()

    except httpx.RequestError as e:
        # Catch httpx-specific request errors
        logging.error(f"Could not update Cal.com schedule: {e}")
        return {"error": f"Could not update Cal.com schedule: {e}"}

    except Exception as e:
        # A general catch-all for any other errors
        logging.error(f"Unexpected error when updating Cal.com schedule: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_get_default_schedule() -> dict:
    """
    Get the default schedule from Cal.com.

    Returns:
        dict: If successful, parsed JSON response from Cal.com.
              If failed, dict with "error" key and message.
    """

    url = "https://api.cal.com/v2/schedules/"
    url_new = url + "default"

    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    logging.info("Fetching default schedule from Cal.com")

    try:
        # Use an async context manager for the client
        async with httpx.AsyncClient() as client:
            # Make an async GET request
            response = await client.get(url_new, headers=headers)

            # Check for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()

            logging.info("Successfully fetched default schedule")
            return response.json()

    except httpx.RequestError as e:
        # Catch httpx-specific request errors
        logging.error(f"Could not get default schedule: {e}")
        return {"error": f"Could not get default schedule: {e}"}

    except Exception as e:
        # A general catch-all for any other errors
        logging.error(f"Unexpected error when getting default schedule: {e}")
        return {"error": "Unexpected error occurred"}


async def cal_get_schedule(schedule_id: int) -> dict:
    """
    Get a specific schedule from Cal.com by its ID.

    Args:
        schedule_id (int): ID of the schedule to fetch.

    Returns:
        dict: If successful, parsed JSON response from Cal.com.
              If failed, dict with "error" key and message.
    """

    url = "https://api.cal.com/v2/schedules/"
    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    if not schedule_id:
        logging.error("Missing required: schedule_id")
        return {"error": "Missing required: schedule_id"}

    url_new = url + str(schedule_id)
    logging.info(f"Fetching Cal.com schedule ID: {schedule_id}")

    try:
        # Use an async context manager for the client
        async with httpx.AsyncClient() as client:
            # Make an async GET request
            response = await client.get(url_new, headers=headers)

            # Check for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()

            logging.info("Successfully fetched schedule")
            return response.json()

    except httpx.RequestError as e:
        # Catch httpx-specific request errors
        logging.error(f"Could not get schedule: {e}")
        return {"error": f"Could not get schedule: {e}"}

    except Exception as e:
        # A general catch-all for any other errors
        logging.error(f"Unexpected error when getting schedule: {e}")
        return {"error": "Unexpected error occurred"}

async def cal_delete_a_schedule(schedule_id: int) -> dict:
    """
    Delete a schedule in Cal.com by its ID.

    Args:
        schedule_id (int): ID of the schedule to delete.

    Returns:
        dict: If successful, parsed JSON response from Cal.com.
              If failed, dict with "error" key and message.
    """

    url = "https://api.cal.com/v2/schedules/"
    headers = header()
    if not headers:
        logging.error("Could not get Cal.com client")
        return {"error": "Could not get Cal.com client"}

    if not schedule_id:
        logging.error("Missing required: schedule_id")
        return {"error": "Missing required: schedule_id"}

    url_new = url + str(schedule_id)

    logging.info(f"Deleting Cal.com schedule ID: {schedule_id}")

    try:
        # Use an async context manager for the client
        async with httpx.AsyncClient() as client:
            # Make an async DELETE request
            response = await client.delete(url_new, headers=headers)

            # Check for HTTP errors (e.g., 4xx or 5xx responses)
            response.raise_for_status()

            logging.info("Successfully deleted schedule")
            return response.json()

    except httpx.RequestError as e:
        # Catch httpx-specific request errors
        logging.error(f"Could not delete schedule: {e}")
        return {"error": f"Could not delete schedule: {e}"}

    except Exception as e:
        # A general catch-all for any other errors
        logging.error(f"Unexpected error when deleting schedule: {e}")
        return {"error": "Unexpected error occurred"}