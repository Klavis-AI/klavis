import requests
import logging
import json

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

base_url = 'https://hacker-news.firebaseio.com/v0'


async def hackerNews_item(item_id: int) -> str:
    """Fetch a Hacker News item by its numeric item_id.

    Args:
        item_id (int): Required. The item's unique item_identifier (e.g., `8863`).
    """
    url = f"{base_url}/item/{item_id}.json"
    logger.info(f"Requesting item {item_id} from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info(f"Successfully fetched item {item_id}")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get item {item_id}: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error when fetching item {item_id}: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_user(username: str) -> str:
    """Fetch a Hacker News user by username.

    Args:
        username (str): Required. The user's unique username (e.g., `'pg'`).
    """
    url = f"{base_url}/user/{username}.json"
    logger.info(f"Requesting user {username} from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info(f"Successfully fetched user {username}")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get user {username}: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error when fetching user {username}: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_maxitem() -> str:
    """Fetch the current largest item ID on Hacker News.
    """
    url = f"{base_url}/maxitem.json"
    logger.info(f"Requesting maxitem from {url}")
    try:
        result = requests.get(url)
        result.raise_for_status()
        logger.info("Successfully fetched maxitem")
        return result.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not get maxitem: {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error when fetching maxitem: {e}")
        return json.dumps({"error": str(e)})