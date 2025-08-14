"""
Exa API client for MCP Server
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from ..models.schemas import (
    ExaSearchParams, 
    ExaContentsParams, 
    ExaSimilarParams,
    ToolExecutionResult
)
from ..utils.config import get_config
from ..utils.logging import get_logger

logger = get_logger("client")


class ExaAPIError(Exception):
    """Custom exception for Exa API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Exa API Error {status_code}: {message}")


class ExaClient:
    """Client for interacting with the Exa API"""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.exa_base_url
        self.api_key = self.config.exa_api_key
        
        self.client = httpx.AsyncClient(
            timeout=self.config.default_timeout,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
        )
        logger.info("Exa client initialized")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the Exa API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            JSON response data
            
        Raises:
            ExaAPIError: If the API request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        retries = 0
        max_retries = self.config.max_retries
        
        while retries <= max_retries:
            try:
                logger.debug(f"Making {method} request to {endpoint}")
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                
                result = response.json()
                logger.debug(f"Request successful: {endpoint}")
                return result
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_detail = e.response.json()
                    if "error" in error_detail:
                        error_msg += f" - {error_detail['error']}"
                except:
                    error_msg += f" - {e.response.text}"
                
                logger.error(f"API request failed: {error_msg}")
                
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise ExaAPIError(e.response.status_code, error_msg)
                
                # Retry on server errors (5xx) and rate limits
                if retries < max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    logger.warning(f"Retrying in {wait_time} seconds... (attempt {retries + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    retries += 1
                else:
                    raise ExaAPIError(e.response.status_code, error_msg)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if retries < max_retries:
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                else:
                    raise ExaAPIError(0, f"Request failed: {str(e)}")
    
    async def search(self, params: ExaSearchParams) -> ToolExecutionResult:
        """
        Perform an AI-powered search
        
        Args:
            params: Search parameters
            
        Returns:
            Tool execution result with search data
        """
        try:
            # Build request payload
            payload = {
                "query": params.query,
                "numResults": params.num_results,
                "useAutoprompt": params.use_autoprompt,
                "type": params.type
            }
            
            # Add optional parameters if provided
            if params.include_domains:
                payload["includeDomains"] = params.include_domains
            if params.exclude_domains:
                payload["excludeDomains"] = params.exclude_domains
            if params.start_crawl_date:
                payload["startCrawlDate"] = params.start_crawl_date
            if params.end_crawl_date:
                payload["endCrawlDate"] = params.end_crawl_date
            if params.start_published_date:
                payload["startPublishedDate"] = params.start_published_date
            if params.end_published_date:
                payload["endPublishedDate"] = params.end_published_date
            if params.category:
                payload["category"] = params.category
            
            logger.info(f"Performing Exa search: {params.query}")
            result = await self._make_request("POST", "/search", json=payload)
            
            num_results = len(result.get('results', []))
            logger.info(f"Search completed: {num_results} results found")
            
            return ToolExecutionResult(
                success=True,
                data=result
            )
            
        except ExaAPIError as e:
            logger.error(f"Search failed: {e}")
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected search error: {str(e)}")
            return ToolExecutionResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    async def get_contents(self, params: ExaContentsParams) -> ToolExecutionResult:
        """
        Get full contents for specific Exa result IDs
        
        Args:
            params: Content retrieval parameters
            
        Returns:
            Tool execution result with content data
        """
        try:
            payload = {
                "ids": params.ids,
                "text": params.text,
                "highlights": params.highlights,
                "summary": params.summary
            }
            
            logger.info(f"Getting contents for {len(params.ids)} items")
            result = await self._make_request("POST", "/contents", json=payload)
            
            num_contents = len(result.get('results', []))
            logger.info(f"Contents retrieved: {num_contents} items")
            
            return ToolExecutionResult(
                success=True,
                data=result
            )
            
        except ExaAPIError as e:
            logger.error(f"Get contents failed: {e}")
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected get contents error: {str(e)}")
            return ToolExecutionResult(
                success=False,
                error=f"Get contents failed: {str(e)}"
            )
    
    async def find_similar(self, params: ExaSimilarParams) -> ToolExecutionResult:
        """
        Find content similar to a given URL
        
        Args:
            params: Similarity search parameters
            
        Returns:
            Tool execution result with similar content data
        """
        try:
            payload = {
                "url": params.url,
                "numResults": params.num_results
            }
            
            # Add optional parameters if provided
            if params.include_domains:
                payload["includeDomains"] = params.include_domains
            if params.exclude_domains:
                payload["excludeDomains"] = params.exclude_domains
            if params.start_crawl_date:
                payload["startCrawlDate"] = params.start_crawl_date
            if params.end_crawl_date:
                payload["endCrawlDate"] = params.end_crawl_date
            if params.start_published_date:
                payload["startPublishedDate"] = params.start_published_date
            if params.end_published_date:
                payload["endPublishedDate"] = params.end_published_date
            if params.category:
                payload["category"] = params.category
            
            logger.info(f"Finding content similar to: {params.url}")
            result = await self._make_request("POST", "/findSimilar", json=payload)
            
            num_results = len(result.get('results', []))
            logger.info(f"Similar content found: {num_results} results")
            
            return ToolExecutionResult(
                success=True,
                data=result
            )
            
        except ExaAPIError as e:
            logger.error(f"Find similar failed: {e}")
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected find similar error: {str(e)}")
            return ToolExecutionResult(
                success=False,
                error=f"Find similar failed: {str(e)}"
            )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("Exa client closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()