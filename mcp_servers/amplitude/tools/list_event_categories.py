import os
import requests
from dotenv import load_dotenv
import logging


# Load credentials
load_dotenv()
API_KEY = os.getenv("AMPLITUDE_API_KEY")
API_SECRET = os.getenv("AMPLITUDE_API_SECRET")
CATEGORY_ENDPOINT = "https://amplitude.com/api/2/taxonomy/category"


def list_event_categories() -> list:
    """
    Lists all event categories defined in Amplitude taxonomy.

    Returns:
      List of category objects with id and name.
    """
    logger = logging.getLogger("amplitude_mcp")
    logger.info("TOOL_CALL list_event_categories")
    
    resp = requests.get(CATEGORY_ENDPOINT, auth=(API_KEY, API_SECRET))
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data