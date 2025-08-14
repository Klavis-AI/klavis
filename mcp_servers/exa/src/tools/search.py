"""
Search-related tools for Exa MCP Server
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from mcp.types import TextContent

from .base import BaseTool
from ..models.schemas import ExaSearchParams, ExaRecentContentParams, ExaAcademicParams


class SearchWebTool(BaseTool):
    """Tool for performing AI-powered web searches"""
    
    @property
    def name(self) -> str:
        return "search_web"
    
    @property
    def description(self) -> str:
        return (
            "Perform an AI-powered web search using Exa. This tool uses neural search "
            "to find highly relevant content based on meaning and context, not just keywords. "
            "Perfect for finding authoritative sources, research papers, or specific information "
            "on any topic. Returns search results with titles, URLs, and snippets."
        )
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and descriptive for best results."
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to include (e.g., ['github.com', 'stackoverflow.com'])"
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to exclude"
                },
                "start_crawl_date": {
                    "type": "string",
                    "description": "Include only pages crawled after this date (YYYY-MM-DD format)"
                },
                "end_crawl_date": {
                    "type": "string",
                    "description": "Include only pages crawled before this date (YYYY-MM-DD format)"
                },
                "type": {
                    "type": "string",
                    "enum": ["neural", "keyword"],
                    "description": "Search type: 'neural' for AI-powered semantic search, 'keyword' for traditional keyword matching",
                    "default": "neural"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by content category (e.g., 'research paper', 'news', 'company')"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute web search"""
        try:
            params = ExaSearchParams(**arguments)
            result = await self.client.search(params)
            
            if not result.success:
                return self._create_error_response(result.error)
            
            # Format the response
            results = result.data.get("results", [])
            formatted_response = self.formatter.format_search_results(
                results, params.query, params.type
            )
            
            return self._create_success_response(formatted_response)
            
        except Exception as e:
            self.logger.error(f"Search execution error: {str(e)}")
            return self._create_error_response(str(e))


class SearchRecentContentTool(BaseTool):
    """Tool for searching recent content"""
    
    @property
    def name(self) -> str:
        return "search_recent_content"
    
    @property
    def description(self) -> str:
        return (
            "Search for recently published or crawled content using Exa. This is a specialized "
            "search tool optimized for finding fresh, up-to-date information. Perfect for "
            "news, recent developments, or current events on any topic."
        )
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for recent content"
                },
                "days_back": {
                    "type": "integer",
                    "description": "Number of days back to search (1-365)",
                    "minimum": 1,
                    "maximum": 365,
                    "default": 7
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of domains to include (e.g., news sites)"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute recent content search"""
        try:
            params = ExaRecentContentParams(**arguments)
            
            # Calculate date range for recent content
            end_date = datetime.now()
            start_date = end_date - timedelta(days=params.days_back)
            
            # Convert to ExaSearchParams
            search_args = {
                "query": params.query,
                "num_results": params.num_results,
                "start_published_date": start_date.strftime("%Y-%m-%d"),
                "end_published_date": end_date.strftime("%Y-%m-%d"),
                "type": "neural"
            }
            
            if params.include_domains:
                search_args["include_domains"] = params.include_domains
            
            search_params = ExaSearchParams(**search_args)
            result = await self.client.search(search_params)
            
            if not result.success:
                return self._create_error_response(result.error)
            
            # Format the response
            results = result.data.get("results", [])
            date_range = f"Last {params.days_back} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
            
            formatted_response = self.formatter.format_recent_results(
                results, params.query, date_range
            )
            
            return self._create_success_response(formatted_response)
            
        except Exception as e:
            self.logger.error(f"Recent search execution error: {str(e)}")
            return self._create_error_response(str(e))


class SearchAcademicContentTool(BaseTool):
    """Tool for searching academic content"""
    
    @property
    def name(self) -> str:
        return "search_academic_content"
    
    @property
    def description(self) -> str:
        return (
            "Search specifically for academic and research content using Exa. This tool is "
            "optimized to find scholarly articles, research papers, academic publications, "
            "and authoritative educational content. Great for research, fact-checking, "
            "or finding credible sources."
        )
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The academic search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Academic domains to focus on (e.g., ['arxiv.org', 'pubmed.ncbi.nlm.nih.gov'])"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute academic content search"""
        try:
            params = ExaAcademicParams(**arguments)
            
            # Academic-focused domains
            academic_domains = [
                "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
                "jstor.org", "ieee.org", "acm.org", "springer.com", 
                "nature.com", "science.org", "plos.org", "biorxiv.org",
                "ssrn.com", "researchgate.net"
            ]
            
            # Merge with user-provided domains if any
            include_domains = params.include_domains or []
            all_domains = academic_domains + include_domains
            
            search_args = {
                "query": params.query,
                "num_results": params.num_results,
                "include_domains": all_domains[:10],  # Limit to avoid API limits
                "type": "neural",
                "category": "research paper"
            }
            
            search_params = ExaSearchParams(**search_args)
            result = await self.client.search(search_params)
            
            if not result.success:
                return self._create_error_response(result.error)
            
            # Format the response
            results = result.data.get("results", [])
            formatted_response = self.formatter.format_academic_results(
                results, params.query, all_domains
            )
            
            return self._create_success_response(formatted_response)
            
        except Exception as e:
            self.logger.error(f"Academic search execution error: {str(e)}")
            return self._create_error_response(str(e))