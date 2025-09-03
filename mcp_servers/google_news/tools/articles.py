# klavis_google_news/models/articles.py
from enum import Enum
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


# ──────────────────────────────────────────────────────────────── #
#  Enumerations mirroring SerpAPI / Google News options           #
# ──────────────────────────────────────────────────────────────── #
class Topic(str, Enum):
    """Top-level Google News navigation topics (topic_token values).

    Docs: https://serpapi.com/google-news-api  (see *Advanced Google News Parameters*)
    """

    world = "world"
    nation = "nation"  # “U.S.” inside the US locale
    business = "business"
    technology = "technology"
    entertainment = "entertainment"
    sports = "sports"
    science = "science"
    health = "health"


class SortBy(str, Enum):
    """Allowed sort orders for the `q=` search endpoint."""

    date = "date"  # Newest first
    relevance = "relevance"  # Google’s default


class Source(BaseModel):
    authors: Optional[List[str]] = Field(None, description="Bylines")
    icon: Optional[HttpUrl] = Field(None, description="Favicon URL")
    name: Optional[str] = Field(None, description="Outlet name")


class Article(BaseModel):
    title: Optional[str] = Field(..., description="Exact headline")
    link: Optional[HttpUrl] = Field(..., description="Canonical URL")
    source: Optional[Source] = Field(None, description="Publisher details")
    published_at: Optional[datetime] = Field(
        None,
        description="When published (UTC)",
        example="2025-08-11T15:19:00Z",
    )
    thumbnail_url: Optional[HttpUrl] = Field(
        None, description="Lead image thumbnail URL"
    )


class ArticleCluster(BaseModel):
    """A bundle of related articles returned under `stories`."""

    serpapi_link: Optional[HttpUrl] = Field(
        None,
        description="Link to fetch more on this cluster",
    )
    stories: List[Article] = Field(
        ...,
        description="The grouped articles in this cluster",
    )


class ArticleSearchIn(BaseModel):
    query: str = Field(
        ...,
        description="Free-text query string; supports Google search operators "
        "(site:, OR, quotes, etc.).",
        examples=['"quantum computing" AND IBM', "site:nytimes.com AI policy"],
    )
    language: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="ISO-639-1 code for UI language (`hl=`).",
    )
    country: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="ISO-3166-1 alpha-2 code for regional edition (`gl=`).",
    )
    from_date: Optional[date] = Field(
        None,
        description="Earliest publication date (inclusive). Converted to SerpAPI `after=`.",
    )
    to_date: Optional[date] = Field(
        None,
        description="Latest publication date (inclusive). Converted to SerpAPI `before=`.",
    )
    sort_by: Optional[SortBy] = Field(
        None,
        description="Force ordering by `date` or `relevance` (default is relevance).",
    )
    page: Optional[int] = Field(
        None,
        ge=1,
        description="Pagination index (one-based).",
    )


class ArticleSearchOut(BaseModel):
    articles: List[Article] = Field(..., description="Individual articles")
    clusters: List[ArticleCluster] = Field(
        default_factory=list,
        description="Grouped story bundles",
    )
    next_page: Optional[str] = Field(None, description="Cursor for next page")
