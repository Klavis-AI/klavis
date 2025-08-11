"""Pydantic models for Tavily MCP Server."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Individual search result from Tavily."""
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    content: str = Field(description="Extracted content summary")
    score: float = Field(description="Relevance score of the result")
    raw_content: Optional[str] = Field(description="Full raw content if available", default=None)


class TavilySearchResponse(BaseModel):
    """Structured response from Tavily search."""
    query: str = Field(description="The original search query")
    answer: Optional[str] = Field(description="Direct answer to the query", default=None)
    results: List[SearchResult] = Field(description="List of search results")
    images: List[str] = Field(description="List of image URLs found", default_factory=list)
    response_time: str = Field(description="Response time in seconds")
    follow_up_questions: List[str] = Field(description="Suggested follow-up questions", default_factory=list)


class ExtractedContent(BaseModel):
    """Structured response from Tavily extract."""
    url: str = Field(description="The URL that was extracted")
    raw_content: str = Field(description="Raw extracted content from the URL")
    response_time: str = Field(description="Response time in seconds")