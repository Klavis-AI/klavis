import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

base_url = 'https://hacker-news.firebaseio.com/v0'


async def hackerNews_topstories_ids() -> list:
    """
    Fetch top story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/topstories.json"
    logger.info(f"Requesting topstories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched topstories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get topstories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching topstories: {e}")
        return {"error": str(e)}


async def hackerNews_newstories_ids() -> list:
    """
    Fetch new story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/newstories.json"
    logger.info(f"Requesting newstories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched newstories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get newstories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching newstories: {e}")
        return {"error": str(e)}


async def hackerNews_askstories_ids() -> list:
    """
    Fetch ask story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/askstories.json"
    logger.info(f"Requesting askstories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched askstories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get askstories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching askstories: {e}")
        return {"error": str(e)}


async def hackerNews_showstories_ids() -> list:
    """
    Fetch show story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/showstories.json"
    logger.info(f"Requesting showstories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched showstories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get showstories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching showstories: {e}")
        return {"error": str(e)}


async def hackerNews_jobstories_ids() -> list:
    """
    Fetch job story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/jobstories.json"
    logger.info(f"Requesting jobstories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched jobstories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get jobstories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching jobstories: {e}")
        return {"error": str(e)}


async def hackerNews_updates_ids() -> dict:
    """
    Fetch updates (new items and profiles) from Hacker News.

    Returns:
        dict: Update JSON on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/updates.json"
    logger.info(f"Requesting updates from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched updates")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get updates: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching updates: {e}")
        return {"error": str(e)}


async def hackerNews_beststories_ids() -> list:
    """
    Fetch best story IDs from Hacker News.

    Returns:
        list: List of IDs on success,
              or {"error": "..."} on failure.
    """
    url = f"{base_url}/beststories.json"
    logger.info(f"Requesting beststories from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched beststories IDs")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get beststories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching beststories: {e}")
        return {"error": str(e)}
