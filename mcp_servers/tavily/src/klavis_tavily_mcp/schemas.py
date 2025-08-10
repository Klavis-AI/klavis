from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    title: Optional[str] = None
    url: HttpUrl
    score: Optional[float] = None
    content: Optional[str] = None


class TavilySearchResponse(BaseModel):
    query: str
    answer: Optional[str] = None
    results: List[SearchResult] = Field(default_factory=list)


class ExtractResult(BaseModel):
    url: HttpUrl
    raw_content: Optional[str] = None
    images: Optional[list[str]] = None


class TavilyExtractResponse(BaseModel):
    results: List[ExtractResult] = Field(default_factory=list)
    failed_results: Optional[list[str]] = None
    response_time: Optional[float] = None