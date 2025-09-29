import json
import httpx
import logging
from .helpers import (
    hackerNews_showstories_ids,
    hackerNews_beststories_ids,
    hackerNews_topstories_ids,
    hackerNews_newstories_ids,
    hackerNews_jobstories_ids,
    hackerNews_askstories_ids,
    hackerNews_updates_ids
)

# Setup logging
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

async def hackerNews_user(username: str) -> dict:
    """Fetch a Hacker News user by username.

    Args:
        username (str): Required. The user's unique username (e.g., `'pg'`).
    """
    url = f"{base_url}/user/{username}.json"
    logger.info(f"Requesting user {username} from {url}")
    try:
        # Use an async client to make a non-blocking request
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(f"Successfully fetched item {username}")
            return response.json()  # This returns a dict
    except httpx.RequestError as e:
        logger.error(f"Could not get username {username}: {e}")
        return {"error": f"An error occurred while requesting {e.request.url!r}."}
    except Exception as e:
        logger.error(f"Unexpected error when fetching user {username}: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_topstories(count:int=5) -> dict:
    """
    Fetch top stories details.
    
    Required:
        count: Number of top stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_topstories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_topstories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_beststories(count:int=5) -> dict:
    """
    Fetch best stories details.
    
    Required:
        count: Number of best stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_beststories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_beststories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_newstories(count:int=5) -> dict:
    """
    Fetch new stories details.
    
    Required:
        count: Number of new stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_newstories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_newstories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_showstories(count:int=5) -> dict:
    """
    Fetch show stories details.
    
    Required:
        count: Number of show stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_showstories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_showstories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_askstories(count:int=5) -> dict:
    """
    Fetch ask stories details.
    
    Required:
    count: Number of ask stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_askstories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_askstories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_jobstories(count:int=5) -> dict:
    """
    Fetch job stories details.
    
    Required:
    count: Number of job stories to fetch.

    Returns:
        str: JSON string of stories or error.
    """
    try:
        ids = await hackerNews_jobstories_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        for item_id in ids[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps(news)
    except Exception as e:
        logger.error(f"Error in hackerNews_jobstories: {e}")
        return json.dumps({"error": str(e)})


async def hackerNews_updates(count:int=5) -> dict:
    """
    Fetch updates: items and profiles.
    
    Required:
    count: Number of updates to fetch.

    Returns:
        str: JSON string with items and profiles or error.
    """
    try:
        ids = await hackerNews_updates_ids()
        if 'error' in ids:
            return json.dumps(ids)
        news = []
        profiles = ids.get('profiles', [])[:count]
        for item_id in ids.get('items', [])[:count]:
            item = await hackerNews_item(item_id)
            news.append(item)
        return json.dumps({
            "items": news,
            "profiles": profiles
        })
    except Exception as e:
        logger.error(f"Error in hackerNews_updates: {e}")
        return json.dumps({"error": str(e)})
