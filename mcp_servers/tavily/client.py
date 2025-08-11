"""Tavily client wrapper with error handling."""
import logging
from typing import Dict, List, Optional, Any

try:
    from tavily import TavilyClient
except ImportError:
    raise ImportError(
        "tavily-python package is required. Install with: pip install tavily-python"
    )

from .config import Config
from .models import TavilySearchResponse, SearchResult, ExtractedContent

logger = logging.getLogger(__name__)


class TavilyClientWrapper:
    """Wrapper for Tavily client with standardized error handling."""
    
    def __init__(self):
        """Initialize Tavily client."""
        self.client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    
    def _convert_response(self, response: Dict[str, Any], query: str) -> TavilySearchResponse:
        """Convert raw Tavily response to structured format."""
        results = []
        for result in response.get("results", []):
            results.append(SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content", ""),
                score=result.get("score", 0.0),
                raw_content=result.get("raw_content")
            ))
        
        return TavilySearchResponse(
            query=response.get("query", query),
            answer=response.get("answer"),
            results=results,
            images=response.get("images", []),
            response_time=str(response.get("response_time", "0")),
            follow_up_questions=response.get("follow_up_questions") or []
        )
    
    def search(self, **params) -> TavilySearchResponse:
        """Execute search with error handling."""
        query = params.get("query", "")
        try:
            # Cap max_results
            if "max_results" in params:
                params["max_results"] = min(params["max_results"], Config.MAX_RESULTS_LIMIT)
            
            response = self.client.search(**params)
            return self._convert_response(response, query)
            
        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return TavilySearchResponse(
                query=query,
                answer=f"Search failed: {str(e)}",
                results=[],
                images=[],
                response_time="0",
                follow_up_questions=[]
            )
    
    def extract(self, url: str) -> ExtractedContent:
        """Extract content from URL with error handling."""
        try:
            response = self.client.extract(urls=[url])
            
            if response and "results" in response and len(response["results"]) > 0:
                result = response["results"][0]
                return ExtractedContent(
                    url=result.get("url", url),
                    raw_content=result.get("raw_content", ""),
                    response_time=str(response.get("response_time", "0"))
                )
            else:
                return ExtractedContent(
                    url=url,
                    raw_content="No content extracted",
                    response_time="0"
                )
                
        except Exception as e:
            logger.error(f"Tavily extract failed for {url}: {str(e)}")
            return ExtractedContent(
                url=url,
                raw_content=f"Extraction failed: {str(e)}",
                response_time="0"
            )


# Global client instance
tavily_client = TavilyClientWrapper()