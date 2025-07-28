import requests
from .base import get_brave_client
import logging

# Configure logging
logger = logging.getLogger(__name__)


async def brave_search(
        query: str,
        count: int = 5,
        country: str = None,
        search_lang: str = None,
        ui_lang: str = None,
        offset: int = None,
        safesearch: str = None,
        spellcheck: str = None,
        freshness: str = None,
        text_decorations: str = None,
        result_filter: str = None,
        units: str = None,
        goggles: str = None,
        extra_snippets: str = None,
        summary: str = None,
        enable_rich_callback: str = None,
        x_loc_lat: float = None,
        x_loc_long: float = None,
        x_loc_timezone: str = None,
        x_loc_city: str = None,
        x_loc_state: str = None,
        x_loc_state_name: str = None,
        x_loc_country: str = None,
        x_loc_postal_code: str = None
) -> dict:
    """
    Perform a Brave search query with optional parameters.

    Args:
        query (str): [Required] The user's search query term (q parameter). Cannot be empty.
            Maximum of 400 characters and 50 words. Supports search operators for optimization.
        count (int): Number of search results to return (max 20, default 5). Only applies to web results.
            Use with offset for pagination.
        country (str): 2-character country code for result localization (default: 'US').
            See supported Country Codes.
        search_lang (str): 2+ character language code for search results (default: 'en').
            See Language Codes.
        ui_lang (str): User interface language in format <language_code>-<country_code>
            (default: 'en-US'). See UI Language Codes.
        offset (int): Zero-based offset for pagination (max 9). Use with count for pagination.
        safesearch (str): Adult content filter ('off', 'moderate' (default), or 'strict').
        spellcheck (bool): Whether to spellcheck the query (default: True).
        freshness (str): Filter by discovery time:
            - 'pd': Last 24 hours
            - 'pw': Last 7 days
            - 'pm': Last 31 days
            - 'py': Last 365 days
            - 'YYYY-MM-DDtoYYYY-MM-DD': Custom date range
        text_decorations (bool): Whether to include highlighting markers in snippets (default: True).
        result_filter (str): Comma-delimited result types to include (e.g., 'news,videos,web').
            Available options: discussions, faq, infobox, news, query, summarizer, videos,
            web, locations.
        units (str): Measurement system ('metric' or 'imperial'). Derived from country if not provided.
        goggles (str): Goggles ID or definition for custom result re-ranking. Can be repeated for multiple goggles.
        extra_snippets (bool): Whether to include up to 5 additional alternative excerpts.
        summary (bool): Whether to generate summaries in web search results.
        enable_rich_callback (str): [Undocumented parameter]

        Location Headers (for personalization):
        x_loc_lat (float): Latitude coordinate
        x_loc_long (float): Longitude coordinate
        x_loc_timezone (str): Timezone
        x_loc_city (str): City name
        x_loc_state (str): State code
        x_loc_state_name (str): State name
        x_loc_country (str): Country code
        x_loc_postal_code (str): Postal code

    Returns:
        dict: JSON response from Brave Search API containing search results or error message.

    Notes:
        - The Web Search API has a maximum of 20 results per request (count parameter)
        - Pagination is achieved by combining count and offset parameters
        - Result filtering applies to all result types except web results (which use count)
        - Location headers personalize results but are all optional
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "x-subscription-token": get_brave_client()
    }

    # Add optional location headers
    header_list = [
        ("x-loc-lat", x_loc_lat),
        ("x-loc-long", x_loc_long),
        ("x-loc-timezone", x_loc_timezone),
        ("x-loc-city", x_loc_city),
        ("x-loc-state", x_loc_state),
        ("x-loc-state-name", x_loc_state_name),
        ("x-loc-country", x_loc_country),
        ("x-loc-postal-code", x_loc_postal_code)
    ]
    for k, v in header_list:
        if v is not None:
            headers[k] = str(v)

    params = {"q": query,
              "count": count}

    param_list = [
        ("country", country),
        ("search_lang", search_lang),
        ("ui_lang", ui_lang),
        ("offset", offset),
        ("safesearch", safesearch),
        ("spellcheck", spellcheck),
        ("freshness", freshness),
        ("text_decorations", text_decorations),
        ("result_filter", result_filter),
        ("units", units),
        ("goggles", goggles),
        ("extra_snippets", extra_snippets),
        ("summary", summary),
        ("enable_rich_callback", enable_rich_callback)
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave search request: {query}")
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info("Received Brave search response")
        return response.json()
    except Exception as e:
        logger.error(f"Brave search failed: {e}")
        return {"error": f"Could not complete Brave search for query: {query}"}


async def brave_image_search(
        query: str,
        count: int = 5,
        search_lang: str = None,
        country: str = None,
        safesearch: str = None,
        spellcheck: str = None,
) -> dict:
    """
    Perform a Brave image search with optional parameters.

    Args:
        query (str): [Required] The user's search query term (q parameter). Cannot be empty.
            Maximum of 400 characters and 50 words.
        count (int): Number of image results to return (default: 5, max: 200).
        search_lang (str): 2+ character language code for search results (default: 'en').
            See Language Codes.
        country (str): 2-character country code for result localization (default: 'US').
            See supported Country Codes.
        safesearch (str): Adult content filter:
            - 'off': No filtering
            - 'strict': Drops all adult content (default)
        spellcheck (bool): Whether to spellcheck the query (default: True).
            If enabled, modified query appears in response's 'altered' key.


    Returns:
        dict: JSON response from Brave Image Search API containing:
            - Image results (up to requested count)
            - Potentially altered query if spellcheck was enabled
            - Error message if request failed

    Notes:
        - Default safesearch setting is more strict ('strict') than web search API
        - Maximum 200 results per request (count parameter)
        - Location headers are all optional but help personalize results
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
        ("spellcheck", spellcheck)
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave image search request: {query}")
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info("Received Brave image search response")
        return response.json()
    except Exception as e:
        logger.error(f"Brave image search failed: {e}")
        return {"error": f"Could not complete Brave image search for query: {query}"}


async def brave_news_search(
        query: str,
        count: int = 5,
        search_lang: str = None,
        ui_lang: str = None,
        country: str = None,
        safesearch: str = None,
        offset: int = None,
        spellcheck: str = None,
        freshness: str = None,
        extra_snippets: str = None,
        goggles: str = None
) -> dict:
    """
    Perform a Brave news search with optional parameters.

    Args:
        query (str): [Required] The user's search query term (q parameter). Cannot be empty.
            Maximum of 400 characters and 50 words.
        count (int): Number of news results to return (default: 5, max: 50).
            Use with offset for pagination.
        search_lang (str): 2+ character language code for search results (default: 'en').
            See Language Codes.
        ui_lang (str): User interface language in format <language_code>-<country_code>
            (default: 'en-US'). See UI Language Codes.
        country (str): 2-character country code for result localization (default: 'US').
            See supported Country Codes.
        safesearch (str): Adult content filter:
            - 'off': No filtering
            - 'moderate': Filter explicit content (default)
            - 'strict': Filter explicit and suggestive content
        offset (int): Zero-based offset for pagination (max 9). Use with count for pagination.
            Example: count=20 & offset=1 gets second page of 20 results.
        spellcheck (bool): Whether to spellcheck the query (default: True).
            Modified query appears in response's 'altered' key if enabled.
        freshness (str): Filter by discovery time:
            - 'pd': Last 24 hours
            - 'pw': Last 7 days
            - 'pm': Last 31 days
            - 'py': Last 365 days
            - 'YYYY-MM-DDtoYYYY-MM-DD': Custom date range
        extra_snippets (bool): Whether to include up to 5 additional alternative excerpts.
            Requires specific API plans.
        goggles (str): Goggles ID or definition for custom result re-ranking.
            Can be repeated for multiple goggles.

    Returns:
        dict: JSON response from Brave News Search API containing:
            - News results (up to requested count)
            - Pagination information if offset used
            - Potentially altered query if spellcheck was enabled
            - Error message if request failed

    Notes:
        - Default safesearch setting is 'moderate' (between web and image search strictness)
        - Maximum 50 results per request (count parameter)
        - Pagination requires combining count and offset parameters
        - Results may overlap across paginated requests
        - Location headers are all optional but help personalize results
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
        ("ui_lang", ui_lang),
        ("country", country),
        ("safesearch", safesearch),
        ("offset", offset),
        ("spellcheck", spellcheck),
        ("freshness", freshness),
        ("extra_snippets", extra_snippets),
        ("goggles", goggles)
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave news search request: {query}")
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info("Received Brave news search response")
        return response.json()
    except Exception as e:
        logger.error(f"Brave news search failed: {e}")
        return {"error": f"Could not complete Brave news search for query: {query}"}


async def brave_video_search(
        query: str,
        count: int = 5,
        safesearch: str = "off",
        search_lang: str = None,
        ui_lang: str = None,
        country: str = None,
        offset: int = None,
        spellcheck: str = None,
        freshness: str = None,
) -> dict:
    """
    Perform a Brave video search with optional parameters.

    Args:
        query (str): [Required] The user's search query term (q parameter). Cannot be empty.
            Maximum of 400 characters and 50 words.
        count (int): Number of video results to return (default: 20, max: 50).
            Use with offset for pagination.
        safesearch (str): Adult content filter:
            - 'off': No filtering (default)
            - 'moderate': Filter explicit content
            - 'strict': Filter explicit and suggestive content
        search_lang (str): 2+ character language code for search results (default: 'en').
            See Language Codes.
        ui_lang (str): User interface language in format <language_code>-<country_code>
            (default: 'en-US'). See UI Language Codes.
        country (str): 2-character country code for result localization (default: 'US').
            See supported Country Codes.
        offset (int): Zero-based offset for pagination (max 9). Use with count for pagination.
            Example: count=20 & offset=1 gets second page of 20 results.
        spellcheck (bool): Whether to spellcheck the query (default: True).
            Modified query appears in response's 'altered' key if enabled.
        freshness (str): Filter by discovery time:
            - 'pd': Last 24 hours
            - 'pw': Last 7 days
            - 'pm': Last 31 days
            - 'py': Last 365 days
            - 'YYYY-MM-DDtoYYYY-MM-DD': Custom date range


    Returns:
        dict: JSON response from Brave Video Search API containing:
            - Video results (up to requested count)
            - Pagination information if offset used
            - Potentially altered query if spellcheck was enabled
            - Error message if request failed

    Notes:
        - Default safesearch setting is 'off' (less strict than other search types)
        - Maximum 50 results per request (count parameter)
        - Pagination requires combining count and offset parameters
        - Results may overlap across paginated requests
        - Location headers are all optional but help personalize results
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

    params = {"q": query, "count": count, "safesearch": safesearch}

    param_list = [
        ("search_lang", search_lang),
        ("ui_lang", ui_lang),
        ("country", country),
        ("offset", offset),
        ("spellcheck", spellcheck),
        ("freshness", freshness)
    ]
    for k, v in param_list:
        if v is not None:
            params[k] = v

    logger.info(f"Sending Brave video search request: {query}")
    try:
        response = requests.get(url, headers=headers, params=params)
        logger.info("Received Brave video search response")
        return response.json()
    except Exception as e:
        logger.error(f"Brave video search failed: {e}")
        return {"error": f"Could not complete Brave video search for query: {query}"}
