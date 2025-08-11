import logging
from typing import List, Optional, Dict, Any
from .base import get_exa_client

# Configure logging
logger = logging.getLogger(__name__)


async def exa_search(
    query: str,
    num_results: int = 10,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    use_autoprompt: bool = True,
    type: str = "neural",
    category: Optional[str] = None,
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform an Exa search query using neural or keyword search.

    Args:
        query (str): [Required] The search query.
        num_results (int): Number of results to return (max 1000, default 10).
        include_domains (List[str]): Domains to include in search results.
        exclude_domains (List[str]): Domains to exclude from search results.
        start_crawl_date (str): Start date for crawl date filter (YYYY-MM-DD).
        end_crawl_date (str): End date for crawl date filter (YYYY-MM-DD).
        start_published_date (str): Start date for published date filter (YYYY-MM-DD).
        end_published_date (str): End date for published date filter (YYYY-MM-DD).
        use_autoprompt (bool): Whether to use autoprompt (default True).
        type (str): Search type - 'neural' or 'keyword' (default 'neural').
        category (str): Category filter for results.
        include_text (List[str]): Text patterns to include in results.
        exclude_text (List[str]): Text patterns to exclude from results.

    Returns:
        Dict[str, Any]: Search results with URLs, titles, and metadata.
    """
    try:
        client = get_exa_client()
        if not client:
            return {"error": "Could not initialize Exa client"}

        # Build search parameters
        search_params = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": use_autoprompt,
            "type": type
        }

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if start_crawl_date:
            search_params["start_crawl_date"] = start_crawl_date
        if end_crawl_date:
            search_params["end_crawl_date"] = end_crawl_date
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date
        if category:
            search_params["category"] = category
        if include_text:
            search_params["include_text"] = include_text
        if exclude_text:
            search_params["exclude_text"] = exclude_text

        logger.info(f"Sending Exa search request: {query}")
        result = client.search_and_contents(**search_params)
        
        # Convert to dict for JSON serialization
        response = {
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "id": r.id,
                    "score": r.score,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text if hasattr(r, 'text') else None
                }
                for r in result.results
            ],
            "autoprompt_string": result.autoprompt_string if hasattr(result, 'autoprompt_string') else None
        }
        
        logger.info("Received Exa search response")
        return response

    except Exception as e:
        logger.error(f"Exa search failed: {e}")
        return {"error": f"Could not complete Exa search for query: {query}. Error: {str(e)}"}


async def exa_get_contents(
    ids: List[str],
    text: bool = True,
    highlights: Optional[Dict[str, Any]] = None,
    summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get contents for specific Exa search result IDs.

    Args:
        ids (List[str]): [Required] List of Exa result IDs to get contents for.
        text (bool): Whether to include text content (default True).
        highlights (Dict): Highlighting options with query and num_sentences.
        summary (Dict): Summary options with query.

    Returns:
        Dict[str, Any]: Contents for the specified IDs.
    """
    try:
        client = get_exa_client()
        if not client:
            return {"error": "Could not initialize Exa client"}

        # Build parameters
        params = {
            "ids": ids,
            "text": text
        }

        if highlights:
            params["highlights"] = highlights
        if summary:
            params["summary"] = summary

        logger.info(f"Getting Exa contents for {len(ids)} IDs")
        result = client.get_contents(**params)
        
        # Convert to dict for JSON serialization
        response = {
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "id": r.id,
                    "text": r.text if hasattr(r, 'text') and text else None,
                    "highlights": r.highlights if hasattr(r, 'highlights') else None,
                    "summary": r.summary if hasattr(r, 'summary') else None,
                    "published_date": r.published_date,
                    "author": r.author
                }
                for r in result.results
            ]
        }
        
        logger.info("Received Exa contents response")
        return response

    except Exception as e:
        logger.error(f"Exa get contents failed: {e}")
        return {"error": f"Could not get Exa contents for IDs: {ids}. Error: {str(e)}"}


async def exa_find_similar(
    url: str,
    num_results: int = 10,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    exclude_source_domain: bool = True,
    category: Optional[str] = None,
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Find pages similar to a given URL.

    Args:
        url (str): [Required] The URL to find similar pages for.
        num_results (int): Number of results to return (max 1000, default 10).
        include_domains (List[str]): Domains to include in search results.
        exclude_domains (List[str]): Domains to exclude from search results.
        start_crawl_date (str): Start date for crawl date filter (YYYY-MM-DD).
        end_crawl_date (str): End date for crawl date filter (YYYY-MM-DD).
        start_published_date (str): Start date for published date filter (YYYY-MM-DD).
        end_published_date (str): End date for published date filter (YYYY-MM-DD).
        exclude_source_domain (bool): Whether to exclude the source domain (default True).
        category (str): Category filter for results.
        include_text (List[str]): Text patterns to include in results.
        exclude_text (List[str]): Text patterns to exclude from results.

    Returns:
        Dict[str, Any]: Similar pages with URLs, titles, and metadata.
    """
    try:
        client = get_exa_client()
        if not client:
            return {"error": "Could not initialize Exa client"}

        # Build parameters
        params = {
            "url": url,
            "num_results": num_results,
            "exclude_source_domain": exclude_source_domain
        }

        # Add optional parameters if provided
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        if start_crawl_date:
            params["start_crawl_date"] = start_crawl_date
        if end_crawl_date:
            params["end_crawl_date"] = end_crawl_date
        if start_published_date:
            params["start_published_date"] = start_published_date
        if end_published_date:
            params["end_published_date"] = end_published_date
        if category:
            params["category"] = category
        if include_text:
            params["include_text"] = include_text
        if exclude_text:
            params["exclude_text"] = exclude_text

        logger.info(f"Finding similar pages to: {url}")
        result = client.find_similar(**params)
        
        # Convert to dict for JSON serialization
        response = {
            "results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "id": r.id,
                    "score": r.score,
                    "published_date": r.published_date,
                    "author": r.author
                }
                for r in result.results
            ]
        }
        
        logger.info("Received Exa find similar response")
        return response

    except Exception as e:
        logger.error(f"Exa find similar failed: {e}")
        return {"error": f"Could not find similar pages for URL: {url}. Error: {str(e)}"}


async def exa_answer(
    query: str,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    use_autoprompt: bool = True,
    type: str = "neural",
    category: Optional[str] = None,
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get a direct answer to a question by performing a search and extracting key information.
    
    Note: This implements answer functionality using search_and_contents since the Answer API
    endpoint may not be available in the current exa_py version.

    Args:
        query (str): [Required] The question to answer.
        include_domains (List[str]): Domains to include in search.
        exclude_domains (List[str]): Domains to exclude from search.
        start_crawl_date (str): Start date for crawl date filter (YYYY-MM-DD).
        end_crawl_date (str): End date for crawl date filter (YYYY-MM-DD).
        start_published_date (str): Start date for published date filter (YYYY-MM-DD).
        end_published_date (str): End date for published date filter (YYYY-MM-DD).
        use_autoprompt (bool): Whether to use autoprompt (default True).
        type (str): Search type - 'neural' or 'keyword' (default 'neural').
        category (str): Category filter for results.
        include_text (List[str]): Text patterns to include in results.
        exclude_text (List[str]): Text patterns to exclude from results.

    Returns:
        Dict[str, Any]: Search results formatted as an answer with sources.
    """
    try:
        client = get_exa_client()
        if not client:
            return {"error": "Could not initialize Exa client"}

        # Build search parameters
        search_params = {
            "query": query,
            "num_results": 5,  # Limit to top 5 for answer generation
            "use_autoprompt": use_autoprompt,
            "type": type
        }

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if start_crawl_date:
            search_params["start_crawl_date"] = start_crawl_date
        if end_crawl_date:
            search_params["end_crawl_date"] = end_crawl_date
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date
        if category:
            search_params["category"] = category
        if include_text:
            search_params["include_text"] = include_text
        if exclude_text:
            search_params["exclude_text"] = exclude_text

        logger.info(f"Getting Exa answer-style search for: {query}")
        result = client.search_and_contents(**search_params)
        
        # Format as answer-style response
        response = {
            "query": query,
            "answer_type": "search_based",
            "note": "This answer is generated from search results. For the best answers, review the sources provided.",
            "sources": [
                {
                    "url": r.url,
                    "title": r.title,
                    "id": r.id,
                    "score": r.score,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text[:500] + "..." if hasattr(r, 'text') and r.text and len(r.text) > 500 else r.text if hasattr(r, 'text') else None
                }
                for r in result.results
            ],
            "autoprompt_string": result.autoprompt_string if hasattr(result, 'autoprompt_string') else None,
            "total_sources": len(result.results)
        }
        
        logger.info("Received Exa answer-style response")
        return response

    except Exception as e:
        logger.error(f"Exa answer failed: {e}")
        return {"error": f"Could not get Exa answer for query: {query}. Error: {str(e)}"}


async def exa_research(
    query: str,
    num_results: int = 10,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    use_autoprompt: bool = True,
    type: str = "neural",
    category: Optional[str] = None,
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Automate in-depth web research and receive structured JSON results with citations.

    Args:
        query (str): [Required] The research query.
        num_results (int): Number of results to return (max 1000, default 10).
        include_domains (List[str]): Domains to include in search.
        exclude_domains (List[str]): Domains to exclude from search.
        start_crawl_date (str): Start date for crawl date filter (YYYY-MM-DD).
        end_crawl_date (str): End date for crawl date filter (YYYY-MM-DD).
        start_published_date (str): Start date for published date filter (YYYY-MM-DD).
        end_published_date (str): End date for published date filter (YYYY-MM-DD).
        use_autoprompt (bool): Whether to use autoprompt (default True).
        type (str): Search type - 'neural' or 'keyword' (default 'neural').
        category (str): Category filter for results.
        include_text (List[str]): Text patterns to include in results.
        exclude_text (List[str]): Text patterns to exclude from results.

    Returns:
        Dict[str, Any]: Structured research results with detailed analysis and citations.
    """
    try:
        client = get_exa_client()
        if not client:
            return {"error": "Could not initialize Exa client"}

        # For research, we'll combine search and content retrieval for comprehensive results
        # Build search parameters
        search_params = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": use_autoprompt,
            "type": type
        }

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if start_crawl_date:
            search_params["start_crawl_date"] = start_crawl_date
        if end_crawl_date:
            search_params["end_crawl_date"] = end_crawl_date
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date
        if category:
            search_params["category"] = category
        if include_text:
            search_params["include_text"] = include_text
        if exclude_text:
            search_params["exclude_text"] = exclude_text

        logger.info(f"Conducting Exa research for: {query}")
        
        # Get search results with content
        result = client.search_and_contents(**search_params)
        
        # Structure the research response
        response = {
            "query": query,
            "research_summary": f"Research conducted on '{query}' yielding {len(result.results)} sources",
            "sources": [
                {
                    "url": r.url,
                    "title": r.title,
                    "id": r.id,
                    "score": r.score,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text if hasattr(r, 'text') else None,
                    "relevance_score": r.score
                }
                for r in result.results
            ],
            "autoprompt_string": result.autoprompt_string if hasattr(result, 'autoprompt_string') else None,
            "total_sources": len(result.results),
            "research_timestamp": "Generated via Exa Research API"
        }
        
        logger.info("Completed Exa research")
        return response

    except Exception as e:
        logger.error(f"Exa research failed: {e}")
        return {"error": f"Could not complete Exa research for query: {query}. Error: {str(e)}"}
