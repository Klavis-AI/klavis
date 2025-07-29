import json
import logging
from .hackerNews_get_ids import (
    hackerNews_showstories_ids,
    hackerNews_beststories_ids,
    hackerNews_topstories_ids,
    hackerNews_newstories_ids,
    hackerNews_jobstories_ids,
    hackerNews_askstories_ids,
    hackerNews_updates_ids,
)
from .hackerNews_items_n_users import hackerNews_item

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

base_url = 'https://hacker-news.firebaseio.com/v0'


async def hackerNews_topstories(count:int=5) -> str:
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


async def hackerNews_beststories(count:int=5) -> str:
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


async def hackerNews_newstories(count:int=5) -> str:
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


async def hackerNews_showstories(count:int=5) -> str:
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


async def hackerNews_askstories(count:int=5) -> str:
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


async def hackerNews_jobstories(count:int=5) -> str:
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


async def hackerNews_updates(count:int=5) -> str:
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
