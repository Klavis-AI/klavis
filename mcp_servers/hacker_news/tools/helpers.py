import httpx
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

base_url = 'https://hacker-news.firebaseio.com/v0'
async def hackerNews_item(item_id: int) -> dict:
    """Fetch a Hacker News item by its numeric item_id.

    Args:
        item_id (int): Required. The item's unique item_identifier (e.g., `8863`).
    """
    url = f"{base_url}/item/{item_id}.json"
    logger.info(f"Requesting item {item_id} from {url}")
    try:
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item {item_id}")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
        logger.error(f"Could not get item {item_id}: {e}")
        return {"error": f"An error occurred while requesting {e.request.url!r}."}
    except Exception as e:
        logger.error(f"Unexpected error when fetching item {item_id}: {e}")
        return json.dumps({"error": str(e)})

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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
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
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
        logger.error(f"Could not get beststories: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error when fetching beststories: {e}")
        return {"error": str(e)}
