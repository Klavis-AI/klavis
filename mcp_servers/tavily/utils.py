"""Utility functions for Tavily MCP Server."""
from typing import Dict, List, Optional, Any


def prepare_search_params(
    query: str,
    search_depth: str = "basic",
    topic: str = "general",
    max_results: int = 5,
    include_images: bool = False,
    include_answer: bool = True,
    include_raw_content: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Prepare standardized search parameters."""
    params = {
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "max_results": max_results,
        "include_images": include_images,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content
    }
    
    # optional parameters
    if include_domains:
        params["include_domains"] = include_domains
    if exclude_domains:
        params["exclude_domains"] = exclude_domains
    
    # any additional kwargs
    params.update(kwargs)
    
    return params