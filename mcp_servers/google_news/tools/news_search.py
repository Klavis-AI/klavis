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

async def google_news_headlines(
    category: str = None,
    country: str = "us", 
    language: str = "en",
    sort_by: str = "relevance"
) -> dict:
    """
    Get Google News headlines by category.
    
    Args:
        category (str): News category (e.g., "business", "technology", "sports", "health", "entertainment", "science")
        country (str): Two-letter country code (default: "us")
        language (str): Two-letter language code (default: "en")
        sort_by (str): Sort method - "relevance" or "date" (default: "relevance")
        
    Returns:
        dict: JSON response with category headlines
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
    
    # Add category-specific query
    if category:
        category_queries = {
            "business": "business",
            "technology": "technology",
            "sports": "sports",
            "health": "health",
            "entertainment": "entertainment",
            "science": "science",
            "world": "world news",
            "politics": "politics"
        }
        params["q"] = category_queries.get(category.lower(), category)
    
    # Add sorting
    if sort_by == "date":
        params["so"] = "1"
    else:
        params["so"] = "0"
    
    logger.info(f"Sending Google News headlines request for category: {category}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info("Received Google News headlines response")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Google News headlines search failed: {e}")
        return {"error": f"Could not complete Google News headlines search: {str(e)}"}

async def google_news_by_source(
    source: str,
    country: str = "us",
    language: str = "en"
) -> dict:
    """
    Get Google News articles from a specific source.
    
    Args:
        source (str): News source name (e.g., "CNN", "BBC", "Reuters")
        country (str): Two-letter country code (default: "us")
        language (str): Two-letter language code (default: "en")
        
    Returns:
        dict: JSON response with news from specified source
    """
    return await google_news_search(
        query=f"site:{source.lower()}.com OR source:{source}",
        country=country,
        language=language
    )

async def google_news_date_range(
    query: str = None,
    start_date: str = None,
    end_date: str = None,
    country: str = "us",
    language: str = "en"
) -> dict:
    """
    Search Google News with date range filtering.
    
    Args:
        query (str): Search query for news articles
        start_date (str): Start date in format "YYYY-MM-DD" (e.g., "2023-01-01")
        end_date (str): End date in format "YYYY-MM-DD" (e.g., "2023-12-31")
        country (str): Two-letter country code (default: "us")
        language (str): Two-letter language code (default: "en")
        
    Returns:
        dict: JSON response with date-filtered news
    """
    # Build query with date operators
    search_query = query or ""
    
    if start_date and end_date:
        date_filter = f"after:{start_date} before:{end_date}"
    elif start_date:
        date_filter = f"after:{start_date}"
    elif end_date:
        date_filter = f"before:{end_date}"
    else:
        date_filter = ""
    
    if date_filter:
        search_query = f"{search_query} {date_filter}".strip()
    
    return await google_news_search(
        query=search_query,
        country=country,
        language=language
    )

async def google_news_topics_list() -> dict:
    """
    Get available Google News topics/categories.
    
    Returns:
        dict: List of available news topics and categories
    """
    return {
        "topics": [
            {"name": "World", "description": "International news and global events"},
            {"name": "Business", "description": "Business, finance, and economy news"},
            {"name": "Technology", "description": "Tech industry, gadgets, and innovation"},
            {"name": "Entertainment", "description": "Movies, TV, celebrities, and entertainment"},
            {"name": "Sports", "description": "Sports news, scores, and analysis"},
            {"name": "Science", "description": "Scientific discoveries and research"},
            {"name": "Health", "description": "Health, medical, and wellness news"},
            {"name": "Politics", "description": "Political news and government affairs"},
            {"name": "Opinion", "description": "Editorial content and opinion pieces"}
        ],
        "note": "Use these topic names in the 'category' parameter of google_news_headlines"
    }

async def google_news_sources_list() -> dict:
    """
    Get popular Google News sources.
    
    Returns:
        dict: List of popular news sources
    """
    return {
        "sources": [
            {"name": "CNN", "domain": "cnn.com", "type": "General News"},
            {"name": "BBC", "domain": "bbc.com", "type": "International News"},
            {"name": "Reuters", "domain": "reuters.com", "type": "Wire Service"},
            {"name": "Associated Press", "domain": "apnews.com", "type": "Wire Service"},
            {"name": "The New York Times", "domain": "nytimes.com", "type": "Newspaper"},
            {"name": "The Washington Post", "domain": "washingtonpost.com", "type": "Newspaper"},
            {"name": "The Guardian", "domain": "theguardian.com", "type": "Newspaper"},
            {"name": "Wall Street Journal", "domain": "wsj.com", "type": "Financial News"},
            {"name": "Bloomberg", "domain": "bloomberg.com", "type": "Financial News"},
            {"name": "TechCrunch", "domain": "techcrunch.com", "type": "Technology"},
            {"name": "ESPN", "domain": "espn.com", "type": "Sports"},
            {"name": "Fox News", "domain": "foxnews.com", "type": "General News"},
            {"name": "CNBC", "domain": "cnbc.com", "type": "Financial News"}
        ],
        "note": "Use these source names in the 'source' parameter of google_news_by_source"
    }