import requests
from .base import get_serpapi_key
import logging

logger = logging.getLogger(__name__)

async def google_news_search(
    query: str = None,
    country: str = "us",
    language: str = "en",
    topic_token: str = None,
    publication_token: str = None,
    story_token: str = None
) -> dict:
    """
    Perform a Google News search using SerpApi.
    
    Args:
        query (str): Search query for news articles
        country (str): Two-letter country code (default: "us")
        language (str): Two-letter language code (default: "en") 
        topic_token (str): Token for specific news topic
        publication_token (str): Token for specific publisher
        story_token (str): Token for full coverage of specific story
        
    Returns:
        dict: JSON response from SerpApi
    """
    api_key = get_serpapi_key()
    if not api_key:
        logger.error("SerpApi key not found")
        return {"error": "Missing SerpApi API key"}
    
    url = "https://serpapi.com/search"
    
    params = {
        "engine": "google_news",
        "api_key": api_key,
        "gl": country,
        "hl": language
    }
    
    # Add search parameters
    if query:
        params["q"] = query
    if topic_token:
        params["topic_token"] = topic_token
    if publication_token:
        params["publication_token"] = publication_token
    if story_token:
        params["story_token"] = story_token
    
    logger.info(f"Sending Google News search request: {query or 'trending'}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info("Received Google News search response")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Google News search failed: {e}")
        return {"error": f"Could not complete Google News search: {str(e)}"}

async def google_news_trending(
    country: str = "us",
    language: str = "en"
) -> dict:
    """
    Get trending Google News articles.
    
    Args:
        country (str): Two-letter country code (default: "us")
        language (str): Two-letter language code (default: "en")
        
    Returns:
        dict: JSON response with trending news
    """
    return await google_news_search(
        query=None,
        country=country,
        language=language
    )