"""
Pydantic models and schemas for Exa MCP Server
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class ExaSearchParams(BaseModel):
    """Parameters for Exa search requests"""
    query: str = Field(..., description="The search query")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include in search")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Domains to exclude from search")
    start_crawl_date: Optional[str] = Field(default=None, description="Start date for crawl filter (YYYY-MM-DD)")
    end_crawl_date: Optional[str] = Field(default=None, description="End date for crawl filter (YYYY-MM-DD)")
    start_published_date: Optional[str] = Field(default=None, description="Start date for published filter (YYYY-MM-DD)")
    end_published_date: Optional[str] = Field(default=None, description="End date for published filter (YYYY-MM-DD)")
    use_autoprompt: bool = Field(default=True, description="Whether to use Exa's autoprompt feature")
    type: str = Field(default="neural", description="Search type: 'neural' or 'keyword'")
    category: Optional[str] = Field(default=None, description="Content category filter")

    @validator('type')
    def validate_search_type(cls, v):
        if v not in ['neural', 'keyword']:
            raise ValueError("Search type must be 'neural' or 'keyword'")
        return v

    @validator('start_crawl_date', 'end_crawl_date', 'start_published_date', 'end_published_date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class ExaContentsParams(BaseModel):
    """Parameters for getting contents of URLs"""
    ids: List[str] = Field(..., description="List of Exa result IDs to get contents for")
    text: bool = Field(default=True, description="Whether to include text content")
    highlights: bool = Field(default=False, description="Whether to include highlights")
    summary: bool = Field(default=False, description="Whether to include AI-generated summary")

    @validator('ids')
    def validate_ids_not_empty(cls, v):
        if not v:
            raise ValueError("At least one ID must be provided")
        return v


class ExaSimilarParams(BaseModel):
    """Parameters for finding similar content"""
    url: str = Field(..., description="URL to find similar content for")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include in search")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Domains to exclude from search")
    start_crawl_date: Optional[str] = Field(default=None, description="Start date for crawl filter (YYYY-MM-DD)")
    end_crawl_date: Optional[str] = Field(default=None, description="End date for crawl filter (YYYY-MM-DD)")
    start_published_date: Optional[str] = Field(default=None, description="Start date for published filter (YYYY-MM-DD)")
    end_published_date: Optional[str] = Field(default=None, description="End date for published filter (YYYY-MM-DD)")
    category: Optional[str] = Field(default=None, description="Content category filter")

    @validator('url')
    def validate_url_format(cls, v):
        from urllib.parse import urlparse
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("URL must include protocol (http:// or https://)")
        return v


class ExaRecentContentParams(BaseModel):
    """Parameters for searching recent content"""
    query: str = Field(..., description="Search query for recent content")
    days_back: int = Field(default=7, ge=1, le=365, description="Number of days back to search")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    include_domains: Optional[List[str]] = Field(default=None, description="Domains to include")


class ExaAcademicParams(BaseModel):
    """Parameters for searching academic content"""
    query: str = Field(..., description="Academic search query")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    include_domains: Optional[List[str]] = Field(default=None, description="Additional academic domains")


class ExaSearchResult(BaseModel):
    """Individual search result from Exa"""
    id: str
    url: str
    title: str
    score: float
    text: Optional[str] = None
    highlights: Optional[List[str]] = None
    published_date: Optional[str] = None


class ExaApiResponse(BaseModel):
    """Response from Exa API"""
    results: List[ExaSearchResult]
    autoprompt_string: Optional[str] = None


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    formatted_response: Optional[str] = None