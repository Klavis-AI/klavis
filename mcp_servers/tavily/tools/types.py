# tools/types.py
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

class Result(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = Field(default=None, alias="raw_content")
    score: Optional[float] = None
    favicon: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")

class SearchResponse(BaseModel):
    query: Optional[str] = None
    answer: Optional[str] = None
    results: List[Result] = Field(default_factory=list)
    response_time: Optional[Union[str, float]] = None
    auto_parameters: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # If you want to always return string outward:
    @field_validator("response_time", mode="before")
    def _rt_to_str(cls, v):
        return None if v is None else str(v)

class ExtractItem(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None     # we will map various upstream fields into this
    images: Optional[List[str]] = None
    model_config = ConfigDict(extra="allow")

class ExtractResponse(BaseModel):
    results: List[ExtractItem] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")

class CrawlPage(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    depth: Optional[int] = None
    parent: Optional[str] = None
    model_config = ConfigDict(extra="allow")

class CrawlResponse(BaseModel):
    pages: List[CrawlPage] = Field(default_factory=list)
    model_config = ConfigDict(extra="allow")
