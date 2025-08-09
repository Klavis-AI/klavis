import httpx
from .base import get_brave_client
import logging

# Configure logging
logger = logging.getLogger(__name__)


async def brave_web_search(
    query: str,
    count: int = 5,
    offset: int = None,
    country: str = None,
    search_lang: str = None,
    safesearch: str = None
) -> dict:
    """
    Perform a Brave search query.

    Args:
        query (str): [Required] The user's search query.
        count (int): Number of results (max 20, default 5).
        offset (int): For pagination.
        country (str): 2-letter country code, e.g., 'US'.
        search_lang (str): Language code, e.g., 'en'.
        safesearch (str): 'off', 'moderate', or 'strict'.
    Returns:
        dict: JSON response.
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": get_brave_client()
    }

    params = {"q": query,
              "count": count}

    param_list = [
        ("country", country),
        ("search_lang", search_lang),
        ("offset", offset),
        ("safesearch", safesearch),
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave search request: {query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()  # Good practice to check for HTTP errors
            logger.info("Received Brave search response")
            return response.json()

    except Exception as e:
        logger.error(f"Brave search failed: {e}")
        return {"error": f"Could not complete Brave search for query: {query}"}


async def brave_image_search(
    query: str,
    count: int = 5,
    offset: int = None,
    search_lang: str = None,
    country: str = None,
    safesearch: str = None
) -> dict:
    """
    Perform a Brave image search.

    Args:
        query (str): [Required] Search query.
        count (int): Number of image results (max 200, default 5).
        offset (int): For pagination.
        search_lang (str): Language code, e.g., 'en'.
        country (str): 2-letter country code, e.g., 'US'.
        safesearch (str): 'off' or 'strict' (default).
    Returns:
        dict: JSON response.
    """
    token = get_brave_client()
    if not token:
        logger.error("Could not get Brave subscription token")
        return {"error": "Missing Brave subscription token"}

    url = "https://api.search.brave.com/res/v1/images/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": token
    }

    # Always include query
    params = {"q": query,
              'count': count}

    # Optional query params
    param_list = [
        ("search_lang", search_lang),
        ("country", country),
        ("safesearch", safesearch),
        ("offset", offset)
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave image search request: {query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            logger.info("Received Brave image search response")
            return response.json()
    except Exception as e:
        logger.error(f"Brave image search failed: {e}")
        return {"error": f"Could not complete Brave image search for query: {query}"}


async def brave_news_search(
    query: str,
    count: int = 5,
    offset: int = None,
    country: str = None,
    search_lang: str = None,
    safesearch: str = None,
    freshness: str = None
) -> dict:
    """
    Perform a Brave news search.
    Args:
        query (str): [Required] Search query.
        count (int): Number of news results (max 50, default 5).
        offset (int): For pagination.
        country (str): 2-letter country code, e.g., 'US'.
        search_lang (str): Language code, e.g., 'en'.
        safesearch (str): 'off', 'moderate', or 'strict'.
        freshness (str): Filter by recency: 'pd' (24h), 'pw' (7d), 'pm' (31d), 'py' (year).
    Returns:
        dict: JSON response.
    """
    token = get_brave_client()
    if not token:
        logger.error("Could not get Brave subscription token")
        return {"error": "Missing Brave subscription token"}

    url = "https://api.search.brave.com/res/v1/news/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": token
    }

    params = {"q": query, "count": count}

    param_list = [
        ("search_lang", search_lang),
        ("country", country),
        ("safesearch", safesearch),
        ("offset", offset),
        ("freshness", freshness),
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave news search request: {query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            logger.info("Received Brave news search response")
            return response.json()
    except Exception as e:
        logger.error(f"Brave news search failed: {e}")
        return {"error": f"Could not complete Brave news search for query: {query}"}


async def brave_video_search(
    query: str,
    count: int = 5,
    offset: int = None,
    country: str = None,
    search_lang: str = None,
    safesearch: str = None,
    freshness: str = None
) -> dict:
    """
    Perform a Brave video search.

    Args:
        query (str): [Required] Search query.
        count (int): Number of video results (max 50, default 5).
        offset (int): For pagination.
        country (str): 2-letter country code, e.g., 'US'.
        search_lang (str): Language code, e.g., 'en'.
        safesearch (str): 'off', 'moderate', or 'strict'.
        freshness (str): Filter by recency: 'pd' (24h), 'pw' (7d), 'pm' (31d), 'py' (year).
    Returns:
        dict: JSON response.
    """

    token = get_brave_client()
    if not token:
        logger.error("Could not get Brave subscription token")
        return {"error": "Missing Brave subscription token"}

    url = "https://api.search.brave.com/res/v1/videos/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": token
    }

    params = {"q": query,
              "count": count}

    param_list = [
        ("search_lang", search_lang),
        ("country", country),
        ("offset", offset),
        ("freshness", freshness),
        ("safesearch", safesearch),
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave video search request: {query}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            logger.info("Received Brave video search response")
            return response.json()
    except Exception as e:
        logger.error(f"Brave video search failed: {e}")
        return {"error": f"Could not complete Brave video search for query: {query}"}
